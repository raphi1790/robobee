import json
import websocket
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
from models import  LiveTrade, Buffer, InfluxConnector, BitstampWebsocketConnector, BinanceWebsocketConnector

try:
    import thread
except ImportError:
    import _thread as thread
import time



# def _start_websocket_connection():
#     uri = "wss://ws.bitstamp.net"
#     ws = websocket.create_connection(uri)
#     print("websocket-connection established.")
#     return ws


# def _create_influx_connection():
#     load_dotenv()
#     user=os.getenv("INFLUX_DB_USER")
#     password=os.getenv("INFLUX_DB_PASSWORD")
#     client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
#     print("DB-connection established:", client)
#     return client
#    

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_ping(wsapp, message):
    print("Got a ping!")

def on_pong(wsapp, message):
    print("Got a pong! No need to respond")


def discover_flowers(aggregation_level=30):
    connector = BinanceWebsocketConnector()
    print("url", connector.url)
    websocket.enableTrace(True)
    buffer = Buffer()
    influx_connector = InfluxConnector()
    print("aggregation-level [s]:", aggregation_level)
    ws = websocket.WebSocketApp(connector.url,
                              on_open = lambda ws: connector.on_open(ws),
                              on_message = lambda ws,msg: connector.on_message(ws,msg,buffer, influx_connector, aggregation_level),
                              on_error = on_error,
                              on_close = on_close,
                              on_ping=on_ping, 
                              on_pong=on_pong)

    ws.run_forever(suppress_origin=True, ping_interval=30, ping_timeout=10)





















  