from src import broker, client, logger
from config import *
import sys, signal
import asyncio

def signal_handler(signal, frame):
    logger.logger.info("\nprogram exiting gracefully")
    sys.exit(0)


if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broker_task = loop.create_task(broker.start_broker(ssl))
        if publish:
            logger.logger.info("Starting subscriber and publisher")
            client_publisher = loop.create_task(client.measurement_publisher(credentials['username'], credentials['password'], ssl))
            client_listner = loop.create_task(client.start_client(credentials['username'], credentials['password'], miners, ssl))
            tasks = asyncio.gather(broker_task, client_publisher, client_listner)
        else:
            logger.logger.info("Starting subscriber only")
            client_listner = loop.create_task(client.start_client(credentials['username'], credentials['password'], miners, ssl))
            tasks = asyncio.gather(broker_task, client_listner)
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