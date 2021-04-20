import json
import websocket
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
try:
    import thread
except ImportError:
    import _thread as thread
import time


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
        ts_firs_element = first_element['timestamp']
        ts_last_element = last_element['timestamp']
        return (ts_last_element-ts_firs_element).seconds




def _start_websocket_connection():
    uri = "wss://ws.bitstamp.net"
    ws = websocket.create_connection(uri)
    print("websocket-connection established.")
    return ws


def _create_influx_connection():
    load_dotenv()
    user=os.getenv("INFLUX_DB_USER")
    password=os.getenv("INFLUX_DB_PASSWORD")
    client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    print("DB-connection established:", client)
    return client


def on_message(ws, message, buffer, influx_client, aggregation_level):
    obj = json.loads(message)
    if bool(obj['data']) :
        price = obj['data']['price']
        timestamp = obj['data']['timestamp']
        utc_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
        buffer.append({'timestamp': utc_timestamp, 'price': price})
    
    time_difference_buffer = buffer.get_time_difference()
    if time_difference_buffer > aggregation_level:
        buffer_data = buffer.get_data()
        if len(buffer_data) == 1:
            first_buffer_element = buffer_data[0]
            start_point = [
                    {
                        "measurement": "ethereum_price",
                        "tags": {
                            "currency": "EUR",
                            "exchange": "Bitstamp"
                        
                        },
                        "time": first_buffer_element['timestamp'],
                        "fields": {
                            "value": first_buffer_element['price']
                        }
                    }
            ]
            influx_client.write_points(start_point)
            
            
        if len(buffer_data) > 1:
            first_buffer_element = buffer_data[0]
            last_buffer_element = buffer_data[len(buffer_data) -1]
            start_point = [
                    {
                        "measurement": "ethereum_price",
                        "tags": {
                            "currency": "EUR",
                            "exchange": "Bitstamp"
                        
                        },
                        "time": first_buffer_element['timestamp'],
                        "fields": {
                            "value": first_buffer_element['price']
                        }
                    }
            ]
            end_point =  [
                    {
                        "measurement": "ethereum_price",
                        "tags": {
                            "currency": "EUR",
                            "exchange": "Bitstamp"
                        
                        },
                        "time": last_buffer_element['timestamp'],
                        "fields": {
                            "value": last_buffer_element['price']
                        }
                    }
            ]
            influx_client.write_points(start_point)
            influx_client.write_points(end_point)
            
        buffer.reset_data()
    

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_ping(wsapp, message):
    print("Got a ping!")

def on_pong(wsapp, message):
    print("Got a pong! No need to respond")

def on_open(ws):
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
    print("websocket-connection established.")


def discover_flowers(aggregation_level=30):
    websocket.enableTrace(True)
    buffer = Buffer()
    influx_client = _create_influx_connection()
    print("aggregation-level [s]:", aggregation_level)
    ws = websocket.WebSocketApp("wss://ws.bitstamp.net",
                              on_open = on_open,
                              on_message = lambda ws,msg: on_message(ws,msg,buffer, influx_client, aggregation_level),
                              on_error = on_error,
                              on_close = on_close,
                              on_ping=on_ping, 
                              on_pong=on_pong)

    ws.run_forever(suppress_origin=True, ping_interval=30, ping_timeout=10)





















  