from dataclasses import dataclass

import pytz
from models import AccountBalance, AccountConnector, InfluxConnector, Transaction
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
from binance.client import Client

@dataclass
class DummyConnector(AccountConnector):
    account_balance: AccountBalance


    def __init__(self):
        self.update_balance()
        self.eth_reserve = float(os.getenv('DUMMY_RESERVE_ETH'))
        self.eur_reserve = float(os.getenv('DUMMY_RESERVE_EUR'))
        self.fee = float(os.getenv("DUMMY_CONNECTOR_FEE"))
    
    def get_balance(self):
        return self.account_balance
    
    def tradeable_eth(self):
        return super().tradeable_eth()
    
    def tradeable_eur(self):
        return super().tradeable_eur()

    def update_balance(self):
        latest_trade = get_current_eth_eur_value(connector="binance")
        try: 
            current_etheur_value = float(latest_trade.price)
        except Exception as e: 
            print("Oops!  Something went wrong with fetching the latest live_trades")
            raise e
        influx_connector = InfluxConnector()
        client = influx_connector.get_client()
        query_str = f"SELECT time, exchange, pair, eth_available,eur_available,balance_total FROM simulator_account_balance  order by time desc limit 1"
        result_set = client.query(query_str)
        if len(result_set) > 0:
            result_points = list(result_set.get_points("simulator_account_balance"))
            self.account_balance = AccountBalance(timestamp_utc=datetime.utcnow()
                            ,exchange=result_points[0]['exchange']
                            ,pair=result_points[0]['pair']
                            ,eth_available=result_points[0]['eth_available']
                            ,eur_available=result_points[0]['eur_available']
                            ,balance_total=current_etheur_value* result_points[0]['eth_available']  + result_points[0]['eur_available']
            )
            
            self._write_account_balance(self.account_balance, connector="simulator")


    def buy_eth(self,amount,price):
        if not self._valid_transaction_volume(amount,price,'buy'):
            return 
        eur = amount*price
        available_eur = eur/(1+self.fee)
        new_eth = available_eur/price
        self.account_balance.eth_available += new_eth
        self.account_balance.eur_available -= eur
        transaction = Transaction(timestamp_utc=datetime.utcnow()
                        , exchange="Bitstamp", pair="ETH-EUR", amount=float(amount)
                        , price=float(price)
                        ,id ='a'
                        ,type="buy" )
        self._write_transaction(transaction, connector="simulator")
        self._write_account_balance(self.account_balance, connector="simulator")

    
    def sell_eth(self,amount,price):
        if not self._valid_transaction_volume(amount,price,'sell'):
            return 
        new_eur = amount*price/(1+self.fee)
        self.account_balance.eth_available -= amount
        self.account_balance.eur_available += new_eur
        transaction = Transaction(timestamp_utc=datetime.utcnow()
                        , exchange="Bitstamp", pair="ETH-EUR", amount=float(amount)
                        , price=float(price)
                        ,id ='a'
                        ,type="sell" )
        self._write_transaction(transaction, connector="simulator")
        self._write_account_balance(self.account_balance,connector="simulator")


    def get_last_transaction(self, **kwargs):
        transaction = super(DummyConnector, self).get_last_transaction(connector="simulator", **kwargs )
        return transaction


