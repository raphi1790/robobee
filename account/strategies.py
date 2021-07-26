from dataclasses import dataclass
from models import Strategy
import api.api as api
from helper import *

@dataclass
class SslChannelEmaStrategy(Strategy):
    name:str = "ssl_channel_ema_strategy"

    def calculate_current_trend(self) :
        live_trades= api.get_eth_eur_values(from_dt_str="now()-15d")
        candlestick_5m = create_candlesticks(live_trades)
        candlestick_5m = candlestick_5m.set_index('timestamp_utc')
        candlestick_1h = create_candlesticks(live_trades, interval='1H')
        candlestick_1h = candlestick_1h.set_index('timestamp_utc')

        return  candlestick_5m, candlestick_1h
    
    def buy_sell_option(self):
        pass
