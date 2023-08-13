import asyncio, math, threading, time, datetime, requests
from . import logger
from config import *

lock = threading.Lock()
condition = threading.Condition(lock)
online_miners = []
offline_miners = []
broker_payload = {}
processed = False
total_hashrate = 0
total_power = 0
updated_at = 0

async def broker_messages(topic, payload):
    global processed
    logger.logger.debug(f" got a new message reading, updating our payload")
    for readout in payload["values"]:
        if readout["dataTypeEnum"] == "POWER_ACTIVE":   
            readout["value"] = round(readout["value"]/1000, 2)
            broker_payload.clear()
            broker_payload.update(readout)
            processed = False
            return

def find_miner_index(dict, search_miner):
    for index, value in enumerate(dict):
        if search_miner in str(value):
            return index
    return None

async def get_temperature(api_key, city):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "units": "metric",  # Request temperature in Celsius
        "appid": api_key
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        temperature = data["main"]["temp"]
        return temperature
    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)
        return None


async def get_miner_data(miners):
    with lock:
        global online_miners, offline_miners, total_hashrate, total_power, broker_payload, updated_at
        online_miners.clear()
        offline_miners.clear()
        total_hashrate = 0
        total_power = 0
        try:
            # all_miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
            for miner in miners:
                try:
                    miner_data = await asyncio.gather(miner.get_data())
                    miner_data = miner_data[0]
                    miner_hashrate = int(miner_data.hashrate)
                    if miner_hashrate > 0:
                        # if miner_hashrate < 70:
                        #     if(miner_data.left_board_hashrate,miner_data.center_board_hashrate, miner_data.right_board_hashrate is not None) and \
                        #         (miner_data.left_board_hashrate == 0 or miner_data.center_board_hashrate == 0 or miner_data.right_board_hashrate == 0):
                        #         logger.logger.info(f" lower than expected hashrate on {miner_data.hostname} one of the HBs is not working")
                        miner_wattage = int(miner_data.wattage) if int(miner_data.wattage) > 0 else 2850
                        miner_efficiency = int(miner_data.efficiency) if int(miner_data.efficiency) > 0 else (2850/(miner_hashrate))
                    else:
                        miner_wattage = 0
                        miner_efficiency = 0
                    total_hashrate = total_hashrate + miner_hashrate
                    total_power = total_power + miner_wattage
                    logger.logger.info(f"{miner_data.hostname}: {miner_hashrate}TH @ {miner_data.temperature_avg} ˚C {round(miner_wattage/1000, 2)} KW at {round(miner_efficiency, 2)} W/TH efficiency")
                    if int(miner_data.hashrate) > 0:
                        online_miners.append(miner_data.ip)
                    else:
                        offline_miners.append(miner_data.ip)
                except Exception as e:
                    logger.logger.error(f" failed with error {e}")
            if total_hashrate > 0:
                logger.logger.info(f" we have {len(online_miners)} active miners with a total hashrate of {round(total_hashrate, 2)}TH with a total power of {round(total_power/1000, 2)}KW and an average efficiency of {round(total_power/total_hashrate, 2)}W/TH")
            else:
                logger.logger.info(f" we have {len(online_miners)} active miners with a total hashrate of {round(total_hashrate, 2)}TH with a total power of {round(total_power/1000, 2)}KW")
        except Exception as e:
            condition.notify()
            logger.logger.error(f" failed with error {e}")
        finally:
            updated_at = int(time.time())
            condition.notify()
            
async def start_miners(miners, num_miners_to_start):
    global offline_miners, total_hashrate, total_power, broker_payload, updated_at, processed
    logger.logger.info(f" we need to start {num_miners_to_start} miner(s)")
    num_miners_started = 0
    try:
        for device, ip in miners_ips.items():
            try:
                if ip in offline_miners:
                    miner = find_miner_index(miners, ip)
                    if miner is not None and num_miners_to_start > 0 and num_miners_started != num_miners_to_start:
                        resume_miner = await miners[miner].resume_mining()
                        if resume_miner:
                            online_miners.append(miners[miner].ip)
                            index = find_miner_index(offline_miners, miners[miner].ip)
                            offline_miners.pop(index)
                            logger.logger.info(f" successfully resumed {device}")
                            num_miners_started += 1
                        else:
                            resume_miner = await miners[miner].api.send_command("resume")
                            if resume_miner:
                                online_miners.append(miners[miner].ip)
                                index = find_miner_index(offline_miners, miners[miner].ip)
                                offline_miners.pop(index)
                                logger.logger.info(f" successfully resumed {device}")
                                num_miners_started += 1
                            else:
                                logger.logger.info(f" couldn't resume {device}")
                        if num_miners_started == num_miners_to_start:
                            processed = True
                            logger.logger.info(f" successfully resumed {num_miners_started} miners") 
                            return          
            except Exception as e:
                logger.logger.error(f" failed with error {e}")
    except Exception as e:
        logger.logger.error(f" failed with error {e}") 
    
