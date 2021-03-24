import sys
from api import get_balance, get_current_eth_eur_value
from dotenv import load_dotenv, find_dotenv
import time
import os
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pytz


def update_account_balance(offset=60):
    load_dotenv()
    user=os.getenv("INFLUX_DB_USER")
    password=os.getenv("INFLUX_DB_PASSWORD")
    client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    print("DB-connection established:", client)

    print("start collecting data:")
   
    
    while True:
        
        current_time = datetime.now(tz=pytz.utc)
        current_eth_eur_value = get_current_eth_eur_value()
        eur_available, eth_available = get_balance()
        # print("current_eth_eur_value", current_eth_eur_value)
        # print("type(eth_available)", type(float(eth_available)))
        # print("type(current_eth_eur_value)", type(current_eth_eur_value))

        if current_eth_eur_value is not None:

            point = [
                        {
                            "measurement": "account_balance",
                            "tags": {
                                "currency": "EUR",
                                "exchange": "Bitstamp"
                            
                            },
                            "time": current_time,
                            "fields": {
                                "eur_value": float(eur_available),
                                "eth_available": float(eth_available),
                                "balance_total": float(eur_available) + float(eth_available) * float(current_eth_eur_value)
                                
                            }
                        }
                ]
            # print("point", point)

            client.write_points(point)
        time.sleep(offset)





if __name__ == "__main__":
    update_account_balance(60)


    
