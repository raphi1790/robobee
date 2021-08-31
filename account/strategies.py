from dataclasses import dataclass
from models import AccountConnector, Strategy, Transaction
import api.api as api
from helper import *
import talib


# @dataclass
# class SslChannelEmaStrategy(Strategy):
#     name:str = "ssl_channel_ema_strategy"

#     def calculate_current_trend(self) :
#         live_trades= api.get_eth_eur_values(from_dt_str="now()-15d")
#         candlestick_5m = create_candlesticks(live_trades)
#         candlestick_5m = candlestick_5m.set_index('timestamp_utc')
#         candlestick_1h = create_candlesticks(live_trades, interval='1H')
#         candlestick_1h = candlestick_1h.set_index('timestamp_utc')

#         return  candlestick_5m, candlestick_1h
    
#     def buy_sell_option(self):
#         pass


@dataclass
class SimpleStrategy(Strategy):
    name:str = "simple_strategy"

    def _collect_data():
        live_trades= api.get_eth_eur_values(from_dt_str="now()-1d")
        candlestick_5m = create_candlesticks(live_trades, interval='5Min')
        candlestick_5m['engulfing'] = talib.CDLENGULFING(candlestick_5m['open'],candlestick_5m['high'], candlestick_5m['low'], candlestick_5m['close'])
        candlestick_5m['ema_10'] = talib.EMA( candlestick_5m['close'],10)
        candlestick_5m['ema_20'] = talib.EMA( candlestick_5m['close'],20)
        print("ema_10:",candlestick_5m[-2:-1]['ema_10'].values[0],"ema_20:",candlestick_5m[-2:-1]['ema_20'].values[0])
        return candlestick_5m

    def _get_trend_long():
        pass
    
    def _get_current_status(last_transaction: Transaction):   
        if last_transaction.type == 'buy':
            return 'in'
        else:
            return 'out'
    
    def _is_bullish_engulfing_pattern(df):
        """
        second last candle must be bullish
        """
        last_relevant_record = df[-2:-1]
        predecessor_record = df[-3:-2]

        length_predecessor_candle = abs(predecessor_record['open'].values[0]-predecessor_record['close'].values[0])
    
        if (len(last_relevant_record.loc[last_relevant_record['engulfing']>0])>0):
            return True
        else:
            return False

    def _is_bullish_trend(df):
        last_relevant_record = df[-2:-1]
        if last_relevant_record['ema_10'].values[0]>last_relevant_record['ema_20'].values[0]:
            return True
        else:
            return False

    def _entry_signal(df):
        if SimpleStrategy._is_bullish_engulfing_pattern(df) and SimpleStrategy._is_bullish_trend(df):
            return True
        else: 
            return False

    def _take_profit(df):
        last_relevant_record = df[-2:-1]
        if (last_relevant_record['ema_20'].values[0] > last_relevant_record['ema_10'].values[0]):
            return True
        else:
            False
    
    def _stop_loss(df, last_transaction:Transaction ):
        last_relevant_record = df[-2:-1]
        if last_transaction.price > last_relevant_record['close'].values[0]*1.0025:
            return True
        else:
            False

    
    def apply(self, connector: AccountConnector):
        data = SimpleStrategy._collect_data()
        current_eth_eur_value = getattr(api.get_current_eth_eur_value(),'price')
        print("current eth-eur-value:", current_eth_eur_value)
        last_transaction = connector.get_last_transaction()
        status = SimpleStrategy._get_current_status(last_transaction)

        if status == 'in':
            print("in-trade")
            if SimpleStrategy._take_profit(data):
                print("take-profit")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            elif SimpleStrategy._stop_loss(data, last_transaction):
                print("stop-loss")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            else: 
                pass 
        if status == 'out':
            print("out-trade")
            if SimpleStrategy._entry_signal(data):
                print("enter trade")
                print("ema_10:", data[-3:-2]['ema_10'], "ema_20:", data[-3:-2]['ema_20'])
                eth_to_buy = calculate_eth(connector.tradeable_eur(),current_eth_eur_value)
                connector.buy_eth(eth_to_buy, current_eth_eur_value)
        
        return data
        
