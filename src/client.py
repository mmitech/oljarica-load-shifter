import asyncio, json
from config import power_topic
from . import logger, manager
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1


async def start_client(username, password, ssl):
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
        logger.logger.info(" measurement listener connected")
        await client.subscribe([(power_topic, QOS_1)])
        logger.logger.info(" measurement listener subscribed")
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            payload = packet.payload.data.decode()
            logger.logger.debug(f" received message - Topic: {topic}, Payload: {payload}")
            # Call a function to process the received measurement event
            payload = json.loads(payload)
            await process_measurement(topic, payload)
    except ClientException as ce:
        logger.logger.error(" client exception: %s", ce)
    except KeyboardInterrupt:
        await client.unsubscribe(["controllers/readout"])
        await client.disconnect()
        logger.logger.info(" stopped")

async def measurement_publisher(username, password, ssl):
    await asyncio.sleep(3)
    client = MQTTClient()
    try:
        await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
        # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
        logger.logger.info(" measurement publisher connected")
        round = 0
        while True:
            measurement = {
                'sensor_id': 1,
                'value': 25.5 + round,
                'unit': 'Celsius'
            }
            payload = json.dumps(measurement).encode()
            await client.publish(power_topic, payload, QOS_1, retain=True)
            logger.logger.debug(f" publisher: payload= {payload}")
            logger.logger.info(" published measurement Sleeping for 10 secs")
            round += 1
            await asyncio.sleep(10)  # Publish data every 5 seconds
    except ClientException as ce:
        await client.disconnect()
        logger.logger.error(" client exception: %s", ce)
    finally:
        await client.disconnect()


async def process_measurement(topic, payload):
    await manager.broker_messages(topic, payload)
    

    