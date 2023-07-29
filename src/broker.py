import os
from . import  logger
import hbmqtt.broker as mqtt_broker

async def start_broker(ssl):
    config = {
        'listeners': {
            'default': {
                'type': 'tcp',
                'bind': '0.0.0.0:1883',
            },
            # 'ws-mqtt': {
            #     'bind': '0.0.0.0:8080',
            #     'type': 'ws',
            #     "max_connections": 10,
            # },
            'ssl': {
                'bind': '0.0.0.0:8883',
                'type': 'tcp',
                'ssl': True,
                'certfile': ssl['crt'],  
                'keyfile': ssl['key'],
            },
        },
        'sys_interval': 10,
        'auth': {
            'allow-anonymous': True,
            'password-file': os.path.join(os.path.dirname(os.path.realpath(__file__)), "../auth.conf"),
            'plugins': ['auth_file', 'auth_anonymous'],

        },
        'topic-check': {
            'enabled': True,
            'plugins': ['topic_acl'],
            'acl': {
                'admin': ['#'],
                'anonymous': [],
            },
        },
    }
    
    try:
        broker = mqtt_broker.Broker(config)
        await broker.start()
        
    except KeyboardInterrupt:
        await broker.shutdown()
        logger.logger.info(" stopped")
    
