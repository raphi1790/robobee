from dataclasses import dataclass
from math import inf
from models import AccountConnector, Strategy, Transaction
import api.api as api
from helper import *
import talib
import pandas as pd
import numpy as np


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
        live_trades= api.get_eth_eur_values(from_dt_str="now()- 1d")
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
        last_relevant_records = df[-4:-1]


        if (len(last_relevant_records.loc[last_relevant_records['engulfing']>0])>0):
            return True
        else:
            return False

    def _bullish_trend_just_started(df):
        last_relevant_record = df[-2:-1]
        intersection_record = df[-5:-4]
        if (last_relevant_record['ema_10'].values[0]>last_relevant_record['ema_20'].values[0] and
               intersection_record['ema_20'].values[0]>intersection_record['ema_10'].values[0] ):
            return True
        else:
            return False

    def _entry_signal(df):
        if SimpleStrategy._is_bullish_engulfing_pattern(df) and SimpleStrategy._bullish_trend_just_started(df):
            return True
        else: 
            return False

    def _take_profit(df):
        last_relevant_record = df[-2:-1]
        if (last_relevant_record['ema_20'].values[0] > last_relevant_record['ema_10'].values[0]):
            return True
        else:
            False
    
    def _stop_loss(df, lower_bound ):
        last_relevant_record = df[-2:-1]
        if lower_bound > last_relevant_record['close'].values[0]:
            return True
        else:
            False

    
    def apply(self, connector: AccountConnector, live_trades_connector_name):
        lower_bound = float(-inf)
        data = SimpleStrategy._collect_data()
        last_relevant_record = data[-2:-1]
        last_relevant_close_value = last_relevant_record['close'].values[0]
        current_eth_eur_value = getattr(api.get_current_eth_eur_value(live_trades_connector_name),'price')
        print("current eth-eur-value:", current_eth_eur_value)
        last_transaction = connector.get_last_transaction()
        status = SimpleStrategy._get_current_status(last_transaction)
        print("last relevant close-value", last_relevant_close_value)
        print("last bullish engulfing pattern", data.loc[data['engulfing']>0])
        if status == 'in':
            print("in-trade")
            lower_bound = last_transaction.price/1.0025
            print("lower_bound", lower_bound)
            # if current_eth_eur_value > last_transaction.price/1.0025 and current_eth_eur_value > lower_bound:
            #     lower_bound = current_eth_eur_value
            # print("lower_bound", lower_bound)
            if SimpleStrategy._take_profit(data):
                print("take-profit")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            elif SimpleStrategy._stop_loss(data, lower_bound):
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
                print("ema_10:", data[-3:-2]['ema_10'].values[0], "ema_20:", data[-3:-2]['ema_20'].values[0])
                eth_to_buy = calculate_eth(connector.tradeable_eur(),current_eth_eur_value)
                connector.buy_eth(eth_to_buy, current_eth_eur_value)
        
        return data

