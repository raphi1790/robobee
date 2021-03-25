import sys
from api.api import get_balance, get_current_eth_eur_value, buy_eth, sell_eth, get_eth_eur_values
from dotenv import load_dotenv, find_dotenv
import time
import os
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
from helper import determine_status


def _calculate_eth(input_budget):
    current_stock_price = get_current_eth_eur_value()
    if current_stock_price is not None:
        num_eth = round(input_budget / current_stock_price,2)
        return num_eth
    else:
        return 0

def _is_buyable(current_eth_value):
    PAST_THRESHOLD = 0.02
    if not (isinstance(current_eth_value, int) or isinstance(current_eth_value, float)):
        return False
    print("upper_threshold",(1+PAST_THRESHOLD)*current_eth_value)
    all_possible_eth_values = get_eth_eur_values()
    print("all_relevant_eth_values",all_possible_eth_values)
    values_above_threshold = [value for value in all_possible_eth_values if value > (1+PAST_THRESHOLD)*current_eth_value]
    print("values_above_threshold",values_above_threshold)
    if len(values_above_threshold) > 0:
        return True
    else:
        return False

def collect_honey():
    while True:
        action = determine_status()
        print("action", action)
    #     if action == 'buy':
        
    #     if action == 'sell':
        
        time.sleep(30)
        

    # RESEVERE = 2800
    # FEE=0.005
    # MARGIN=0.01
    # upper_threshold = 2*FEE + MARGIN
    # eur_available, eth_available = get_balance()
    # tradable_budget = eur_available-RESEVERE
    # print("tradable_budget",tradable_budget)
    # current_eth_value = get_current_eth_eur_value()
    # if tradable_budget > 0 and eth_available == 0 and _is_buyable(current_eth_value):
    #     num_eth = _calculate_eth(tradable_budget)
    #     print("num_eth",num_eth)
    #     # response = buy_eth(num_eth)
    # if eth_available > 0:


        




if __name__ == "__main__":
    collect_honey()