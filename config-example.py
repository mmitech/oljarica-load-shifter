publish = True
credentials = {
    'username': 'admin', 
    'password': 'admin123!!!',
}
ssl = {
    'key': './ssl/mqtt-selfsigned.key',
    'crt': './ssl/mqtt-selfsigned.crt'
}
miners = {
    '001' : '192.168.3.211:3000',
    '002' : '192.168.3.212:3000',
    '003' : '192.168.3.213:3000',
}