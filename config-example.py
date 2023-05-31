# publish test data to the broker (used for teting the sumbscription and data processing)
publish = False

# The hydro power plant power produced is not constant, 
# it jumps up and down every second, we give our algo a buffer
# to use and not go crazy about stopping and starting miners
buffer = 10

# this is the average power for 1 miner afer optemization
# we use this to calculate the amount of miners we need to start/stop
miner_avg_kw = 2.5

# Broker credentials
credentials = {
    'username': 'test', 
    'password': 'test123!!!',
}

#topic to subscribe to
power_topic = "controllers/readout"

# SSL if MQTTS is used instead of MQTT
ssl = {
    'key': './ssl/mqtt-selfsigned.key',
    'crt': './ssl/mqtt-selfsigned.crt'
}

# TODO this use the pool and address/username to set miners automatically
pools = {
    "nicehash": "stratum+tcp://sha256asicboost.auto.nicehash.com:9200"
}
BTC_Address = "something"

# the host names and IPs of our miners
miners_ips = {
    "shelf_1" : {
        'S1982T-01' : '10.10.0.101',
        'S1982T-02' : '10.10.0.102',
        'S1982T-03' : '10.10.0.103',
        'S1982T-04' : '10.10.0.104',
        'S1982T-05' : '10.10.0.105',
        'S1982T-06' : '10.10.0.106',
        'S1982T-19' : '10.10.0.119',
        'S1982T-20' : '10.10.0.120',
        'S1982T-21' : '10.10.0.121',
        'S1982T-22' : '10.10.0.122',
        'S1982T-23' : '10.10.0.123',
        'S1982T-24' : '10.10.0.124',
        'S1982T-37' : '10.10.0.137',
        'S1982T-38' : '10.10.0.138',
        'S1982T-39' : '10.10.0.139',
        'S1982T-40' : '10.10.0.140',
        'S1982T-41' : '10.10.0.141',
        'S1982T-42' : '10.10.0.142',
    },
    "shelf_2": {
        'S1982T-07' : '10.10.0.107',
        'S1982T-08' : '10.10.0.108',
        'S1982T-09' : '10.10.0.109',
        'S1982T-10' : '10.10.0.110',
        'S1982T-11' : '10.10.0.111',
        'S1982T-12' : '10.10.0.112',
        'S1982T-25' : '10.10.0.125',
        'S1982T-26' : '10.10.0.126',
        'S1982T-27' : '10.10.0.127',
        'S1982T-28' : '10.10.0.128',
        'S1982T-29' : '10.10.0.129',
        'S1982T-30' : '10.10.0.130',
        'S1982T-43' : '10.10.0.143',
        'S1982T-44' : '10.10.0.144',
        'S1982T-45' : '10.10.0.145',
        'S1982T-46' : '10.10.0.146',
        'S1982T-47' : '10.10.0.147',
        'S1982T-48' : '10.10.0.148',
        
    },
    "Shelf_3": {
        'S1982T-13' : '10.10.0.113',
        'S1982T-14' : '10.10.0.114',
        'S1982T-15' : '10.10.0.115',
        'S1982T-16' : '10.10.0.116',
        'S1982T-17' : '10.10.0.117',
        'S1982T-18' : '10.10.0.118',
        'S1982T-31' : '10.10.0.131',
        'S1982T-32' : '10.10.0.132',
        'S1982T-33' : '10.10.0.133',
        'S1982T-34' : '10.10.0.134',
        'S1982T-35' : '10.10.0.135',
        'S1982T-36' : '10.10.0.136',
        'S1982T-49' : '10.10.0.149',
        'S1982T-50' : '10.10.0.150',
    }
}