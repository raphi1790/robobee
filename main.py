from influxdb import InfluxDBClient
from data_collector import start_websocket_connection, collect_websocket_data

if __name__ == "__main__":
    ws = start_websocket_connection()
    collect_websocket_data(ws, aggregation_level=30)


# client = InfluxDBClient('localhost', 8086, 'root', 'Gotthard', "pi_influxdb")
# print("client", client)

# dbs = client.get_list_database()
# print("dbs", dbs)

# results = client.query('SHOW RETENTION POLICIES')

# print("results", results)