import time
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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

    
