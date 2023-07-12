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
        # await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
        # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
        await client.connect(f'mqtt://{username}:{password}@broker.mmitech.info/')
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

async def process_measurement(topic, payload):
    await manager.broker_messages(topic, payload)
    

    