from dataclasses import dataclass
from datetime import datetime
import json
import os
import time
from dotenv.main import load_dotenv

from influxdb.client import InfluxDBClient
import pytz
try:
    import thread
except ImportError:
    import _thread as thread
import time


@dataclass
class LiveTrade:
    timestamp_utc: datetime
    pair: str
    exchange: str
    price: float

    def to_influx(self, websocket_connector_prefix: str):
        return {
                        "measurement": f"{websocket_connector_prefix}_live_trades",
                        "tags": {
                            "pair": self.pair,
                            "exchange": self.exchange
                        
                        },
                        "time": str(self.timestamp_utc),
                        "fields": {
                            "price": float(self.price) 
                        }
        }
                    
        
@dataclass
class BitstampLiveTrade(LiveTrade):

    def to_influx(self):
        super.to_influx(self, connector="bitstamp")  


@dataclass
class BinanceLiveTrade(LiveTrade):

    def to_influx(self):
        super.to_influx(self, connector="binance")   

@dataclass
class WebsocketConnector:
    url:str
    prefix:str

    def on_message():
        pass
    
    def on_open():
        pass

@dataclass
class BitstampWebsocketConnector(WebsocketConnector):
    url:str="wss://ws.bitstamp.net"
    prefix:str="bitstamp"

    def on_message(self, ws, message, buffer, influx_connector, aggregation_level):
        obj = json.loads(message)
        if bool(obj['data']) :
            price = obj['data']['price']
            timestamp = obj['data']['timestamp']
            utc_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
            current_trade = LiveTrade(utc_timestamp, pair="ETH-EUR" , exchange="Bitstamp", price=price)
            buffer.append(current_trade)

        
        time_difference_buffer = buffer.get_time_difference()
        if time_difference_buffer > aggregation_level:
            buffer_data = buffer.get_data()
            if len(buffer_data) == 1:
                first_buffer_element = buffer_data[0]
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                
                
                
            if len(buffer_data) > 1:
                first_buffer_element = buffer_data[0]
                last_buffer_element = buffer_data[len(buffer_data) -1]
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                influx_connector.write_point(last_buffer_element.to_influx(self.prefix))
                
            buffer.reset_data()
    
    def on_open(self, ws):
        def run(*args):
            # request websocket data
            websocket_request_data =  {
                "event": "bts:subscribe",
                "data": {
                    "channel": "live_trades_etheur"
                }
            }
            websocket_request_data_json = json.dumps(websocket_request_data)
            ws.send(websocket_request_data_json)
        thread.start_new_thread(run, ())
        time.sleep(0.01)
        print("websocket-connection established.")  

@dataclass
class BinanceWebsocketConnector(WebsocketConnector):
    url:str="wss://stream.binance.com:9443/ws/stream"
    prefix:str="binance"

    def on_message(self, ws, message, buffer, influx_connector, aggregation_level):
        print("im there")
        obj = json.loads(message)
        print("message", message)
        # if bool(obj['data']) :
        #     price = obj['data']['price']
        #     timestamp = obj['data']['timestamp']
        #     utc_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
        #     current_trade = LiveTrade(utc_timestamp, pair="ETH-EUR" , exchange="Bitstamp", price=price)
        #     buffer.append(current_trade)

        
        # time_difference_buffer = buffer.get_time_difference()
        # if time_difference_buffer > aggregation_level:
        #     buffer_data = buffer.get_data()
        #     if len(buffer_data) == 1:
        #         first_buffer_element = buffer_data[0]
        #         influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                
                
                
        #     if len(buffer_data) > 1:
        #         first_buffer_element = buffer_data[0]
        #         last_buffer_element = buffer_data[len(buffer_data) -1]
        #         influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
        #         influx_connector.write_point(last_buffer_element.to_influx(self.prefix))
                
        #     buffer.reset_data()
    
    def on_open(self, ws):
        def run(*args):
            # request websocket data
            websocket_request_data =  {
            "method": "SUBSCRIBE",
            "params":
            [
            "etheur@trade",
            ],
            "id": 1
            }
            websocket_request_data_json = json.dumps(websocket_request_data)
            ws.send(websocket_request_data_json)
        thread.start_new_thread(run, ())
        time.sleep(0.01)
        print("websocket-connection established.")  




@dataclass
class Buffer:
    data=[]

    def __init__(self):
        self.data=[]
    def append(self, element):
        self.data.append(element)
    def get_data(self):
        return self.data
    def reset_data(self):
        self.data = []
    def get_time_difference(self):
        if len(self.data)==0:
            return 0
        first_element = self.data[0]
        last_element = self.data[len(self.data)-1]
        ts_first_element = first_element.timestamp_utc
        ts_last_element = last_element.timestamp_utc
        return (ts_last_element-ts_first_element).seconds

@dataclass
class InfluxConnector:
    client: InfluxDBClient

    def __init__(self):
        load_dotenv()
        user=os.getenv("INFLUX_DB_USER")
        password=os.getenv("INFLUX_DB_PASSWORD")
        self.client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    
    def get_client(self):
        return self.client

    def write_point(self,influx_point):
        self.client.write_points([influx_point])

