import time
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime
from api import *

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

def _is_buyable(reserve, margin, fee, available_eur,available_eth, current_stock_price, past_stock_prices):
    print("past_stock_prices",past_stock_prices)
    return True

def _is_sellable():
    return False

def determine_status():
    RESERVE, FEE, MARGIN  = _get_config_data()
    available_eur, available_eth = get_balance()
    current_stock_price = get_current_eth_eur_value()
    past_stock_prices = get_eth_eur_values()
    last_selling_price = get_last_transaction_price('sell')
    last_buying_price = get_last_transaction_price('buy')
    is_plausible = _is_plausible(available_eur, available_eth, current_stock_price, RESERVE, FEE, MARGIN)
    is_buyable = _is_buyable(RESERVE, MARGIN, FEE, available_eur,available_eth, current_stock_price, past_stock_prices)
    is_sellable = _is_sellable()
    print("is_plausible",is_plausible)

    if is_plausible and is_buyable:
        return 'buy'
    
    if is_plausible and is_sellable:
        return 'sell'
    
    return None

