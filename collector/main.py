from influxdb import InfluxDBClient
from data_collector import start_websocket_connection, collect_websocket_data

if __name__ == "__main__":
    ws = start_websocket_connection()
    collect_websocket_data(ws, aggregation_level=60)
