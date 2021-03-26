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
from datetime import datetime


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


def _prepare_response(content):
    decoded_content = content.decode("utf-8") 
    content_dict = ast.literal_eval(decoded_content)
    return content_dict


def _connect_influx_db():
    load_dotenv()
    user=os.getenv("INFLUX_DB_USER")
    password=os.getenv("INFLUX_DB_PASSWORD")
    client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    return client 

def write_transaction(type,id, timestamp, price, amount):
    try:
        client = _connect_influx_db()
        point = [
                            {
                                "measurement": "transactions",
                                "tags": {
                                    "currency": "EUR",
                                    "exchange": "Bitstamp",
                                    "type": type,
                                    "id": str(id)
                                
                                },
                                "time": timestamp,
                                "fields": {
                                    "price": float(price),
                                    "amount": float(amount) 
                                }
                            }
                    ]

        client.write_points(point)
    except Exception as e:
        print(e)

def _is_valid_limit_response(response):
    try:
        if bool(response['id']):
            return True
    except:
        return False




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
    
    content_dict = _prepare_response(r.content)
    if bool(content_dict):
        return float(content_dict["eur_available"]),float(content_dict['eth_available'])


def get_current_eth_eur_value():
    client = _connect_influx_db()
    #print("DB-connection established:", client)
    result_set = client.query('SELECT value FROM ethereum_price WHERE time > now() - 2m order by time desc limit 1')
    if len(result_set) > 0:
        result_points = list(result_set.get_points("ethereum_price"))
        return float(result_points[0]['value'])
    else:
        return None

def get_eth_eur_values(interval_str='1d',to_dt_str='now()' ):
    client = _connect_influx_db()
    query_str = f"SELECT value FROM ethereum_price WHERE time > {to_dt_str} - {interval_str} order by time desc"
    # print("query_str", query_str)
    result_set = client.query(query_str)
    if len(result_set) > 0:
        result_points = list(result_set.get_points("ethereum_price"))
        # Reverse order such that most recent stock_price is at idx = lenght - 1
        return [float(result_points[idx]['value']) for idx in reversed(range(len(result_points)))]
    else:
        return None

def get_last_transaction_price(type='buy'):
    client = _connect_influx_db()
    # print("DB-connection established:", client)
    query = f"""SELECT * FROM transactions WHERE type = '{type}' order by time desc limit 1"""
    result_set = client.query(query)
    if len(result_set) > 0:
        result_points = list(result_set.get_points("transactions"))
        return float(result_points[0]['price'])
    else:
        return None


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
    
    
    return _prepare_response(r.content)
 

def cancel_order(order_id):
    client_id, api_key, api_secret = _get_api_keys()
    nonce, timestamp, content_type = _get_nonce_timestamp_content_type()
    payload_string = _get_payload_string('check_order', order_id=order_id, amount=None, price=None )

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        '/api/v2/cancel_order/' + \
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
    'https://www.bitstamp.net/api/v2/cancel_order/',
    headers=headers,
    data=payload_string
    )
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    
    
    return _prepare_response(r.content)



def buy_limit_order(amount, price):
    if not (isinstance(price, int) or isinstance(price, float)):
        raise Exception('price is not a number') 
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
    print("payload_string", payload_string)
    if not r.status_code == 200:
        raise Exception('Status code not 200')

    signature_check = _get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
    if not r.headers.get('X-Server-Auth-Signature') == signature_check:
        raise Exception('Signatures do not match')
    

    return _prepare_response(r.content)
 



def buy_eth(amount):
    if amount <= 0 or amount is None:
        return 
    # current_etheur_value = get_current_eth_eur_value()
    current_etheur_value= 1000
    for idx in range(3):
        try:
            bidding_value = round(current_etheur_value + idx * 0.3 ,2)
            print("bidding_value", bidding_value)
            limit_content = buy_limit_order(amount, bidding_value)
            print(limit_content)
            if not _is_valid_limit_response(limit_content):
                break
            
            order_id = limit_content['id']
            print("limit_content", limit_content)
            print("order_id", order_id)
            time.sleep(10)
            status_content = check_order_status(str(order_id))
            print("status_content", status_content['status'])
            if status_content['status'] == 'Open':
                if float(status_content['amount_remaining']) < amount:
                    # a subset of the original order is fulfilled
                    cancel_content = cancel_order(str(order_id))
                    print("open, limit_content", limit_content)
                    write_transaction('buy',limit_content['id'], limit_content['datetime'], 
                            limit_content['price'],limit_content['amount'])
                    return limit_content
                else:
                    cancel_content = cancel_order(str(order_id))
                    print("cancel_content",cancel_content)
            elif status_content['status'] == 'Finished':
                print("finished, limit_content", limit_content)
                if bool(limit_content['id']):
                    print(limit_content)
                    write_transaction('buy',limit_content['id'], limit_content['datetime'], 
                            limit_content['price'],limit_content['amount'])
                return limit_content
            else:
                cancel_content = cancel_order(str(order_id))

        except ValueError:
            print("Oops!  Something went wrong with buying ETH")
    return None
        
   
       
       
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
    
    return _prepare_response(r.content)


def sell_eth(amount):
    if amount <= 0 or amount is None:
        return 
    current_etheur_value = get_current_eth_eur_value()
    print("current_value", current_etheur_value)
    # current_etheur_value= 3000
    for idx in range(3):
        try:
            bidding_value = round(float(current_etheur_value) - idx * 0.5 ,2)
            print("bidding_value", bidding_value)
            limit_content = sell_limit_order(amount, bidding_value)
            print(limit_content)
            if not _is_valid_limit_response(limit_content):
                break
            
            order_id = limit_content['id']
            print("limit_content", limit_content)
            print("order_id", order_id)
            time.sleep(10)
            status_content = check_order_status(str(order_id))
            print("status_content", status_content['status'])
            if status_content['status'] == 'Open':
                if float(status_content['amount_remaining']) < amount:
                    # a subset of the original order is fulfilled
                    cancel_content = cancel_order(str(order_id))
                    print("open, limit_content", limit_content)
                    write_transaction('sell',limit_content['id'], limit_content['datetime'], 
                            limit_content['price'],limit_content['amount'])
                    return limit_content
                else:
                    cancel_content = cancel_order(str(order_id))
                    print("cancel_content",cancel_content)
            elif status_content['status'] == 'Finished':
                print("finished, limit_content", limit_content)
                if bool(limit_content['id']):
                    print(limit_content)
                    write_transaction('sell',limit_content['id'], limit_content['datetime'], 
                            limit_content['price'],limit_content['amount'])
                return limit_content
            else:
                cancel_content = cancel_order(str(order_id))

        except ValueError:
            print("Oops!  Something went wrong with selling ETH")
    return None






