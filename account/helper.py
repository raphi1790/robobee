import time
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime, timedelta


def get_config_data():
    load_dotenv()
    RESERVE=os.getenv("RESERVE")
    BUYING_MARGIN=os.getenv("BUYING_MARGIN")
    SELLING_MARGIN=os.getenv("SELLING_MARGIN")
    FEE=os.getenv("FEE")
    return float(RESERVE), float(BUYING_MARGIN),float(SELLING_MARGIN), float(FEE)
    

def _is_plausible(available_eur, available_eth, current_stock_price, reserve, buying_margin, selling_margin, fee, past_stock_prices_1d, past_stock_prices_10m):
    is_plausible = False
    if (available_eth is  not None and   available_eur is not None and 
            current_stock_price is not None and buying_margin is not None and 
            selling_margin is not None and 
            fee is not  None and reserve is not None and 
            len(past_stock_prices_1d)>50 and len(past_stock_prices_10m)>5) :
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


def _upper_threshold_is_satisfied(current_stock_price,past_stock_prices_1d,margin):
    values_above_threshold = [value for value in past_stock_prices_1d if value > (1+margin)*current_stock_price]
    return len(values_above_threshold)>0 
    

def _is_buyable(reserve, buying_margin, available_eur,available_eth, current_stock_price, past_stock_prices_1d, past_stock_prices_10m, last_selling_datetime):
    tradeable_budet=available_eur-reserve
    buying_power_condition=tradeable_budet>(available_eth*current_stock_price)
    upper_threshold_condition_longterm = _upper_threshold_is_satisfied(current_stock_price,past_stock_prices_1d,buying_margin)
    upper_threshold_condition_shorterm = _upper_threshold_is_satisfied(current_stock_price,past_stock_prices_10m,buying_margin)
    if last_selling_datetime is None:
        no_trade_condition = True
    else:
        no_trade_condition = datetime.now() - timedelta(days=1) > last_selling_datetime 
    trend=_determine_trend(past_stock_prices_10m)
    if ((buying_power_condition and upper_threshold_condition_longterm and not (trend == 'decreasing') ) or
        (buying_power_condition and trend == 'increasing' and upper_threshold_condition_shorterm) or
        (buying_power_condition and no_trade_condition )  ):
        return True
    
    return False


def _is_sellable(selling_margin, available_eth, current_stock_price, last_buying_price):
    modified_buying_price=last_buying_price or 10000 # 10000 is just a default value in case of None
    stock_price_condition= (1+selling_margin)*modified_buying_price < current_stock_price
    available_eth_condition=available_eth>=0.03
    if (available_eth_condition and stock_price_condition):
        return True
    return False

def determine_status(available_eur, available_eth, current_stock_price, RESERVE, FEE, BUYING_MARGIN, SELLING_MARGIN, past_stock_prices_1d, past_stock_prices_10m,last_selling_datetime, last_buying_price):
    is_plausible = _is_plausible(available_eur, available_eth, current_stock_price, RESERVE, FEE, BUYING_MARGIN, SELLING_MARGIN, past_stock_prices_1d, past_stock_prices_10m)
    print("is_plausible",is_plausible)

    if is_plausible:
        is_buyable = _is_buyable(RESERVE, BUYING_MARGIN, available_eur,available_eth, current_stock_price, past_stock_prices_1d, past_stock_prices_10m, last_selling_datetime)
        is_sellable = _is_sellable(SELLING_MARGIN, available_eth, current_stock_price, last_buying_price)
        print("is_buyable", is_buyable)
        print("is_sellable", is_sellable)
        if is_buyable:
            return 'buy'
        if is_sellable:
            return 'sell'

    return None


def calculate_eth(input_budget, current_stock_price):
    if current_stock_price is not None:
        num_eth = round(input_budget / current_stock_price,2)
        return num_eth
    else:
        return 0