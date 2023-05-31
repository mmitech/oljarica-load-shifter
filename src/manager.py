import asyncio, math
from . import logger
from config import *


def find_miner_index(dict, search_miner):
    for index, value in enumerate(dict):
        if search_miner in str(value):
            return index
    return None
        
async def load_shifting(miners, payload):
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
                # logger.logger.info(f"{miner_data}")
                # logger.logger.info(f"{miner_data.hostname}: {miner_data.hashrate}TH @ {miner_data.temperature_avg} ˚C")
                if int(miner_data.hashrate) > 0:
                    online_miners.append(miner_data.ip)
                else:
                    offline_miners.append(miner_data.ip)
            except Exception as e:
                logger.logger.info(f"failed with error {e}")
        # await asyncio.sleep(10)
        power = payload["value"]
        if power - buffer > 0 and len(online_miners) > 0:
            num_miners_to_pause = math.ceil((power - buffer) / miner_avg_kw)
            logger.logger.info(f"we have a total hashrate of {round(total_hashrate, 2)}TH and we using a total power of {round(total_power/1000, 2)}KW")
            logger.logger.info(f"these are our online miners {online_miners}")
            logger.logger.info(f"these are our offline miners {offline_miners}")
            logger.logger.info(f"we need to pause this number of miners {num_miners_to_pause}")
            num_miners_stopped = 0
            try:
                for shelf, devices in miners_ips.items():
                    for device, ip in devices.items():
                        try:
                            if ip in online_miners:
                                miner = find_miner_index(miners, ip)
                                if miner is not None and num_miners_stopped != num_miners_to_pause:
                                    stop_miner = await miners[miner].stop_mining()
                                    if stop_miner:
                                        logger.logger.info(f"we successfully paused {device}")
                                        num_miners_stopped += 1
                                    else:
                                        logger.logger.info(f"couldn't stop {device}")
                                else:
                                    if num_miners_stopped == num_miners_to_pause:
                                        logger.logger.info(f"we successfully paused {num_miners_to_pause} miners")
                                    return         
                        except Exception as e:
                            logger.logger.info(f"failed with error {e}")
            except Exception as e:
                logger.logger.info(f"failed with error {e}")
        if power - buffer < 0 and abs(power) > buffer and len(offline_miners) > 0:
            num_miners_to_start = math.floor(abs(power + buffer) / miner_avg_kw)
            logger.logger.info(f"we have a total hashrate of {round(total_hashrate, 2)}TH and we using a total power of {round(total_power/1000, 2)}KW")
            logger.logger.info(f"these are our online miners {online_miners}")
            logger.logger.info(f"these are our offline miners {offline_miners}")
            logger.logger.info(f"we need to start this number of miners {num_miners_to_start}")
            num_miners_started = 0
            try:
                for shelf, devices in miners_ips.items():
                    for device, ip in devices.items():
                        try:
                            if ip in offline_miners:
                                miner = find_miner_index(miners, ip)
                                if miner is not None and num_miners_started != num_miners_to_start:
                                    resume_miner = await miners[miner].resume_mining()
                                    if resume_miner:
                                        logger.logger.info(f"we successfully resumed {device}")
                                        num_miners_started += 1
                                    else:
                                        logger.logger.info(f"couldn't resume {device}")
                                else:
                                    if num_miners_started == num_miners_to_start:
                                        logger.logger.info(f"we successfully resumed {num_miners_to_start} miners")
                                    return         
                        except Exception as e:
                            logger.logger.info(f"failed with error {e}")
            except Exception as e:
                logger.logger.info(f"failed with error {e}")
        else:
            logger.logger.info(" Nothing to do right now")
            pass
    except Exception as e:
        logger.logger.info(f"failed with error {e}")