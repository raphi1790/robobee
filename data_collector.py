import json
from websocket import create_connection
from influxdb import InfluxDBClient
from datetime import datetime



uri = "wss://ws.bitstamp.net"
ws = create_connection(uri)

data = {
        "event": "bts:subscribe",
        "data": {
            "channel": "live_trades_btcusd"
        }
    }
data_json = json.dumps(data)




client = InfluxDBClient('localhost', 8086, 'root', 'root')
print("client", client)

dbs = client.get_list_database()
print("dbs", dbs)

# ws.send(data_json)
# while True:
#     try:
#         result = ws.recv()
#         obj = json.loads(result)
#         if bool(obj['data']) :
#             price = obj['data']['price']
#             timestamp = obj['data']['timestamp']
#             print("timestamp", datetime.fromtimestamp(int(timestamp)))
#             print("obj", obj)
#             json_body = [
#             {
#                 "measurement": "bitcoin_price",
#                 "tags": {
#                     "currency": "USD",
#                     "exchange": "Bitstamp"
                   
#                 },
#                 "time": datetime.fromtimestamp(int(timestamp)),
#                 "fields": {
#                     "value": price
#                 }
#             }
#             ]
#             # print("json_body",json_body)
#             client.write_points(json_body)
#     except Exception as e:
#         print(e)
#         break