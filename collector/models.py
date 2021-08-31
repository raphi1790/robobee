from dataclasses import dataclass
from datetime import datetime
import os
from dotenv.main import load_dotenv

from influxdb.client import InfluxDBClient


@dataclass
class LiveTrade:
    timestamp_utc: datetime
    pair: str
    exchange: str
    price: float

    def to_influx(self):
        return {
                        "measurement": "live_trades",
                        "tags": {
                            "pair": self.pair,
                            "exchange": self.exchange
                        
                        },
                        "time": str(self.timestamp_utc),
                        "fields": {
                            "price": float(self.price) 
                        }
                    }

@dataclass
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
        ts_first_element = first_element.timestamp_utc
        ts_last_element = last_element.timestamp_utc
        return (ts_last_element-ts_first_element).seconds

@dataclass
class InfluxConnector:
    client: InfluxDBClient

    def __init__(self):
        load_dotenv()
        user=os.getenv("INFLUX_DB_USER")
        password=os.getenv("INFLUX_DB_PASSWORD")
        self.client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    
    def get_client(self):
        return self.client

    def write_point(self,influx_point):
        self.client.write_points([influx_point])

