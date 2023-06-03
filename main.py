from src import broker, client, logger, manager
from config import *
import sys, signal, asyncio, json, time
from pyasic import get_miner

# keyboard signal to end the loops
def signal_handler(signal, frame):
    logger.logger.info("\nprogram exiting gracefully")
    sys.exit(0)
    
miners = []

# init the miners API
async def get_miners():
    global miners
    while True:
        miners.clear()
        logger.logger.debug(" connecting to miners")
        for shelf, devices in miners_ips.items():
            for device, ip in devices.items():
                try:
                    logger.logger.debug(f" Trying to init {device} with IP: {ip}")
                    miner =  await get_miner(ip)
                    miners.append(miner)
                except Exception as e:
                    logger.logger.error(f"failed with error {e}")
        # logger.logger.info(f" successfully connected to {len(miners)} miners")
        logger.logger.debug(f"{miners}")
        try:
            await manager.get_miner_data(miners)
            await manager.load_shifting(miners)
            await asyncio.sleep(sleep_duration)
        except Exception as e:
            logger.logger.error(f"An error occurred: {e}")
            logger.logger.info("Restarting in 5 seconds...")
            time.sleep(5)  

if __name__ == '__main__':
    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            broker_task = loop.create_task(broker.start_broker(ssl))
            if publish:
                logger.logger.info("Starting subscriber and publisher")
                init_miners = loop.create_task(get_miners())
                client_publisher = loop.create_task(client.measurement_publisher(credentials['username'], credentials['password'], ssl))
                client_listner = loop.create_task(client.start_client(credentials['username'], credentials['password'], ssl))
                tasks = asyncio.gather(broker_task, client_publisher, client_listner,init_miners)
            else:
                logger.logger.info("Starting subscriber only")
                init_miners = loop.create_task(get_miners())
                client_listner = loop.create_task(client.start_client(credentials['username'], credentials['password'], ssl))
                tasks = asyncio.gather(broker_task, client_listner,init_miners)
            signal.signal(signal.SIGINT, signal_handler)
            logger.logger.info("started. Press Ctrl+C to stop.")
            loop.run_forever()
        except KeyboardInterrupt:
            broker_task.cancel()
            client_listner.cancel()
            if publish:
                client_publisher.cancel()
            loop.stop
            logger.logger.info("MQTT broker stopped.")
        except Exception as e:
            logger.logger.error(f"An error occurred: {e}")
            logger.logger.info("Restarting in 5 seconds...")
            time.sleep(5)