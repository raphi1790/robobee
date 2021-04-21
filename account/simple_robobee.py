import sys
from api.api import get_balance, get_current_eth_eur_value, buy_eth, sell_eth, get_eth_eur_values, get_last_transaction
from dotenv import load_dotenv, find_dotenv
import time
import os
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz
from helper import determine_status, get_config_data, calculate_eth




def collect_honey():
    RESERVE,BUYING_MARGIN, SELLING_MARGIN, FEE,   = get_config_data()
    while True:
        available_eur, available_eth = get_balance()
        current_stock_price = get_current_eth_eur_value()
        past_stock_prices_1d = get_eth_eur_values(from_dt_str='now() - 1d' , to_dt_str='now()')
        past_stock_prices_7d_1d = get_eth_eur_values(from_dt_str='now() - 7d' , to_dt_str='now() - 1d')
        past_stock_prices_10m = get_eth_eur_values(from_dt_str='now() - 10m' , to_dt_str='now()')
        last_buying_transaction = get_last_transaction('buy')
        last_selling_transaction = get_last_transaction('sell')
        last_fallback_transaction = get_last_transaction('buy_fallback')
        action = determine_status(available_eur, available_eth
            , current_stock_price, RESERVE, FEE, BUYING_MARGIN, SELLING_MARGIN
            , past_stock_prices_1d,past_stock_prices_7d_1d, past_stock_prices_10m
            ,last_buying_transaction
            ,last_selling_transaction
            ,last_fallback_transaction)
        print("action", action)
        if action == 'buy':
            tradeable_budget=available_eur - RESERVE
            buying_eth = calculate_eth(tradeable_budget, current_stock_price)
            print("tradeable_budget", tradeable_budget)
            print("buying_eth", buying_eth)
            buy_eth(buying_eth, current_stock_price,'buy')
        if action == 'buy_fallback':
            tradeable_budget=available_eur
            buying_eth = calculate_eth(tradeable_budget, current_stock_price)
            print("tradeable_budget", tradeable_budget)
            print("buying_eth", buying_eth)
            buy_eth(buying_eth, current_stock_price,'buy_fallback')

        if action == 'sell':
            print("selling available_eth", available_eth)
            sell_eth(available_eth, current_stock_price )

        
        time.sleep(30)
        

if __name__ == "__main__":
    collect_honey()