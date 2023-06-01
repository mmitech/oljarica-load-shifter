import asyncio, math, threading, time
from . import logger
from config import *

lock = threading.Lock()
online_miners = []
offline_miners = []
total_hashrate = 0
total_power = 0
updated_at = 0

def find_miner_index(dict, search_miner):
    for index, value in enumerate(dict):
        if search_miner in str(value):
            return index
    return None

async def get_miner_data(miners):
    lock.acquire()
    global online_miners
    global offline_miners
    global total_hashrate
    global total_power
    global updated_at
    online_miners = []
    offline_miners = []
    total_hashrate = 0
    total_power = 0
    try:
        all_miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
        for miner_data in all_miner_data:
            total_hashrate = int(total_hashrate) + int(miner_data.hashrate)
            total_power = int(total_power) + int(miner_data.wattage)
            try:
                logger.logger.debug(f"{miner_data.hostname}: {miner_data.hashrate}TH @ {miner_data.temperature_avg} ˚C {round(miner_data.wattage/1000, 2)} KW at {round(miner_data.efficiency, 2)} W/TH efficiency")
                if int(miner_data.hashrate) > 0:
                    online_miners.append(miner_data.ip)
                else:
                    offline_miners.append(miner_data.ip)
            except Exception as e:
                logger.logger.info(f" failed with error {e}")
        logger.logger.info(f" we have {len(online_miners)} active miners with a total hashrate of {round(total_hashrate, 2)}TH with a total power of {round(total_power/1000, 2)}KW")
    except Exception as e:
        lock.release()
        logger.logger.info(f" failed with error {e}")
    finally:
        updated_at = int(time.time())
        lock.release()

async def load_shifting(miners, payload):
    global online_miners
    global offline_miners
    global total_hashrate
    global total_power
    global updated_at
    if (int(time.time()) - updated_at) > 3600:
        logger.logger.info(f" our data is older than 1 hour, trying to get new data")
        get_miner_data(miners)
    else:
        power = payload["value"]
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
                                        num_miners_stopped += 1
                                    else:
                                        logger.logger.info(f" couldn't stop {device}")
                                else:
                                    if num_miners_to_pause > 0 and num_miners_stopped == num_miners_to_pause:
                                        logger.logger.info(f" successfully paused {num_miners_to_pause} miners")
                                    elif num_miners_to_pause == 0:
                                        logger.logger.info(" Nothing to do right now")
                                    return         
                        except Exception as e:
                            logger.logger.info(f" failed with error {e}")
            except Exception as e:
                logger.logger.info(f" failed with error {e}")
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
                                        logger.logger.info(" Nothing to do right now")
                                    return         
                        except Exception as e:
                            logger.logger.info(f" failed with error {e}")
            except Exception as e:
                logger.logger.info(f" failed with error {e}")
        else:
            logger.logger.info(" Nothing to do right now")
            pass