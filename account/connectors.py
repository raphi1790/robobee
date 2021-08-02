from dataclasses import dataclass
from models import AccountConnector
from dotenv import load_dotenv
import os
import uuid
import hashlib
import hmac
import time
import requests
from urllib.parse import urlencode
from datetime import datetime
import ast

@dataclass
class AccountSimulator(AccountConnector):
    pass


@dataclass 
class BitstampConnector(AccountConnector):

    @staticmethod
    def _get_api_keys():
        load_dotenv()
        client_id = os.environ.get('CLIENT_ID')
        api_key = os.environ.get('API_KEY')
        api_secret = str.encode(os.environ.get('API_SECRET'))

        # print("client_id", client_id)
        # print("api_key", api_key)
        # print("api_secret",api_secret )
        return client_id, api_key, api_secret

    @staticmethod
    def _get_nonce_timestamp_content_type():
        timestamp = str(int(round(time.time() * 1000)))
        nonce = str(uuid.uuid4())
        content_type = 'application/x-www-form-urlencoded'
        return nonce, timestamp, content_type

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _generate_signature(message, api_secret):
        signature = hmac.new(api_secret, msg=message, digestmod=hashlib.sha256).hexdigest()
        return signature

    @staticmethod
    def _get_signature_check(nonce, timestamp, response_header, response_content, api_secret):
        string_to_sign = (nonce + timestamp + response_header.get('Content-Type')).encode('utf-8') + response_content
        signature_check = hmac.new(api_secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
        return signature_check

    @staticmethod
    def _prepare_response(content):
        decoded_content = content.decode("utf-8") 
        content_dict = ast.literal_eval(decoded_content)
        return content_dict
        
    def get_balance(self):
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('balance', order_id=None, amount=None, price=None)

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
        signature = BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
        'https://www.bitstamp.net/api/v2/balance/etheur/',
        headers=headers,
        data=payload_string
        )
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        
        content_dict = BitstampConnector._prepare_response(r.content)
        if bool(content_dict):
            return float(content_dict["eur_available"]),float(content_dict['eth_available'])


    def buy_eth(amount, price):
        pass

    def sell_eth(amount, price):
        pass
