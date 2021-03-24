import json
import websocket
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv




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




def discover_flowers(aggregation_level=30):
    ws = _start_websocket_connection()

    # open db-connection
    influx_client = _create_influx_connection()

    # request websocket data
    websocket_request_data =  {
        "event": "bts:subscribe",
        "data": {
            "channel": "live_trades_etheur"
        }
    }
    websocket_request_data_json = json.dumps(websocket_request_data)
    ws.send(websocket_request_data_json ) # start requesting websocket-data  
    print("channel subscribed.")


    print("aggregation-level [s]:", aggregation_level)
    print("start collecting data...")
    while True:
        start_time = datetime.now(tz=pytz.utc)
        current_time = start_time
        interval = aggregation_level # aggregate all transactions within the time-interval into one point
        buffer = []
        while current_time < start_time + timedelta(seconds=interval):
            try: 
                result = ws.recv()
                obj = json.loads(result)
                # print("obj", obj)

                if bool(obj['data']) :
                    price = obj['data']['price']
                    timestamp = obj['data']['timestamp']
                    utc_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
                    buffer.append({'timestamp': utc_timestamp, 'price': price})

                    
                current_time = datetime.now(tz=pytz.utc)
            except Exception as e:
                print(e)
                break
               
        
        if len(buffer) >= 2:
            first_buffer_element = buffer[0]
            last_buffer_element = buffer[len(buffer) -1]
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
        
        if len(buffer) == 1:
            first_buffer_element = buffer[0]
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



















  