@dataclass 
class BitstampConnector(AccountConnector):
    account_balance:AccountBalance

    def __init__(self):
        self.update_balance()
        self.eth_reserve = float(os.getenv('BITSTAMP_RESERVE_ETH'))
        self.eur_reserve = float(os.getenv('BITSTAMP_RESERVE_EUR'))
        self.fee = float(os.getenv("BITSTAMP_CONNECTOR_FEE"))

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
    def _check_order_status(order_id):
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
        return self.account_balance
    
    def tradeable_eth(self):
        return super().tradeable_eth()
    
    def tradeable_eur(self):
        return super().tradeable_eur()

    def update_balance(self):
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
            latest_trade = get_current_eth_eur_value()
            try: 
                current_etheur_value = latest_trade.price
            except Exception as e: 
                print("Oops!  Something went wrong with fetching the latest live_trades")
                raise e

            self.account_balance=AccountBalance(timestamp_utc=datetime.utcnow()
                ,pair="ETH-EUR"
                ,exchange="Bitstamp"
                ,eth_available=float(content_dict['eth_available'])
                ,eur_available=float(content_dict["eur_available"])
                ,balance_total=float(current_etheur_value)*float(content_dict['eth_available']) + float(content_dict["eur_available"])
            )
            self._write_account_balance(self.account_balance, connector="bitstamp")



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
                        transaction = Transaction(timestamp_utc=datetime.strptime(limit_content['datetime'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
                                                , exchange="Bitstamp", pair="ETH-EUR", amount=float(limit_content['amount'])
                                                , price=float(limit_content['price'])
                                                ,id =str(limit_content['id'])
                                                ,type="buy" )
                        self._write_transaction(transaction, connector="bitstamp")
                        return limit_content
                    else:
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("cancel_content",cancel_content)
                elif status_content['status'] == 'Finished':
                    print("finished, limit_content", limit_content)
                    if bool(limit_content['id']):
                        print(limit_content)
                        transaction = Transaction(timestamp_utc=datetime.strptime(limit_content['datetime'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
                                                , exchange="Bitstamp", pair="ETH-EUR", amount=float(limit_content['amount'])
                                                , price=float(limit_content['price'])
                                                ,id =str(limit_content['id'])
                                                ,type="buy" )
                        self._write_transaction(transaction, connector="bitstamp")
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
                        transaction = Transaction(timestamp_utc=datetime.strptime(limit_content['datetime'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
                                                , exchange="Bitstamp", pair="ETH-EUR", amount=float(limit_content['amount'])
                                                , price=float(limit_content['price'])
                                                ,id =str(limit_content['id'])
                                                ,type="sell" )
                        self._write_transaction(transaction, connector="bitstamp")
                        return limit_content
                    else:
                        cancel_content = BitstampConnector._cancel_order(str(order_id))
                        print("cancel_content",cancel_content)
                elif status_content['status'] == 'Finished':
                    print("finished, limit_content", limit_content)
                    if bool(limit_content['id']):
                        print(limit_content)
                        transaction = Transaction(timestamp_utc=datetime.strptime(limit_content['datetime'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
                                                , exchange="Bitstamp", pair="ETH-EUR", amount=float(limit_content['amount'])
                                                , price=float(limit_content['price'])
                                                ,id =str(limit_content['id'])
                                                ,type="sell" )
                        self._write_transaction(transaction, connector="bitstamp")
                    return limit_content
                else:
                    cancel_content = BitstampConnector._cancel_order(str(order_id))

            except ValueError:
                print("Oops!  Something went wrong with selling ETH")
        return None

    def get_last_transaction(self, **kwargs):
        transaction = super(BitstampConnector, self).get_last_transaction(connector="bitstamp", **kwargs)
        return transaction

@dataclass
class BinanceConnector(AccountConnector):
    account_balance:AccountBalance

    def _initialize_binance_client(self):
        api_key = os.environ.get('BINANCE_API_KEY')
        api_secret = os.environ.get('BINANCE_API_SECRET')
        client = Client(api_key, api_secret)
        print("client", client)
        return client

    def __init__(self):
        self.update_balance()
        self.eth_reserve = float(os.getenv('BINANCE_RESERVE_ETH'))
        self.eur_reserve = float(os.getenv('BINANCE_RESERVE_EUR'))
        self.fee = float(os.getenv("BINANCE_CONNECTOR_FEE"))

    def update_balance(self):
        try: 
            binance_client = self._initialize_binance_client()
            eur_available = float(binance_client.get_asset_balance(asset='EUR')['free'])
            eth_available = float(binance_client.get_asset_balance(asset='ETH')['free'])
        except Exception as e: 
            print("Oops!  Something went wrong with accessing the account")
            raise e

        latest_trade = get_current_eth_eur_value(connector='binance')
        try: 
            current_etheur_value = float(latest_trade.price)
            print("current_etheur_value", current_etheur_value)
        except Exception as e: 
            print("Oops! Something went wrong with fetching the latest live_trades")
            raise e

        self.account_balance=AccountBalance(timestamp_utc=datetime.utcnow()
            ,pair="ETH-EUR"
            ,exchange="Binance"
            ,eth_available=eth_available
            ,eur_available=eur_available
            ,balance_total=current_etheur_value*eth_available + eur_available
        )
        self._write_account_balance(self.account_balance, connector="binance")

 
    
    def _valid_transaction_volume(self, amount, price, transaction_type):
        if price is None:
            return False
        eur_necessary = round(amount * price,2)
        eth_necessary = amount


        # print("eur_available",self.account_balance.eur_available )
        # print("eth_available",self.account_balance.eth_available )
        # print("eur_necessary",eur_necessary )
        # print("eth_necessary",eth_necessary )

        if(transaction_type == 'buy'):
            return self.account_balance.eur_available > eur_necessary
        if(transaction_type == 'sell'):
            return self.account_balance.eth_available > eth_necessary
        else:
            return False

    def tradeable_eth(self):
        return self.account_balance.eth_available - self.eth_reserve
    
    def tradeable_eur(self):
        return self.account_balance.eur_available - self.eur_reserve

    def _write_transaction(self,transaction:Transaction, connector):
        try:
            influx_connector = InfluxConnector()
            influx_connector.write_point(transaction.to_influx(connector=connector))
        except Exception as e:
            print(e)

    def _write_account_balance(self, acount_balance:AccountBalance, connector):
        try:
            influx_connector = InfluxConnector()
            print("account_balance.to_influx()", acount_balance.to_influx(connector=connector))
            influx_connector.write_point(acount_balance.to_influx(connector=connector))
        except Exception as e:
            print(e)
    

    def get_last_transaction(self, **kwargs):
        transaction = super(BinanceConnector, self).get_last_transaction(connector="binance", **kwargs)
        return transaction

        
    def get_balance(self):
        return self.account_balance

    def buy_eth(self,amount, price):
        if not self._valid_transaction_volume(amount,price,'buy'):
            print("not enough money on account")
            return 
        if amount <= 0 or amount is None or price is None:
            return 
        latest_trade = get_current_eth_eur_value(connector="binance")
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
                order = self._buy_limit_order(amount, bidding_value)
                print(order)
                if not self._is_valid_limit_response(order):
                    break
                
                order_id = order['orderId']
                print("order", order)
                print("order_id", order_id)
                time.sleep(10)
                status_content = self._check_order_status(order_id)
                print("status_content", status_content['status'])
                if status_content['status'] == 'FILLED':
                    transaction = Transaction(timestamp_utc=datetime.fromtimestamp(status_content['time']/ 1000.0).astimezone(pytz.utc)
                                                , exchange="Binance", pair="ETH-EUR", amount=float(status_content['executedQty'])
                                                , price=float(status_content['price'])
                                                ,id =str(status_content['orderId'])
                                                ,type="buy" )
                    self._write_transaction(transaction, connector="binance")
                    return status_content    

            except ValueError:
                print("Oops!  Something went wrong with buying ETH")
        return None

    def sell_eth(self,amount, price):
        if not self._valid_transaction_volume(amount,price,'sell'):
            print("not enough eth on account")
            return 
        if amount <= 0 or amount is None or price is None:
            return 
        latest_trade = get_current_eth_eur_value(connector="binance")
        try: 
            current_etheur_value = latest_trade.price
        except Exception as e: 
            print("Oops!  Something went wrong with fetching the latest live_trades")
            raise e
        # The price might jumped up again on current_etheur_value, therefore, we want to take the value, which satisfied the rules
        base_price = max(current_etheur_value, price) 
        print("base_price", base_price)

        # current_etheur_value= 1000
        for idx in range(3):
            try:
                bidding_value = round(float(base_price) - idx * 0.5 ,2)
                print("bidding_value", bidding_value)
                order = self._sell_limit_order(amount, bidding_value)
                print(order)
                if not self._is_valid_limit_response(order):
                    break
                
                order_id = order['orderId']
                print("order", order)
                print("order_id", order_id)
                time.sleep(10)
                status_content = self._check_order_status(order_id)
                print("status_content", status_content['status'])
                if status_content['status'] == 'FILLED':
                    transaction = Transaction(timestamp_utc=datetime.fromtimestamp(status_content['time']/ 1000.0).astimezone(pytz.utc)
                                                , exchange="Binance", pair="ETH-EUR", amount=float(status_content['executedQty'])
                                                , price=float(status_content['price'])
                                                ,id =str(status_content['orderId'])
                                                ,type="sell" )
                    self._write_transaction(transaction, connector="binance")
                    return status_content    

            except ValueError:
                print("Oops!  Something went wrong with selling ETH")
        return None

    def _sell_limit_order(self, amount, price):
        client = self._initialize_binance_client()
        order = client.order_limit_sell(
            symbol='ETHEUR',
            timeInForce='FOK',
            quantity=amount,
            price=price)
        return order

    def _buy_limit_order(self, amount, price):
        client = self._initialize_binance_client()
        order = client.order_limit_buy(
            symbol='ETHEUR',
            timeInForce='FOK',
            quantity=amount,
            price=price)
        return order
    
    def _is_valid_limit_response(self, response):
        try:
            if bool(response['orderId']):
                return True
        except:
            return False

    def _check_order_status(self, order_id):
        client = self._initialize_binance_client()
        all_orders = client.get_all_orders(symbol='ETHEUR')
        current_order = [x for x in all_orders if x['orderId'] == order_id][0]
        return current_order

    def _write_transaction(self,transaction:Transaction, connector):
        try:
            influx_connector = InfluxConnector()
            influx_connector.write_point(transaction.to_influx(connector=connector))
        except Exception as e:
            print(e)



