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
from api.api import get_current_eth_eur_value

@dataclass
class DummyConnector(AccountConnector):
    eth_available:float=0
    eur_available:float=500
    
    def get_balance(self):
        return self.eur_available, self.eth_available

    def buy_eth(self,amount,price):
        if not self._valid_transaction_volume(amount,price,'buy'):
            return 
        self.eth_available += amount
        self.eur_available -= amount*price
    
    def sell_eth(self,amount,price):
        if not self._valid_transaction_volume(amount,price,'sell'):
            return 
        self.eth_available -= amount
        self.eur_available += amount*price




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

    @staticmethod
    def _get_open_orders():
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('open_order',order_id=None, amount=None, price=None)

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
        signature = BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
    'https://www.bitstamp.net/api/v2/open_orders/etheur/',
        headers=headers,
        data=payload_string
        )
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        
        content = r.content.decode("utf-8") 
        content_dict = ast.literal_eval(content)
        print("content", content)

    @staticmethod
    def check_order_status(order_id):
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('check_order', order_id=order_id, amount=None, price=None )

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
        signature = BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
        'https://www.bitstamp.net/api/v2/order_status/',
        headers=headers,
        data=payload_string
        )
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        
        
        return BitstampConnector._prepare_response(r.content)
    
    @staticmethod
    def _cancel_order(order_id):
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('check_order', order_id=order_id, amount=None, price=None )

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
        signature =BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
        'https://www.bitstamp.net/api/v2/cancel_order/',
        headers=headers,
        data=payload_string
        )
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        
        
        return BitstampConnector._prepare_response(r.content)

    @staticmethod
    def _buy_limit_order(amount, price):
        if not (isinstance(price, int) or isinstance(price, float)):
            raise Exception('price is not a number') 
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('buy_sell_order',amount=amount, price=price, order_id=None)

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
        signature = BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
        'https://www.bitstamp.net/api/v2/buy/etheur/',
        headers=headers,
        data=payload_string
        )
        print("payload_string", payload_string)
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        

        return BitstampConnector._prepare_response(r.content)

    def _is_valid_limit_response(response):
        try:
            if bool(response['id']):
                return True
        except:
            return False


    @staticmethod
    def _sell_limit_order(amount, price):
        client_id, api_key, api_secret = BitstampConnector._get_api_keys()
        nonce, timestamp, content_type = BitstampConnector._get_nonce_timestamp_content_type()
        payload_string = BitstampConnector._get_payload_string('buy_sell_order',amount=amount, price=price, order_id=None)

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
        signature = BitstampConnector._generate_signature(message, api_secret)
        headers = BitstampConnector._generate_headers(message, signature, nonce, timestamp,content_type, api_key)

        r = requests.post(
        'https://www.bitstamp.net/api/v2/sell/etheur/',
        headers=headers,
        data=payload_string
        )
        if not r.status_code == 200:
            raise Exception('Status code not 200')

        signature_check = BitstampConnector._get_signature_check(nonce, timestamp, r.headers, r.content, api_secret)
        if not r.headers.get('X-Server-Auth-Signature') == signature_check:
            raise Exception('Signatures do not match')
        
        return BitstampConnector._prepare_response(r.content)
        
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


    def buy_eth(self,amount, price):
        if not self._valid_transaction_volume(amount,price,'buy'):
            print("not enough money on account")
            return 
        if amount <= 0 or amount is None or price is None:
            return 
        latest_trade = get_current_eth_eur_value()
        try: 
            current_etheur_value = latest_trade.price
        except Exception as e: 
            print("Oops!  Something went wrong with fetching the latest live_trades")
            raise e
        # The price might jumped up again on current_etheur_value, therefore, we want to take the value, which satisfied the rules
        base_price = min(current_etheur_value, price) 

        print("base_price", base_price)

        # current_etheur_value= 1000
        for idx in range(3):
            try:
                bidding_value = round(float(base_price) + idx * 0.3 ,2)
                print("bidding_value", bidding_value)
                limit_content = BitstampConnector._buy_limit_order(amount, bidding_value)
                print(limit_content)
                if not BitstampConnector._is_valid_limit_response(limit_content):
                    break
                
                order_id = limit_content['id']
                print("limit_content", limit_content)
                print("order_id", order_id)
                time.sleep(10)
                status_content = BitstampConnector._check_order_status(str(order_id))
                print("status_content", status_content['status'])
                if status_content['status'] == 'Open':
                    if float(status_content['amount_remaining']) < amount:
                        # a subset of the original order is fulfilled
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("open, limit_content", limit_content)
                        # write_transaction(tag,limit_content['id'], limit_content['datetime'], 
                        #         limit_content['price'],limit_content['amount'])
                        return limit_content
                    else:
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("cancel_content",cancel_content)
                elif status_content['status'] == 'Finished':
                    print("finished, limit_content", limit_content)
                    if bool(limit_content['id']):
                        print(limit_content)
                        # write_transaction(tag,limit_content['id'], limit_content['datetime'], 
                        #         limit_content['price'],limit_content['amount'])
                    return limit_content
                else:
                    cancel_content = BitstampConnector._cancel_order(str(order_id))

            except ValueError:
                print("Oops!  Something went wrong with buying ETH")
        return None

    def sell_eth(self,amount, price):
        if not self._valid_transaction_volume(amount,price,'sell'):
            print("not enough eth on account")
            return 
        if amount <= 0 or amount is None or price is None:
            return 
        latest_trade = get_current_eth_eur_value()
        try: 
            current_etheur_value = latest_trade.price
        except Exception as e: 
            print("Oops!  Something went wrong with fetching the latest live_trades")
            raise e
        # The price might jumped up again on current_etheur_value, therefore, we want to take the value, which satisfied the rules
        base_price = max(current_etheur_value, price) 
        # print("base_price", base_price)
        # current_etheur_value= 3000
        for idx in range(3):
            try:
                bidding_value = round(float(base_price) - idx * 0.5 ,2)
                print("bidding_value", bidding_value)
                limit_content = BitstampConnector._sell_limit_order(amount, bidding_value)
                print(limit_content)
                if not BitstampConnector._is_valid_limit_response(limit_content):
                    break
                
                order_id = limit_content['id']
                print("limit_content", limit_content)
                print("order_id", order_id)
                time.sleep(10)
                status_content = BitstampConnector._check_order_status(str(order_id))
                print("status_content", status_content['status'])
                if status_content['status'] == 'Open':
                    if float(status_content['amount_remaining']) < amount:
                        # a subset of the original order is fulfilled
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("open, limit_content", limit_content)
                        # write_transaction('sell',limit_content['id'], limit_content['datetime'], 
                        #         limit_content['price'],limit_content['amount'])
                        return limit_content
                    else:
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("cancel_content",cancel_content)
                elif status_content['status'] == 'Finished':
                    print("finished, limit_content", limit_content)
                    if bool(limit_content['id']):
                        print(limit_content)
                        # write_transaction('sell',limit_content['id'], limit_content['datetime'], 
                        #         limit_content['price'],limit_content['amount'])
                    return limit_content
                else:
                    cancel_content = BitstampConnector._cancel_order(str(order_id))

            except ValueError:
                print("Oops!  Something went wrong with selling ETH")
        return None
