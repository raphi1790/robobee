from dataclasses import dataclass
from datetime import datetime

@dataclass
class LiveTrade:
    timestamp_utc: datetime
    pair: str
    exchange: str
    price: float

    def to_dict(self):
        return {'timestamp_utc': self.timestamp_utc,
                'pair': self.pair,
                'exchange': self.exchange,
                'price': self.price}

@dataclass
class Candlestick:
    open_timestamp_utc: datetime
    close_timestamp_utc: datetime
    interval_length_m: int
    open: float
    close: float
    high: float
    low: float

