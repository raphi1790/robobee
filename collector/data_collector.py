from models import WebsocketConnector
import websocket
from dotenv import load_dotenv
from models import  LiveTrade, Buffer, InfluxConnector


def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_ping(wsapp, message):
    print("Got a ping!")

def on_pong(wsapp, message):
    print("Got a pong! No need to respond")


def discover_flowers(websocket_connector:WebsocketConnector, aggregation_level=30):
    websocket.enableTrace(True)
    buffer = Buffer()
    influx_connector = InfluxConnector()
    print("aggregation-level [s]:", aggregation_level)
    ws = websocket.WebSocketApp(websocket_connector.url,
                              on_open = lambda ws: websocket_connector.on_open(ws),
                              on_message = lambda ws,msg: websocket_connector.on_message(ws,msg,buffer, influx_connector, aggregation_level),
                              on_error = on_error,
                              on_close = on_close,
                              on_ping=on_ping, 
                              on_pong=on_pong)

    ws.run_forever(suppress_origin=True, ping_interval=30, ping_timeout=10)





















  