import json
import websocket
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
from models import  LiveTrade, Buffer, InfluxConnector

try:
    import thread
except ImportError:
    import _thread as thread
import time





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


def on_message(ws, message, buffer, influx_connector, aggregation_level):
    obj = json.loads(message)
    if bool(obj['data']) :
        price = obj['data']['price']
        timestamp = obj['data']['timestamp']
        utc_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
        current_trade = LiveTrade(utc_timestamp, pair="ETH-EUR", exchange="Bitstamp", price=price)
        buffer.append(current_trade)

    
    time_difference_buffer = buffer.get_time_difference()
    if time_difference_buffer > aggregation_level:
        buffer_data = buffer.get_data()
        if len(buffer_data) == 1:
            first_buffer_element = buffer_data[0]
            influx_connector.write_point(first_buffer_element.to_influx())
            
            
            
        if len(buffer_data) > 1:
            first_buffer_element = buffer_data[0]
            last_buffer_element = buffer_data[len(buffer_data) -1]
            influx_connector.write_point(first_buffer_element.to_influx())
            influx_connector.write_point(last_buffer_element.to_influx())
            
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
    time.sleep(0.01)
    print("websocket-connection established.")


def discover_flowers(aggregation_level=30):
    websocket.enableTrace(True)
    buffer = Buffer()
    influx_connector = InfluxConnector()
    print("aggregation-level [s]:", aggregation_level)
    ws = websocket.WebSocketApp("wss://ws.bitstamp.net",
                              on_open = on_open,
                              on_message = lambda ws,msg: on_message(ws,msg,buffer, influx_connector, aggregation_level),
                              on_error = on_error,
                              on_close = on_close,
                              on_ping=on_ping, 
                              on_pong=on_pong)

    ws.run_forever(suppress_origin=True, ping_interval=30, ping_timeout=10)





















  