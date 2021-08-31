from dataclasses import dataclass
from models import Indicator
import pandas as pd

@dataclass
class SslChannel(Indicator):
    name: str = "ssl_channel"
    lookback_highs: int = 10
    lookback_lows: int = 10

    def apply_indicator(self,candlestick_df) -> pd.DataFrame:
        candlestick_df = self.add_simple_moving_average_to_df(candlestick_df, self.lookback_highs, 'high' )
        candlestick_df = self.add_simple_moving_average_to_df(candlestick_df, self.lookback_lows, 'low' )
        candlestick_df[self.name +'_hlv']=candlestick_df.apply(lambda row: 1 if row['close']>row['sma_'+'high'+'_'+str(self.lookback_highs)] 
                            else -1 if row['close']<row['sma_'+'low'+'_'+str(self.lookback_highs)] else 0 ,axis=1  )
        candlestick_df[self.name+'_hlv_prev'] =candlestick_df[self.name+'_hlv'].shift()
        candlestick_df[self.name +'_hlv'] = candlestick_df.apply(lambda row: row[self.name+'_hlv_prev'] if row[self.name+"_"+'hlv']==0 else row[self.name+"_"+ 'hlv'], axis=1)
        candlestick_df.drop(columns=[self.name+'_hlv_prev'],inplace=True)
        candlestick_df[self.name +'_ssl_down'] = candlestick_df.apply(lambda row: row['sma_'+'high'+'_'+str(self.lookback_highs)] if row[self.name+"_"+'hlv'] < 0 
                            else row['sma_'+'low'+'_'+str(self.lookback_lows)] , axis=1)
        candlestick_df[self.name +'_ssl_up'] = candlestick_df.apply(lambda row: row['sma_'+'low'+'_'+str(self.lookback_lows)] if row[self.name+"_"+'hlv'] < 0 
                        else row['sma_'+'high'+'_'+str(self.lookback_highs)] , axis=1)
        
        candlestick_df[self.name+'_trend'] = candlestick_df.apply(lambda row: 1 if row[self.name+"_"+'ssl_up'] > row[self.name+"_"+'ssl_down'] else -1 if row[self.name+"_"+'ssl_down'] > row[self.name+"_"+'ssl_up'] else 0, axis=1)

        return candlestick_df

@dataclass
class ExponentialMovingAverage(Indicator):
    name: str = "ema"
    lookback: int = 10

    def apply_indicator(self,candlestick_df) -> pd.DataFrame:
        candlestick_df[self.name+'_'+str(self.lookback)] = pd.Series.ewm(candlestick_df['close'], span=self.lookback).mean()
        return candlestick_df