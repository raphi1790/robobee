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
    

def _is_plausible(available_eur, available_eth, current_stock_price, reserve, buying_margin, selling_margin, fee, past_stock_prices_1d,past_stock_prices_7d_1d, past_stock_prices_10m):
    is_plausible = False
    if (available_eth is  not None and   available_eur is not None and 
            current_stock_price is not None and buying_margin is not None and 
            selling_margin is not None and 
            fee is not  None and reserve is not None and 
            len(past_stock_prices_1d)>50 and len(past_stock_prices_10m)>5 and len(past_stock_prices_7d_1d)>50) :
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
    moving_averages = _calculate_moving_average(list_stock_prices,10)
    if len(moving_averages)<=5:
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


def _is_above_threshold(current_stock_price,past_stock_prices,margin):
    values_above_threshold = [value for value in past_stock_prices if value > (1+margin)*current_stock_price]
    return len(values_above_threshold)>3

def _upper_threshold_is_satisfied(current_stock_price,past_stock_prices_1d,past_stock_prices_7d_1d, buying_margin):
    # is_above_upper_threshold_1d = _is_above_threshold(current_stock_price,past_stock_prices_1d, buying_margin)
    # is_above_upper_threshold_7d = _is_above_threshold(current_stock_price,past_stock_prices_7d_1d,buying_margin)
    max_1d = max(past_stock_prices_1d)
    max_7d_1d =  max(past_stock_prices_7d_1d)
    is_alltime_high = max_1d > max_7d_1d
    print("max_1d",max_1d)
    print("max_7d", max_7d_1d)
    print("is_alltime_high",is_alltime_high )
    if(is_alltime_high):
        # Increase buying_margin in order to deal with recent alltime-highs
        return _is_above_threshold(current_stock_price,past_stock_prices_1d,1.5*buying_margin)
    else:
        return _is_above_threshold(current_stock_price,past_stock_prices_1d,buying_margin)

def _is_below_threshold(relevant_stock_price,past_stock_prices,margin):
    values_below_threshold = [value for value in past_stock_prices if value < relevant_stock_price / (1+margin)]
    return len(values_below_threshold)>3   

def _is_buyable(reserve, buying_margin, available_eur,available_eth, current_stock_price, past_stock_prices_1d,past_stock_prices_7d_1d, past_stock_prices_10m, last_selling_datetime, trend):
    tradeable_budet=available_eur-reserve
    buying_power_condition=tradeable_budet>(available_eth*current_stock_price)
    upper_threshold_condition_shorterm = _is_above_threshold(current_stock_price,past_stock_prices_10m,buying_margin)
    upper_threshold_is_satisfied_longterm = _upper_threshold_is_satisfied(current_stock_price,past_stock_prices_1d,past_stock_prices_7d_1d, buying_margin)
    print("buying condition longterm satisfied", upper_threshold_is_satisfied_longterm )
    print("buying condition shorterm satisfied", upper_threshold_condition_shorterm )
    #if last_selling_datetime is None:
        # no_trade_condition = True
    # else:
        # no_trade_condition = datetime.now() - timedelta(days=1) > last_selling_datetime 
    
    
    if ((buying_power_condition and upper_threshold_is_satisfied_longterm and not (trend == 'decreasing') ) or
        (buying_power_condition and trend == 'increasing' and upper_threshold_condition_shorterm) ):
        if (buying_power_condition and upper_threshold_is_satisfied_longterm and not (trend == 'decreasing')):
            print("condition longterm satisfied")
        if (buying_power_condition and trend == 'increasing' and upper_threshold_condition_shorterm):
            print("condition shorterm satisfied")
        return True
    
    return False

def _buy_fallback(last_selling_datetime, last_buying_datetime, last_buying_price, available_eth, available_eur, reserve,past_stock_prices_1d,past_stock_prices_10m, current_stock_price, trend ):
    buying_was_last_trade = last_selling_datetime < last_buying_datetime # buying was the last trade
    eth_are_already_bought = available_eth > 0.03 
    only_eur_reserve_is_available = available_eur < reserve * 1.01
    fallback_is_already_bought = available_eur < 20
    fallback_ratio = 0.15
    lower_trend_than_last_buying = _is_below_threshold(last_buying_price,past_stock_prices_1d,fallback_ratio )
    current_price_condition = current_stock_price * (1+fallback_ratio)< last_buying_price 
    if(buying_was_last_trade and eth_are_already_bought and only_eur_reserve_is_available and
       lower_trend_than_last_buying and current_price_condition and not (trend == 'decreasing') and not fallback_is_already_bought ):
       return True
    return False

