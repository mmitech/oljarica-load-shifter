import asyncio, math, threading, time, datetime
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

async def get_miner_data(miners):
    with lock:
        global online_miners, offline_miners, total_hashrate, total_power, broker_payload, updated_at
        online_miners.clear()
        offline_miners.clear()
        total_hashrate = 0
        total_power = 0
        try:
            all_miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
            for miner_data in all_miner_data:
                try:
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
                except Exception as e:
                    logger.logger.error(f" failed with error {e}")
                try:
                    logger.logger.debug(f"{miner_data.hostname}: {miner_hashrate}TH @ {miner_data.temperature_avg} ˚C {round(miner_wattage/1000, 2)} KW at {round(miner_efficiency, 2)} W/TH efficiency")
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

async def load_shifting(miners):
    with lock:
        global online_miners, offline_miners, total_hashrate, total_power, broker_payload, updated_at, processed
        current_time = datetime.datetime.now().time()
        logger.logger.debug(f" payload: {broker_payload}")
        if not processed:
            if (int(time.time()) - updated_at) > 3600:
                logger.logger.info(f" our data is older than 1 hour, trying to get new data")
                condition.notify()
                get_miner_data(miners)
            elif not broker_payload:
                condition.notify()
                logger.logger.debug(f" no messages received yet")
            elif ignore_readout:
                logger.logger.debug(f" ignoring conroller readouts")
                if run_non_stop and len(offline_miners) > 0:
                    logger.logger.debug(f" all miners should run non stop")
                    num_miners_to_start = len(offline_miners)
                    if num_miners_to_start > 0:
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
                                                broker_payload["value"] = broker_payload["value"] + miner_avg_kw
                                                online_miners.append(miners[miner].ip)
                                                index = find_miner_index(offline_miners, miners[miner].ip)
                                                offline_miners.pop(index)
                                                logger.logger.info(f" successfully resumed {device}")
                                                num_miners_started += 1
                                            else:
                                                resume_miner = await miners[miner].api.send_command("resume")
                                                if resume_miner:
                                                    broker_payload["value"] = broker_payload["value"] + miner_avg_kw
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
                    else:
                        processed = True
                        logger.logger.info(f" all miners are online")
                elif current_time >= datetime.time(start_hour, 0) or current_time < datetime.time(stop_hour, 0) and len(offline_miners) > 0:
                    num_miners_to_start = len(offline_miners)
                    logger.logger.debug(f" ignoring conroller readouts miners should only run between {start_hour} and {stop_hour}")
                    if num_miners_to_start > 0:
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
                                                broker_payload["value"] = broker_payload["value"] + miner_avg_kw
                                                online_miners.append(miners[miner].ip)
                                                index = find_miner_index(offline_miners, miners[miner].ip)
                                                offline_miners.pop(index)
                                                logger.logger.info(f" successfully resumed {device}")
                                                num_miners_started += 1
                                            else:
                                                resume_miner = await miners[miner].api.send_command("resume")
                                                if resume_miner:
                                                    broker_payload["value"] = broker_payload["value"] + miner_avg_kw
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
                    else:
                        processed = True
                        logger.logger.info(f" all miners are online")
            elif current_time >= datetime.time(stop_hour, 0) or current_time < datetime.time(start_hour, 0) and len(online_miners) > 0:
                num_miners_to_pause = len(online_miners)
                logger.logger.debug(f" ignoring conroller readouts miners should only run between {start_hour} and {stop_hour}")
                if num_miners_to_pause > 0:
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
                                            broker_payload["value"] = broker_payload["value"] - miner_avg_kw
                                            offline_miners.append(miners[miner].ip)
                                            index = find_miner_index(online_miners, miners[miner].ip)
                                            online_miners.pop(index)
                                            num_miners_stopped += 1
                                        else:
                                            stop_miner = await miners[miner].api.send_command("pause")
                                            if stop_miner:
                                                logger.logger.info(f" successfully paused {device}")
                                                broker_payload["value"] = broker_payload["value"] - miner_avg_kw
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
                                                broker_payload["value"] = broker_payload["value"] - miner_avg_kw
                                                offline_miners.append(miners[miner].ip)
                                                index = find_miner_index(online_miners, miners[miner].ip)
                                                online_miners.pop(index)
                                                num_miners_stopped += 1
                                            else:
                                                stop_miner = await miners[miner].api.send_command("pause")
                                                if stop_miner:
                                                    logger.logger.info(f" successfully paused {device}")
                                                    broker_payload["value"] = broker_payload["value"] - miner_avg_kw
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
                        try:
                            for device, ip in miners_ips.items():
                                try:
                                    if ip in offline_miners:
                                        miner = find_miner_index(miners, ip)
                                        if miner is not None and num_miners_to_start > 0 and num_miners_started != num_miners_to_start:
                                            resume_miner = await miners[miner].resume_mining()
                                            if resume_miner:
                                                broker_payload["value"] = broker_payload["value"] + miner_avg_kw
                                                online_miners.append(miners[miner].ip)
                                                index = find_miner_index(offline_miners, miners[miner].ip)
                                                offline_miners.pop(index)
                                                logger.logger.info(f" successfully resumed {device}")
                                                num_miners_started += 1
                                            else:
                                                resume_miner = await miners[miner].api.send_command("resume")
                                                if resume_miner:
                                                    broker_payload["value"] = broker_payload["value"] + miner_avg_kw
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