import json
from websocket import create_connection
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz


def start_websocket_connection():
    uri = "wss://ws.bitstamp.net"
    ws = create_connection(uri)
    return ws

def collect_websocket_data(websocket, aggregation_level=30):
    # open connection
    client = InfluxDBClient('localhost', 8086, 'root', 'Gotthard', 'pi_influxdb')

    # request websocket data
    websocket_request_data =  {
        "event": "bts:subscribe",
        "data": {
            "channel": "live_trades_btcusd"
        }
    }
    websocket_request_data_json = json.dumps(websocket_request_data)
    websocket.send(websocket_request_data_json) # start requesting websocket-data


    while True:
        start_time = datetime.now(tz=pytz.utc)
        current_time = start_time
        interval = aggregation_level # aggregate all transactions within the time-interval into one point
        values = []
        while current_time < start_time + timedelta(seconds=interval):
            try:
                result = websocket.recv()
                obj = json.loads(result)

                if bool(obj['data']) :
                    price = obj['data']['price']
                    timestamp = obj['data']['timestamp']
                    localized_timestamp = datetime.fromtimestamp(int(timestamp)).astimezone(pytz.utc)
                    values.append(price)

                    
                current_time = datetime.now(tz=pytz.utc)
            except Exception as e:
                print(e)
                break
        
        average_value = sum(values)/len(values) if len(values) > 0 else 0
        print("values", values)
        print("average_value",average_value )
        print("len(values)", len(values))
        if len(values) > 0:
            single_point = [
                    {
                        "measurement": "bitcoin_price",
                        "tags": {
                            "currency": "USD",
                            "exchange": "Bitstamp"
                        
                        },
                        "time": current_time,
                        "fields": {
                            "value": average_value
                        }
                    }
            ]
            client.write_points(single_point )















  