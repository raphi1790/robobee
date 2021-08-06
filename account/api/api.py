import hashlib
import hmac
import time
import requests
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
import ast
from urllib.parse import urlencode
from datetime import datetime
from models import InfluxConnector, LiveTrade
import json



def get_eth_eur_values(from_dt_str='now() - 1d',to_dt_str='now()', measurement='live_trades' ):
    influx_connector = InfluxConnector()
    client = influx_connector.get_client()
    print("influx_client", client)
    query_str = f"SELECT time, exchange, pair, price FROM {measurement} WHERE time >= {from_dt_str} and time <= {to_dt_str} order by time desc"
    result_set = client.query(query_str)
    if len(result_set) > 0:
        result_points = list(result_set.get_points(f"{measurement}"))
        print("type(result_points[idx])", type(result_points[0]))

        # Reverse order such that most recent stock_price is at idx = lenght - 1
        return [LiveTrade(result_points[idx]['time'], result_points[idx]['pair'],
                         result_points[idx]['exchange'], 
                         result_points[idx]['price']) 
                    for idx in reversed(range(len(result_points)))]
    else:
        return None

def get_current_eth_eur_value():
    live_trades = get_eth_eur_values(from_dt_str='now() - 2m', to_dt_str='now()',measurement='live_trades')
    if len(live_trades)>0:
        return live_trades[-1]
    else:
        return None


    
