from dataclasses import dataclass
from datetime import datetime
import json
import os
import threading
import time
from dotenv.main import load_dotenv
import operator

from influxdb.client import InfluxDBClient
import pytz
import websocket
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

    def connect_websocket(self):
        print("url", self.url)
        influx_connector = InfluxConnector()
        buffer = Buffer()
        aggregation_level = 30
        print("aggregation-level [s]:", aggregation_level)
        ws = websocket.WebSocketApp(self.url,
            on_open = lambda ws: self.on_open(ws),
            on_message = lambda ws,msg: self.on_message(ws,msg,buffer, influx_connector, aggregation_level),
            on_error = self.on_error,
            on_close = lambda wsapp, close_status_code, close_msg: self.on_close(wsapp, close_status_code, close_msg),
            on_ping=self.on_ping, 
            on_pong=self.on_pong)

        wst = threading.Thread(target=ws.run_forever())
        wst.daemon = True
        wst.start()


    def on_message():
        pass
    
    def on_open():
        pass
    
    def on_error(ws, error, args):
        print(error)

    def on_ping(wsapp, message):
        print("Got a ping!")

    def on_pong(wsapp, message):
        print("Got a pong! No need to respond")

    def on_close(self, wsapp, close_status_code, close_msg):
        print("close_message", close_msg )
        # print('disconnected from server')
        print ("Retry : %s" % time.ctime())
        time.sleep(10)
        self.connect_websocket() # retry per 10 seconds

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
                
                
            if len(buffer_data) == 2:
                first_buffer_element = buffer_data[0]
                last_buffer_element = buffer_data[len(buffer_data) -1]
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                influx_connector.write_point(last_buffer_element.to_influx(self.prefix))

            if len(buffer_data) >2:
                first_buffer_element = buffer_data[0]
                last_buffer_element = buffer_data[len(buffer_data) -1]
                max_element = max(buffer_data, key=operator.attrgetter('price'))
                min_element = min(buffer_data, key=operator.attrgetter('price'))
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                influx_connector.write_point(max_element.to_influx(self.prefix))
                influx_connector.write_point(min_element.to_influx(self.prefix))
                influx_connector.write_point(last_buffer_element.to_influx(self.prefix))
                
            buffer.reset_data()
    
    def on_open(self, ws):
        print("opening...")
         # request websocket data
        websocket_request_data =  {
            "event": "bts:subscribe",
            "data": {
                "channel": "live_trades_etheur"
            }
        }
        websocket_request_data_json = json.dumps(websocket_request_data)
        ws.send(websocket_request_data_json)
        print("websocket-connection established.")  

@dataclass
class BinanceWebsocketConnector(WebsocketConnector):
    url:str="wss://stream.binance.com:9443/ws/stream"
    prefix:str="binance"

    def on_message(self, ws, message, buffer, influx_connector, aggregation_level):
        obj = json.loads(message)
        if bool(obj['p']) :
            price = obj['p']
            timestamp = obj['T']
            utc_timestamp = datetime.fromtimestamp(timestamp / 1000.0).astimezone(pytz.utc)
            current_trade = LiveTrade(utc_timestamp, pair="ETH-EUR" , exchange="Binance", price=price)
            print(current_trade)
            buffer.append(current_trade)

        
        time_difference_buffer = buffer.get_time_difference()
        if time_difference_buffer > aggregation_level:
            buffer_data = buffer.get_data()
            if len(buffer_data) == 1:
                first_buffer_element = buffer_data[0]
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                
            if len(buffer_data) == 2:
                first_buffer_element = buffer_data[0]
                last_buffer_element = buffer_data[len(buffer_data) -1]
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                influx_connector.write_point(last_buffer_element.to_influx(self.prefix))

            if len(buffer_data) >2:
                first_buffer_element = buffer_data[0]
                last_buffer_element = buffer_data[len(buffer_data) -1]
                max_element = max(buffer_data, key=operator.attrgetter('price'))
                min_element = min(buffer_data, key=operator.attrgetter('price'))
                influx_connector.write_point(first_buffer_element.to_influx(self.prefix))
                influx_connector.write_point(max_element.to_influx(self.prefix))
                influx_connector.write_point(min_element.to_influx(self.prefix))
                influx_connector.write_point(last_buffer_element.to_influx(self.prefix))
            buffer.reset_data()
    
    def on_open(self, ws):
        print("opening...")
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

