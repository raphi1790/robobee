import time
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def create_candlesticks(live_trades, interval='5Min'):
    df = pd.DataFrame.from_records([s.to_dict() for s in live_trades])
    time_grouper = interval
    df = df.set_index('timestamp_utc')
    df.index = pd.to_datetime(df.index)

    openings = df.groupby(pd.Grouper(freq=time_grouper))['price'].nth([0]).reset_index().rename(columns={'price': 'open'})
    closings = df.groupby(pd.Grouper(freq=time_grouper))['price'].nth([-1]).reset_index().rename(columns={'price': 'close'})
    candlestick_df = df.groupby(pd.Grouper(freq=time_grouper))['price'].agg(
        low=np.min, high=np.max ).reset_index()
    candlestick_df = candlestick_df.merge(openings, on='timestamp_utc' ).merge(closings, on='timestamp_utc')

    return candlestick_df


def plot_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(x=df['timestamp_utc'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'])
                     ])

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()

def add_simple_moving_average_to_df(df, lookback, column ):
    df['sma_'+column+'_'+str(lookback)] = df.loc[:,column].rolling(window=lookback).mean()
    return df

def calculate_ssl_channel(df, lookback_highs, lookback_lows):
    df = add_simple_moving_average_to_df(df, lookback_highs, 'high' )
    df = add_simple_moving_average_to_df(df, lookback_lows, 'low' )
    df['hlv']=df.apply(lambda row: 1 if row['close']>row['sma_'+'high'+'_'+str(lookback_highs)] 
                        else -1 if row['close']<row['sma_'+'low'+'_'+str(lookback_highs)] else 0 ,axis=1  )
    df['hlv_prev'] =df['hlv'].shift()
    df['hlv'] = df.apply(lambda row: row['hlv_prev'] if row['hlv']==0 else row['hlv'], axis=1)
    df.drop(columns=['hlv_prev'],inplace=True)
    df['ssl_down'] = df.apply(lambda row: row['sma_'+'high'+'_'+str(lookback_highs)] if row['hlv'] < 0 
                        else row['sma_'+'low'+'_'+str(lookback_lows)] , axis=1)
    df['ssl_up'] = df.apply(lambda row: row['sma_'+'low'+'_'+str(lookback_lows)] if row['hlv'] < 0 
                    else row['sma_'+'high'+'_'+str(lookback_highs)] , axis=1)
    
    df['trend'] = df.apply(lambda row: 'up' if row['ssl_up'] > row['ssl_down'] else 'down' if row['ssl_down'] > row['ssl_up'] else 'none')

    return df
 
