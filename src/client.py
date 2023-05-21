import asyncio
import json
from . import logger, manager
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1


async def start_client(username, password, miners, ssl):
    config = {
        'keep_alive': 5,
        'ping_delay': 1,
        'auto_reconnect': True
    }
    await asyncio.sleep(2)
    client = MQTTClient(config=config)
    try:
        await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
        # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
        logger.logger.info("Measurement listener connected")
        await client.subscribe([('controllers/readout', QOS_1)])
        logger.logger.info("Measurement listener subscribed")
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            payload = packet.payload.data.decode()
            logger.logger.info(f"Received message - Topic: {topic}, Payload: {payload}")
            # Call a function to process the received measurement event
            await process_measurement(topic, payload, miners)
    except ClientException as ce:
        logger.logger.error("Client exception: %s", ce)
    except KeyboardInterrupt:
        await client.unsubscribe(["controllers/readout"])
        await client.disconnect()
        logger.logger.info("stopped")

async def measurement_publisher(username, password, ssl):
    await asyncio.sleep(5)
    client = MQTTClient()
    try:
        await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
        # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
        logger.logger.info("Measurement publisher connected")
        round = 0
        while True:
            measurement = {
                'sensor_id': 1,
                'value': 25.5 + round,
                'unit': 'Celsius'
            }
            payload = json.dumps(measurement).encode()
            await client.publish('controllers/readout', payload, QOS_1, retain=True)
            # logger.logger.info(f"publisher: payload= {payload}")
            logger.logger.info("Published measurement Sleeping for 10 secs")
            round += 1
            await asyncio.sleep(10)  # Publish data every 5 seconds
    except ClientException as ce:
        await client.disconnect()
        logger.logger.error("Client exception: %s", ce)
    finally:
        await client.disconnect()


async def process_measurement(topic, payload, miners):
    
    logger.logger.info("doing something")
    

    