@dataclass
class EmaStrategy(Strategy):
    name:str = "3_6_9_strategy"

    def _collect_data(self):
        live_trades= api.get_eth_eur_values(from_dt_str="now()- 1d", measurement='binance_live_trades' )
        candlestick_5m = create_candlesticks(live_trades, interval='5Min')
        candlestick_5m['engulfing'] = talib.CDLENGULFING(candlestick_5m['open'],candlestick_5m['high'], candlestick_5m['low'], candlestick_5m['close'])
        candlestick_5m['ema_3'] = talib.EMA( candlestick_5m['close'],3)
        candlestick_5m['ema_6'] = talib.EMA( candlestick_5m['close'],6)
        candlestick_5m['ema_9'] = talib.EMA( candlestick_5m['close'],9)
        candlestick_5m['sma_21'] = talib.SMA( candlestick_5m['close'],21)
        candlestick_5m['sma_50'] = talib.SMA( candlestick_5m['close'],50)
        candlestick_5m['sma_100'] = talib.SMA( candlestick_5m['close'],100)
        return candlestick_5m


    def _data_validation_successful(self, candlestick_5m):
        offset_index=70
        tolerance=10
        candlestick_5m['validation_time_utc'] = candlestick_5m.index - pd.DateOffset(minutes=offset_index*5)
        latest_record=candlestick_5m[-2:-1]
        validation_record=candlestick_5m[(-2-(offset_index-tolerance)):(-1-(offset_index-tolerance))]
        boolean_array=validation_record.index >= latest_record['validation_time_utc']
        if boolean_array[0]:
            return True
        else:
            return False


    def _get_current_status(self, last_transaction: Transaction):   
        if last_transaction.type == 'buy':
            return 'in'
        else:
            return 'out'

    def _calculate_trendline(self,data, order=1):
        index = range(len(data))
        coeffs = np.polyfit(index, list(data), order)
        slope = coeffs[-2]
        return float(slope)
        
    def _is_up_trend(self, df):
        last_record = df[-2:-1]
        trend_records = df[-5:-1]
        trend_sma_21 = self._calculate_trendline(trend_records['sma_21'].values)
        print("current slope sma_21",  trend_sma_21)
        # trend_sma_50 = self._calculate_trendline(trend_records['sma_50'].values)
        # trend_sma_100 = self._calculate_trendline(trend_records['sma_100'].values)
        if (last_record['sma_21'].values[0]>last_record['sma_50'].values[0] and 
            last_record['sma_50'].values[0]>last_record['sma_100'].values[0] and 
            trend_sma_21 >= 0.1 
            ):
            return True
        else:
            return False

    
    def _short_term_up_trend_started(self, df):
        last_relevant_record = df[-2:-1]
        intersection_record = df[-3:-2]

        if (last_relevant_record['ema_3'].values[0]>last_relevant_record['ema_6'].values[0] and 
            last_relevant_record['ema_3'].values[0]>last_relevant_record['ema_9'].values[0] and 
            (intersection_record['ema_3'].values[0]<intersection_record['ema_6'].values[0] or
               intersection_record['ema_3'].values[0]<intersection_record['ema_9'].values[0] ) ):
            return True
        else:
            return False

    def _entry_signal(self, df, is_up_trend):
        if self._short_term_up_trend_started(df) and is_up_trend:
            return True
        else: 
            return False

    def _take_profit(self,df, upper_bound, current_eth_eur_value):
        last_relevant_record = df[-2:-1]
        trend_records = df[-4:-1]
        trend_ema_3 = self._calculate_trendline(trend_records['ema_3'].values)
        print("trend data ema_3", trend_records['ema_3'].values)
        print("slope ema_3", trend_ema_3)
        if (current_eth_eur_value > upper_bound and  (
        (last_relevant_record['ema_3'].values[0]< last_relevant_record['ema_6'].values[0]
        or last_relevant_record['ema_3'].values[0] < last_relevant_record['ema_9'].values[0])
        or trend_ema_3 < 0.1 )): 
            return True
        else:
            False
    
    def _stop_loss(self,df, lower_bound, current_eth_eur_value ):
        last_relevant_record = df[-2:-1]
        if (lower_bound > last_relevant_record['close'].values[0] and 
            current_eth_eur_value < lower_bound):
            return True
        else:
            False

    
    def apply(self, connector: AccountConnector, live_trades_connector_name):
        lower_bound = float(-inf)
        data = self._collect_data()
        last_relevant_record = data[-2:-1]
        last_relevant_close_value = last_relevant_record['close'].values[0]
        current_eth_eur_value = getattr(api.get_current_eth_eur_value(connector=live_trades_connector_name),'price')
        print("current eth-eur-value:", current_eth_eur_value)
        last_transaction = connector.get_last_transaction()
        status = self._get_current_status(last_transaction)
        print("last relevant close-value", last_relevant_close_value)
        print( data.index[-3], "ema_3:",data[-3:-2]['ema_3'].values[0],"ema_6:",data[-3:-2]['ema_6'].values[0],"ema_9:",data[-3:-2]['ema_9'].values[0])
        print( data.index[-2], "ema_3:",data[-2:-1]['ema_3'].values[0],"ema_6:",data[-2:-1]['ema_6'].values[0],"ema_9:",data[-2:-1]['ema_9'].values[0])
        print( data.index[-2], "sma_21:",data[-2:-1]['sma_21'].values[0],"sma_50:",data[-2:-1]['sma_50'].values[0],"sma_100:",data[-2:-1]['sma_100'].values[0])
        is_up_trend = self._is_up_trend(data)
        print("is_up_trend", is_up_trend)
        data_validation_successful = self._data_validation_successful(data)
        print("data_validation_successful", data_validation_successful)
        if status == 'in':
            print("in-trade")
            lower_bound = last_transaction.price/1.004
            upper_bound = last_transaction.price*1.003
            print("lower_bound", lower_bound)
            print("upper_bound", upper_bound)
            # if current_eth_eur_value > last_transaction.price/1.0025 and current_eth_eur_value > lower_bound:
            #     lower_bound = current_eth_eur_value
            if self._take_profit(data, upper_bound, current_eth_eur_value):
                print("take-profit")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            elif self._stop_loss(data, lower_bound, current_eth_eur_value):
                print("stop-loss")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            else: 
                pass 
        if status == 'out':
            print("out-trade")
            if self._entry_signal(data, is_up_trend) and data_validation_successful:
                print("enter trade")
                eth_to_buy = calculate_eth(connector.tradeable_eur(),current_eth_eur_value)
                connector.buy_eth(eth_to_buy, current_eth_eur_value)
        
        return data


