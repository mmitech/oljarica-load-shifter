import asyncio, math, threading, time, json
from . import logger
from config import *

lock = threading.Lock()
condition = threading.Condition(lock)
online_miners = []
offline_miners = []
broker_payload = {}
total_hashrate = 0
total_power = 0
updated_at = 0

async def broker_messages(topic, payload):
    logger.logger.info(f" got a new message reading, updating our payload")
    broker_payload.clear()
    broker_payload.update(payload)

def find_miner_index(dict, search_miner):
    for index, value in enumerate(dict):
        if search_miner in str(value):
            return index
    return None

async def get_miner_data(miners):
    with lock:
        global online_miners
        global offline_miners
        global total_hashrate
        global total_power
        global updated_at
        online_miners.clear()
        offline_miners.clear()
        total_hashrate = 0
        total_power = 0
        try:
            all_miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
            for miner_data in all_miner_data:
                miner_hashrate = int(miner_data.hashrate)
                if miner_hashrate > 0:
                    if miner_hashrate < 70:
                        if miner_data.left_board_hashrate == 0 or miner_data.center_board_hashrate == 0 or miner_data.right_board_hashrate == 0:
                            logger.logger.info(f" lower than expected hashrate on {miner_data.hostname} one of the HBs is not working")
                    miner_wattage = int(miner_data.wattage) if int(miner_data.wattage) > 0 else 2850
                    miner_efficiency = int(miner_data.efficiency) if int(miner_data.efficiency) > 0 else (2850/(miner_hashrate))
                else:
                    miner_wattage = 0
                    miner_efficiency = 0
                total_hashrate = total_hashrate + miner_hashrate
                total_power = total_power + miner_wattage
                try:
                    logger.logger.debug(f"{miner_data.hostname}: {miner_hashrate}TH @ {miner_data.temperature_avg} ˚C {round(miner_wattage/1000, 2)} KW at {round(miner_efficiency, 2)} W/TH efficiency")
                    if int(miner_data.hashrate) > 0:
                        online_miners.append(miner_data.ip)
                    else:
                        offline_miners.append(miner_data.ip)
                except Exception as e:
                    logger.logger.error(f" failed with error {e}")
            logger.logger.info(f" we have {len(online_miners)} active miners with a total hashrate of {round(total_hashrate, 2)}TH with a total power of {round(total_power/1000, 2)}KW and an average efficiency of {round(total_power/total_hashrate, 2)}W/TH")
        except Exception as e:
            condition.notify()
            logger.logger.error(f" failed with error {e}")
        finally:
            updated_at = int(time.time())
            condition.notify()

async def load_shifting(miners):
    with lock:
        global online_miners
        global offline_miners
        global total_hashrate
        global total_power
        global broker_payload
        global updated_at
        logger.logger.debug(f" payload: {broker_payload}")
        if (int(time.time()) - updated_at) > 3600:
            logger.logger.info(f" our data is older than 1 hour, trying to get new data")
            condition.notify()
            get_miner_data(miners)
        elif not broker_payload:
            condition.notify()
            logger.logger.info(f" no messages received yet")
        else:
            power = broker_payload["value"]
            if power - buffer > 0 and len(online_miners) > 0:
                num_miners_to_pause = math.ceil((power - buffer) / miner_avg_kw)
                logger.logger.debug(f" these are our offline miners {offline_miners}")
                if num_miners_to_pause > 0:
                    logger.logger.info(f" we need to pause {num_miners_to_pause} miner(s)")
                num_miners_stopped = 0
                try:
                    for shelf, devices in miners_ips.items():
                        for device, ip in devices.items():
                            try:
                                if ip in online_miners:
                                    miner = find_miner_index(miners, ip)
                                    if miner is not None and num_miners_to_pause > 0 and num_miners_stopped != num_miners_to_pause:
                                        stop_miner = await miners[miner].stop_mining()
                                        if stop_miner:
                                            logger.logger.info(f" successfully paused {device}")
                                            offline_miners.append(miners[miner].ip)
                                            num_miners_stopped += 1
                                        else:
                                            logger.logger.info(f" couldn't stop {device}")
                                    else:
                                        if num_miners_to_pause > 0 and num_miners_stopped == num_miners_to_pause:
                                            logger.logger.info(f" successfully paused {num_miners_to_pause} miners")
                                        elif num_miners_to_pause == 0:
                                            logger.logger.info(" nothing to do right now")
                                        return         
                            except Exception as e:
                                logger.logger.error(f" failed with error {e}")
                except Exception as e:
                    logger.logger.error(f" failed with error {e}")
            if power - buffer < 0 and abs(power) > buffer and len(offline_miners) > 0:
                num_miners_to_start = math.floor(abs(power + buffer) / miner_avg_kw)
                logger.logger.debug(f" these are our online miners {online_miners}")
                logger.logger.debug(f" these are our offline miners {offline_miners}")
                if num_miners_to_start > 0:
                    logger.logger.info(f" we need to start {num_miners_to_start} miner(s)")
                num_miners_started = 0
                try:
                    for shelf, devices in miners_ips.items():
                        for device, ip in devices.items():
                            try:
                                if ip in offline_miners:
                                    miner = find_miner_index(miners, ip)
                                    if miner is not None and num_miners_to_start > 0 and num_miners_started != num_miners_to_start:
                                        power_limit = await miners[miner].set_power_limit(2500)
                                        if power_limit:
                                            logger.logger.info(f" power limit was successfully set on {device}")
                                        resume_miner = await miners[miner].resume_mining()
                                        if resume_miner:
                                            
                                            logger.logger.info(f" successfully resumed {device}")
                                            num_miners_started += 1
                                        else:
                                            logger.logger.info(f" couldn't resume {device}")
                                    else:
                                        if num_miners_to_start > 0 and num_miners_started == num_miners_to_start:
                                            logger.logger.info(f" successfully resumed {num_miners_to_start} miners")
                                        elif num_miners_to_start == 0:
                                            logger.logger.info(" nothing to do right now")
                                        return         
                            except Exception as e:
                                logger.logger.error(f" failed with error {e}")
                except Exception as e:
                    logger.logger.error(f" failed with error {e}")
            else:
                condition.notify()
                logger.logger.debug(" nothing to do right now")
                pass
            condition.notify()
        condition.notify()