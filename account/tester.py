import sys
from api.api_v2 import *
from datetime import datetime, timedelta
from helper_v2 import *
import json



if __name__ == "__main__":
    # content = check_order_status("1340141453066241")
    # print("content", content)
    # get_open_orders()
    # buy_limit_order(amount=0.03, price=1390)
    #sell_limit_order(amount=0.03, price=1530)
    #get_open_orders()
    # content = check_order_status("1338019410989057")
    # print(content['status'])
    # sell_eth(0.04)
    # eur, eth = get_balance()
    # a, b = get_last_transaction_price('sell')
    
    # print(a)
    # trend = None
    # print(not (trend == 'decreasing') )
    # print (a -  timedelta(days=1))

    # person_string = '{"name": "Bob", "age": 25}'
    # student = Student(**json.loads(person_string))
    # print(type(student))
    # print(student.name)

    live_trades= get_eth_eur_values(from_dt_str="now()-10d")

    create_candlesticks(live_trades)