def _calculate_selling_margin(last_buying_datetime, selling_margin):
    current_time = datetime.now() 
    if last_buying_datetime < current_time - timedelta(days=2):
        return 0.6 * selling_margin
    if last_buying_datetime < current_time - timedelta(days=1):
        return 0.8*selling_margin
    else:
        return selling_margin

def _is_fallback_sellable(last_buying_transaction, last_fallback_transaction, selling_margin, current_stock_price, available_eth):
    if (last_fallback_transaction['amount'] is None or last_fallback_transaction['price'] is None
         or last_buying_transaction['amount'] is None or last_buying_transaction['price'] is None or available_eth == 0) :
        return False
    
    fallback_reserve = last_fallback_transaction['amount'] * last_fallback_transaction['price']
    traded_budget = last_buying_transaction['amount'] * last_buying_transaction['price']
    necessary_stock_price = ((1+selling_margin)*traded_budget + fallback_reserve) /available_eth
    return  necessary_stock_price < current_stock_price
 


def _is_sellable(selling_margin, available_eth, current_stock_price, past_stock_prices_10m,trend, available_eur, reserve, last_buying_transaction, last_selling_transaction, last_fallback_transaction):
    last_buying_datetime = last_buying_transaction['time']
    last_buying_price = last_buying_transaction['price']
    modified_buying_price=last_buying_price or 10000 # 10000 is just a default value in case of None
    modified_margin = _calculate_selling_margin(last_buying_datetime, selling_margin)
    print("last_buying_price:",last_buying_price)
    print("last_buying_date",last_buying_datetime )
    print("seling_modified_margin:",modified_margin )
    stock_price_condition= (1+modified_margin)*modified_buying_price < current_stock_price
    print("selling_stock_price_condition:", stock_price_condition)
    available_eth_condition=available_eth>=0.03
    fallback_condition_eur = available_eur < 0.1 * reserve
    fallback_condition_price = _is_fallback_sellable(last_buying_transaction, last_fallback_transaction, selling_margin, current_stock_price, available_eth) # calculated amount, where we still make profit;
    print("selling_fallback_condition_price:", fallback_condition_price)
    print("selling_fallback_condition_eur:", fallback_condition_eur)
    if ((available_eth_condition and stock_price_condition and not (trend == 'increasing')) or
        (fallback_condition_eur and fallback_condition_price and not (trend == 'increasing'))) :
        return True
    return False



def determine_status(available_eur, available_eth, current_stock_price, RESERVE, FEE, BUYING_MARGIN, SELLING_MARGIN
    , past_stock_prices_1d,past_stock_prices_7d_1d
    , past_stock_prices_10m
    ,last_buying_transaction
    ,last_selling_transaction
    ,last_fallback_transaction):
    is_plausible = _is_plausible(available_eur, available_eth, current_stock_price, RESERVE, FEE, BUYING_MARGIN, SELLING_MARGIN, past_stock_prices_1d,past_stock_prices_7d_1d, past_stock_prices_10m)
    print("is_plausible",is_plausible)
    if is_plausible:
        trend=_determine_trend(past_stock_prices_10m)
        print("stock_price:", current_stock_price)
        print("trend", trend)

        is_buyable = _is_buyable(RESERVE, BUYING_MARGIN, available_eur,available_eth, current_stock_price, past_stock_prices_1d,past_stock_prices_7d_1d, past_stock_prices_10m, last_selling_transaction['time'], trend)
        is_sellable = _is_sellable(SELLING_MARGIN, available_eth, current_stock_price, past_stock_prices_10m, trend, available_eur, RESERVE, last_buying_transaction, last_selling_transaction, last_fallback_transaction)
        buy_fallback = _buy_fallback(last_selling_transaction['time'], last_buying_transaction['time'], last_buying_transaction['price'], available_eth, available_eur, RESERVE,past_stock_prices_1d,past_stock_prices_10m, current_stock_price, trend)
        print("is_buyable", is_buyable)
        print("is_sellable", is_sellable)
        print("buy_fallback", buy_fallback )
        if is_buyable:
            return 'buy'
        if is_sellable:
            return 'sell'
        if buy_fallback:
            return 'buy_fallback'

    return None


def calculate_eth(input_budget, current_stock_price):
    if current_stock_price is not None:
        num_eth = round(input_budget / current_stock_price,2)
        return num_eth
    else:
        return 0