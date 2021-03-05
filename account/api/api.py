import hashlib
import hmac
import time
import requests
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
import ast
from influxdb import InfluxDBClient


def _get_api_keys():
    load_dotenv()
    client_id = os.environ.get('CLIENT_ID')
    api_key = os.environ.get('API_KEY')
    api_secret = str.encode(os.environ.get('API_SECRET'))

    # print("client_id", client_id)
    # print("api_key", api_key)
    # print("api_secret",api_secret )
    return client_id, api_key, api_secret


def get_balance():
    client_id, api_key, api_secret = _get_api_keys()
    timestamp = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    content_type = 'application/x-www-form-urlencoded'
    payload = {'offset': '1'}

    if sys.version_info.major >= 3:
        from urllib.parse import urlencode
    else:
        from urllib import urlencode

    payload_string = urlencode(payload)

    # '' (empty string) in message represents any query parameters or an empty string in case there are none
    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/balance/etheur/' + \
        '' + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = hmac.new(api_secret, msg=message, digestmod=hashlib.sha256).hexdigest()
    headers = {
        'X-Auth': 'BITSTAMP ' + api_key,
        'X-Auth-Signature': signature,
        'X-Auth-Nonce': nonce,
        'X-Auth-Timestamp': timestamp,
        'X-Auth-Version': 'v2',
        'Content-Type': content_type
    }
    r = requests.post(
    'https://www.bitstamp.net/api/v2/balance/etheur/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    string_to_sign = (nonce + timestamp + r.headers.get('Content-Type')).encode('utf-8') + r.content
    signature_check = hmac.new(api_secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    if bool(content_dict):
        return content_dict["eur_available"], content_dict['eth_available']

def get_current_eth_eur_value():
    load_dotenv()
    user=os.getenv("INFLUX_DB_USER")
    password=os.getenv("INFLUX_DB_PASSWORD")
    client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    print("DB-connection established:", client)

    result_set = client.query('SELECT value FROM ethereum_price WHERE time > now() - 2d limit 1')
    if len(result_set) > 0:
        result_points = list(result_set.get_points("ethereum_price"))
        return result_points[0]['value']







