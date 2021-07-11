from dataclasses import dataclass
from datetime import datetime


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
                            "price": self.price 
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

