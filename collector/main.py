from influxdb import InfluxDBClient
from data_collector import looking_for_flowers

if __name__ == "__main__":
    # collect live-trades using websocket
    looking_for_flowers( aggregation_level=30)
