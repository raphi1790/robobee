import time
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime
from api.api import *

def _get_config_data():
    load_dotenv()
    RESERVE=os.getenv("RESERVE")
    MARGIN=os.getenv("MARGIN")
    FEE=os.getenv("FEE")
    return RESERVE, MARGIN, FEE
    

def _is_plausible(available_eur, available_eth, current_stock_price, reserve, margin, fee):
    is_plausible = False
    print(available_eur)
    print(available_eth)
    print(current_stock_price)
    if not (available_eth is  None or  available_eur is  None or current_stock_price is  None or margin is  None or fee is  None or reserve is  None) :
        is_plausible = True
    return is_plausible

def _calculate_moving_average(values, window_size=3):
    i = 0
    moving_averages = []
    while i < len(values) - window_size + 1:
        this_window = values[i : i + window_size]
        window_average = sum(this_window) / window_size
        moving_averages.append(window_average)
        i += 1
    return moving_averages

def _determine_trend(list_stock_prices):
    moving_averages = _calculate_moving_average(list_stock_prices,5)
    if len(moving_averages)<=10:
        return None
    
    current_value = moving_averages[0]
    is_increasing = True
    is_descreasing = True
    for idx in range(1,len(moving_averages)):
        if current_value < moving_averages[idx]:
            is_descreasing = False
        if current_value > moving_averages[idx]:
            is_increasing = False
        current_value = moving_averages[idx]

    if is_increasing and not is_descreasing:
        return 'increasing'
    if is_descreasing and not is_increasing:
        return 'decreasing'
    return None
    

def _is_buyable(reserve, margin, fee, available_eur,available_eth, current_stock_price, past_stock_prices_1d, past_stock_prices_10m):
    print("past_stock_prices_1d",past_stock_prices_1d)
    print("past_stock_prices_10m",past_stock_prices_10m)
    print("moving_averages",_calculate_moving_average(past_stock_prices_10m,3))
    print("trend",_determine_trend(past_stock_prices_10m))
    return True

def _is_sellable():
    return False

def determine_status():
    RESERVE, FEE, MARGIN  = _get_config_data()
    available_eur, available_eth = get_balance()
    current_stock_price = get_current_eth_eur_value()
    past_stock_prices_1d = get_eth_eur_values()
    past_stock_prices_10m = get_eth_eur_values(interval_str='10m')
    last_selling_price = get_last_transaction_price('sell')
    last_buying_price = get_last_transaction_price('buy')
    is_plausible = _is_plausible(available_eur, available_eth, current_stock_price, RESERVE, FEE, MARGIN)
    is_buyable = _is_buyable(RESERVE, MARGIN, FEE, available_eur,available_eth, current_stock_price, past_stock_prices_1d, past_stock_prices_10m)
    is_sellable = _is_sellable()
    print("is_plausible",is_plausible)

    if is_plausible and is_buyable:
        return 'buy'
    
    if is_plausible and is_sellable:
        return 'sell'
    
    return None

