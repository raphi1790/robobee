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

def calculate_simple_moving_average(df, lookback, column ):
    df['sma_'+column+'_'+str(lookback)] = df.loc[:,column].rolling(window=lookback).mean()
    return df

    