async def stop_miners(miners, num_miners_to_pause):
    global online_miners, total_hashrate, total_power, broker_payload, updated_at, processed
    logger.logger.info(f" we need to pause {num_miners_to_pause} miner(s)")
    num_miners_stopped = 0
    try:
        for device, ip in miners_ips.items():
            try:
                if ip in online_miners:
                    miner = find_miner_index(miners, ip)
                    if miner is not None and num_miners_stopped != num_miners_to_pause:
                        stop_miner = await miners[miner].stop_mining()
                        if stop_miner:
                            logger.logger.info(f" successfully paused {device}")
                            offline_miners.append(miners[miner].ip)
                            index = find_miner_index(online_miners, miners[miner].ip)
                            online_miners.pop(index)
                            num_miners_stopped += 1
                        else:
                            stop_miner = await miners[miner].api.send_command("pause")
                            if stop_miner:
                                logger.logger.info(f" successfully paused {device}")
                                offline_miners.append(miners[miner].ip)
                                index = find_miner_index(online_miners, miners[miner].ip)
                                online_miners.pop(index)
                                num_miners_stopped += 1
                            else:
                                logger.logger.info(f" couldn't stop {device}")
                        if num_miners_stopped == num_miners_to_pause:
                            processed = True
                            logger.logger.info(f" successfully paused {num_miners_stopped} miners") 
                            return 
            except Exception as e:
                logger.logger.error(f" failed with error {e}")    
    except Exception as e:
        logger.logger.error(f" failed with error {e}")  

async def load_shifting(miners):
    with lock:
        global online_miners, offline_miners, total_hashrate, total_power, broker_payload, updated_at, processed
        current_time = datetime.datetime.now().time()
        logger.logger.debug(f" payload: {broker_payload}")
        if not processed or run_non_stop:
            current_temperature = await get_temperature(API_key, location)
            logger.logger.debug(f" current temp in {location} is {current_temperature}˚C")
            if (int(time.time()) - updated_at) > 3600:
                logger.logger.info(f" our data is older than 1 hour, trying to get new data")
                condition.notify()
                get_miner_data(miners)
            elif not broker_payload and not ignore_readout:
                condition.notify()
                logger.logger.debug(f" no messages received yet")
            elif ignore_readout:
                logger.logger.debug(f" ignoring conroller readouts")
                if run_non_stop and current_temperature < temp_halt_ambient:
                    logger.logger.info(f" current temp in {location} is {current_temperature}˚C which is less than {temp_halt_ambient}˚C so all miners should be running")
                    if len(offline_miners) > 0:
                        num_miners_to_start = len(offline_miners)
                        logger.logger.info(f" we need to start {num_miners_to_start} miner(s)")
                        await start_miners(miners, num_miners_to_start)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are online")
                elif run_non_stop and current_temperature >= temp_halt_ambient:
                    logger.logger.info(f" current temp in {location} is {current_temperature}˚C which is higher than {temp_halt_ambient}˚C")
                    if len(online_miners) > 0:
                        num_miners_to_pause = len(online_miners)
                        logger.logger.info(f" we need to pause {num_miners_to_pause} miner(s)")
                        await stop_miners(miners, num_miners_to_pause)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are offline")
                elif not run_non_stop and current_time >= datetime.time(start_hour, 0) or current_time < datetime.time(stop_hour, 0) and len(offline_miners) > 0:
                    logger.logger.info(f" ignoring conroller readouts miners should only run between {start_hour} and {stop_hour}")
                    if len(offline_miners) > 0:
                        num_miners_to_start = len(offline_miners)
                        logger.logger.info(f" we need to start {num_miners_to_start} miner(s)")
                        await start_miners(miners, num_miners_to_start)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are online")
                elif not run_non_stop and current_time >= datetime.time(stop_hour, 0) or current_time < datetime.time(start_hour, 0) and len(online_miners) > 0:
                    logger.logger.info(f" ignoring conroller readouts miners should only run between {start_hour} and {stop_hour}")
                    if len(online_miners) > 0:
                        num_miners_to_pause = len(online_miners)
                        logger.logger.info(f" we need to pause {num_miners_to_pause} miner(s)")
                        await stop_miners(miners, num_miners_to_pause)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are offline")    
            else:                
                power = broker_payload["value"]
                if power - buffer > 0 and len(online_miners) > 0:
                    num_miners_to_pause = math.ceil((power - buffer) / miner_avg_kw)
                    num_miners_to_pause = num_miners_to_pause if num_miners_to_pause < len(online_miners) else len(online_miners)
                    logger.logger.debug(f" these are our offline miners {offline_miners}")
                    if num_miners_to_pause > 0:
                        logger.logger.info(f" we need to pause {num_miners_to_pause} miner(s)")
                        await stop_miners(miners, num_miners_to_pause)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are offline")   
                elif power - buffer < 0 and abs(power) > buffer and len(offline_miners) > 0:
                    num_miners_to_start = math.floor(abs(power + buffer) / miner_avg_kw)
                    num_miners_to_start = num_miners_to_start if num_miners_to_start < len(offline_miners) else len(offline_miners)
                    logger.logger.debug(f" these are our online miners {online_miners}")
                    logger.logger.debug(f" these are our offline miners {offline_miners}")
                    if num_miners_to_start > 0:
                        logger.logger.info(f" we need to start {num_miners_to_start} miner(s)")
                        num_miners_started = 0
                        await start_miners(miners, num_miners_to_start)
                    else:
                        processed = True
                        logger.logger.info(f" all miners are online")
                else:
                    condition.notify()
                    logger.logger.debug(" nothing to do right now")
                    pass
                condition.notify()
            condition.notify()
        else:
            condition.notify()
            logger.logger.debug(" measurement already processed")