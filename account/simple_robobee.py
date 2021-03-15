import sys
from api.api import get_balance, get_current_eth_eur_value, buy_eth, sell_eth
from dotenv import load_dotenv, find_dotenv
import time
import os
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz


def _calculate_eth(input_budget):
    current_stock_price = get_current_eth_eur_value()
    if current_stock_price is not None:
        num_eth = round(input_budget / current_stock_price,2)
        return num_eth
    else:
        return 0

def collect_honey():

    RESEVERE = 2800
    FEE=0.005
    MARGIN=0.01
    upper_threshold = 2*FEE + MARGIN
    eur_available, eth_available = get_balance()
    tradable_budget = eur_available-RESEVERE
    print("tradable_budget",tradable_budget)

    if tradable_budget > 0:
        num_eth = _calculate_eth(tradable_budget)
        print("num_eth",num_eth)
        # response = buy_eth(num_eth)


        




if __name__ == "__main__":
    collect_honey()