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
from urllib.parse import urlencode


def _get_api_keys():
    load_dotenv()
    client_id = os.environ.get('CLIENT_ID')
    api_key = os.environ.get('API_KEY')
    api_secret = str.encode(os.environ.get('API_SECRET'))

    # print("client_id", client_id)
    # print("api_key", api_key)
    # print("api_secret",api_secret )
    return client_id, api_key, api_secret

def _get_nonce_timestamp_content_type():
    timestamp = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    content_type = 'application/x-www-form-urlencoded'
    return nonce, timestamp, content_type

def _generate_headers(message, signature, nonce, timestamp, content_type, api_key):
    headers = {
        'X-Auth': 'BITSTAMP ' + api_key,
        'X-Auth-Signature': signature,
        'X-Auth-Nonce': nonce,
        'X-Auth-Timestamp': timestamp,
        'X-Auth-Version': 'v2',
        'Content-Type': content_type
    }
    return headers

def _get_payload_string(mode, order_id, amount, price):
    timestamp = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    content_type = 'application/x-www-form-urlencoded'
    if mode == 'balance' or mode == 'buy_order' or mode == 'open_order':
        payload = {'offset': '1' }
    
    if mode == 'check_order': 
        payload = {'offset': '1',
                'id': str(order_id)} # "1336540724711425"

    if mode== 'buy_sell_order':
        payload = {'offset': '1',
                'amount': amount,
                'price': price
                }

    payload_string = urlencode(payload)
    
    return payload_string

def _generate_signature(message, api_secret):
    signature = hmac.new(api_secret, msg=message, digestmod=hashlib.sha256).hexdigest()
    return signature


def _get_signature_check(nonce, timestamp, response_header, response_content, api_secret):
    string_to_sign = (nonce + timestamp + response_header.get('Content-Type')).encode('utf-8') + response_content
    signature_check = hmac.new(api_secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
    return signature_check


def get_balance():
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('balance', order_id=None, amount=None, price=None)

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
    signature = _generate_signature(message, api_secret)
    headers = _generate_headers(message, signature, nonce, timestamp,content_type, api_key)

    r = requests.post(
    'https://www.bitstamp.net/api/v2/balance/etheur/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    print("content", content)
    if bool(content_dict):
        return content_dict["eur_available"], content_dict['eth_available']


def get_current_eth_eur_value():
    load_dotenv()
    user=os.getenv("INFLUX_DB_USER")
    password=os.getenv("INFLUX_DB_PASSWORD")
    client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    #print("DB-connection established:", client)

    result_set = client.query('SELECT value FROM ethereum_price WHERE time > now() - 2m order by time desc limit 1')
    if len(result_set) > 0:
        result_points = list(result_set.get_points("ethereum_price"))
        return result_points[0]['value']


def get_open_orders():
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('open_order',order_id=None, amount=None, price=None)

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/open_orders/etheur/' + \
        '' + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = _generate_signature(message, api_secret)
    headers = _generate_headers(message, signature, nonce, timestamp,content_type, api_key)

    r = requests.post(
   'https://www.bitstamp.net/api/v2/open_orders/etheur/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    print("content", content)


def check_order_status(order_id):
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('check_order', order_id=order_id, amount=None, price=None )

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/order_status/' + \
        '' + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = _generate_signature(message, api_secret)
    headers = _generate_headers(message, signature, nonce, timestamp,content_type, api_key)

    r = requests.post(
    'https://www.bitstamp.net/api/v2/order_status/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    print("content", content)
 

def buy_limit_order(amount, price):
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('buy_sell_order',amount=amount, price=price, order_id=None)

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/buy/etheur/' + \
        '' + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = _generate_signature(message, api_secret)
    headers = _generate_headers(message, signature, nonce, timestamp,content_type, api_key)

    r = requests.post(
     'https://www.bitstamp.net/api/v2/buy/etheur/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    print("content", content)


def sell_limit_order(amount, price):
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('buy_sell_order',amount=amount, price=price, order_id=None)

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/sell/etheur/' + \
        '' + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = _generate_signature(message, api_secret)
    headers = _generate_headers(message, signature, nonce, timestamp,content_type, api_key)

    r = requests.post(
     'https://www.bitstamp.net/api/v2/sell/etheur/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    content = r.content.decode("utf-8") 
    content_dict = ast.literal_eval(content)
    print("content", content)