@dataclass
class NoLossStrategy(Strategy):
    name:str = "no_loss_strategy"

    def _collect_data(self):
        live_trades= api.get_eth_eur_values(from_dt_str="now()- 3d", measurement='binance_live_trades' )
        candlestick_5m = create_candlesticks(live_trades, interval='5Min')
        candlestick_5m['engulfing'] = talib.CDLENGULFING(candlestick_5m['open'],candlestick_5m['high'], candlestick_5m['low'], candlestick_5m['close'])
        candlestick_5m['ema_3'] = talib.EMA( candlestick_5m['close'],3)
        candlestick_5m['ema_6'] = talib.EMA( candlestick_5m['close'],6)
        candlestick_5m['ema_9'] = talib.EMA( candlestick_5m['close'],9)
        candlestick_5m['sma_21'] = talib.SMA( candlestick_5m['close'],21)
        candlestick_5m['sma_50'] = talib.SMA( candlestick_5m['close'],50)
        candlestick_5m['sma_100'] = talib.SMA( candlestick_5m['close'],100)
        return candlestick_5m


    def _data_validation_successful(self, candlestick_5m):
        offset_index=90
        tolerance=10
        candlestick_5m['validation_time_utc'] = candlestick_5m.index - pd.DateOffset(minutes=offset_index*5)
        latest_record=candlestick_5m[-2:-1]
        validation_record=candlestick_5m[(-2-(offset_index-tolerance)):(-1-(offset_index-tolerance))]
        boolean_array=validation_record.index >= latest_record['validation_time_utc']
        if boolean_array[0]:
            return True
        else:
            return False

    
    def _get_current_status(self, last_transaction: Transaction):   
        if last_transaction.type == 'buy':
            return 'in'
        else:
            return 'out'

    def _calculate_trendline(self,data, order=1):
        index = range(len(data))
        coeffs = np.polyfit(index, list(data), order)
        slope = coeffs[-2]
        return float(slope)
    

    def _is_down_trend_long(self, df):
        last_record = df[-2:-1]
        trend_records = df[-5:-1]
        trend_sma_21 = self._calculate_trendline(trend_records['sma_21'].values)
        print("current slope sma_21",  trend_sma_21)
        # trend_sma_50 = self._calculate_trendline(trend_records['sma_50'].values)
        # trend_sma_100 = self._calculate_trendline(trend_records['sma_100'].values)
        if (last_record['sma_21'].values[0]<last_record['sma_50'].values[0] and 
            last_record['sma_50'].values[0]<last_record['sma_100'].values[0] and 
            trend_sma_21 < 0.1 
            ):
            return True
        else:
            return False

    def _is_down_trend_short(self, df):
        last_record = df[-2:-1]
        trend_records = df[-5:-1]
        trend_ema_3 = self._calculate_trendline(trend_records['ema_3'].values)
        print("current slope ema_3",  trend_ema_3)
        if (last_record['ema_3'].values[0]<last_record['ema_6'].values[0] and 
            last_record['ema_6'].values[0]<last_record['ema_9'].values[0] and 
            trend_ema_3 < 0.1 
            ):
            return True
        else:
            return False

    def _below_higher_highs(self, df,current_eth_eur_value):
        last_relevant_record = df[-2:-1]
        close_values_1d = df['close'].values
        highest_high = max(close_values_1d)
        print("highest_high", highest_high)
        lower_threshold = highest_high/1.02
        print("lower entry-threshold", lower_threshold)
        if (lower_threshold >= last_relevant_record['close'].values[0] and 
            lower_threshold >= current_eth_eur_value):
            return True
        else:
            return False

    def _entry_signal(self, df, current_eth_eur_value, is_down_trend_long, is_down_trend_short):
        if (self._below_higher_highs(df, current_eth_eur_value) and not is_down_trend_long and not is_down_trend_short ):
            return True
        else: 
            return False

    def _take_profit(self,df, upper_bound, current_eth_eur_value):
        last_relevant_record = df[-2:-1]
        trend_records = df[-4:-1]
        trend_ema_3 = self._calculate_trendline(trend_records['ema_3'].values)
        print("trend data ema_3", trend_records['ema_3'].values)
        print("slope ema_3", trend_ema_3)
        if (current_eth_eur_value > upper_bound and  (
        (last_relevant_record['ema_3'].values[0]< last_relevant_record['ema_6'].values[0]
        or last_relevant_record['ema_3'].values[0] < last_relevant_record['ema_9'].values[0])
        or trend_ema_3 < 0.1 )): 
            return True
        else:
            False
    
    def _stop_loss(self, df ):
        # no stop loss
        return False

    
    def apply(self, connector: AccountConnector, live_trades_connector_name):
        lower_bound = float(-inf)
        data = self._collect_data()
        data_validation_successful = self._data_validation_successful(data)
        print("data_validation_successful", data_validation_successful)
        last_relevant_record = data[-2:-1]
        last_relevant_close_value = last_relevant_record['close'].values[0]
        print("last close-value", last_relevant_close_value )
        current_eth_eur_value = getattr(api.get_current_eth_eur_value(connector=live_trades_connector_name),'price')
        print("current eth-eur-value:", current_eth_eur_value)
        last_transaction = connector.get_last_transaction()
        status = self._get_current_status(last_transaction)
        print("last relevant close-value", last_relevant_close_value)
        print( data.index[-3], "ema_3:",data[-3:-2]['ema_3'].values[0],"ema_6:",data[-3:-2]['ema_6'].values[0],"ema_9:",data[-3:-2]['ema_9'].values[0])
        print( data.index[-2], "ema_3:",data[-2:-1]['ema_3'].values[0],"ema_6:",data[-2:-1]['ema_6'].values[0],"ema_9:",data[-2:-1]['ema_9'].values[0])
        print( data.index[-2], "sma_21:",data[-2:-1]['sma_21'].values[0],"sma_50:",data[-2:-1]['sma_50'].values[0],"sma_100:",data[-2:-1]['sma_100'].values[0])
        is_down_trend_long = self._is_down_trend_long(data)
        is_down_trend_short = self._is_down_trend_short(data)
        print("is_down_trend_long", is_down_trend_long)
        print("is_down_trend_short", is_down_trend_short)
        if status == 'in':
            print("in-trade")
            upper_bound = last_transaction.price*1.004
            print("buying price", last_transaction.price)
            print("upper_bound", upper_bound)
            # if current_eth_eur_value > last_transaction.price/1.0025 and current_eth_eur_value > lower_bound:
            #     lower_bound = current_eth_eur_value
            if self._take_profit(data, upper_bound, current_eth_eur_value):
                print("take-profit")
                print("last buying price:",last_transaction.price, ",current eth-eur-value:",current_eth_eur_value)
                tradeable_eth = connector.tradeable_eth()
                connector.sell_eth(tradeable_eth, current_eth_eur_value)
            elif self._stop_loss(data):
                # This case will never happen, since we don't use any stop-loss in this strategy
                pass
            else: 
                pass 
        if status == 'out':
            print("out-trade")
            if self._entry_signal(data,current_eth_eur_value, is_down_trend_long, is_down_trend_short ) and data_validation_successful:
                print("enter trade")
                eth_to_buy = calculate_eth(connector.tradeable_eur(),current_eth_eur_value)
                connector.buy_eth(eth_to_buy, current_eth_eur_value)
        
        return data
