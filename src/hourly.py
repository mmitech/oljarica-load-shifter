import json, datetime
from . import logger
from config import power_topic
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1
 

async def manual_process(manual_reading, current_time, username, password):
    if manual_reading and current_time >= datetime.time(19, 0) or current_time < datetime.time(8, 0):
        client = MQTTClient()
        try:
            await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
            # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
            logger.logger.info(" measurement publisher connected")
            measurement = {
                'sensor_id': 1,
                'value': -150,
                'unit': 'KW'
            }
            payload = json.dumps(measurement).encode()
            await client.publish(power_topic, payload, QOS_1, retain=True)
            logger.logger.debug(f" publisher: payload= {payload}")
            logger.logger.info(" published measurement Sleeping ")
        except ClientException as ce:
            await client.disconnect()
            logger.logger.error(" client exception: %s", ce)
        finally:
            await client.disconnect()
    elif manual_reading and current_time >= datetime.time(8, 0) or current_time < datetime.time(19, 0):
        client = MQTTClient()
        try:
            await client.connect(f'mqtt://{username}:{password}@127.0.0.1:1883')
            # await client.connect(f'mqtts://{username}:{password}@broker.mmitech.info/', cafile={ssl['crt']})
            logger.logger.info(" measurement publisher connected")
            measurement = {
                'sensor_id': 1,
                'value': 150,
                'unit': 'KW'
            }
            payload = json.dumps(measurement).encode()
            await client.publish(power_topic, payload, QOS_1, retain=True)
            logger.logger.debug(f" publisher: payload= {payload}")
            logger.logger.info(" published measurement Sleeping ")
        except ClientException as ce:
            await client.disconnect()
            logger.logger.error(" client exception: %s", ce)
        finally:
            await client.disconnect()
    else:
        logger.logger.debug(f" manual hourly processing is disabled")