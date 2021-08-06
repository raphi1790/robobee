from dataclasses import dataclass
from datetime import datetime
import os
from dotenv.main import load_dotenv
from influxdb.client import InfluxDBClient
import pandas as pd

@dataclass
class LiveTrade:
    timestamp_utc: datetime
    pair: str
    exchange: str
    price: float

    def to_dict(self):
        return {'timestamp_utc': self.timestamp_utc,
                'pair': self.pair,
                'exchange': self.exchange,
                'price': self.price}

@dataclass
class Indicator:
    name: str

    def add_simple_moving_average_to_df(self, df, lookback, column ) -> pd.DataFrame:
        df['sma_'+column+'_'+str(lookback)] = df.loc[:,column].rolling(window=lookback).mean()
        return df

    def apply_indicator(self, candlestick_df, *args) -> pd.DataFrame:
        pass



@dataclass
class Strategy:
    name: str

    def calculate_current_trend(self):
        pass

    def buy_sell_option(self):
        pass


@dataclass
class Transaction:
    timestamp_utc: datetime
    exchange: str
    pair: str
    amount: float
    price: float
    id: str
    type: str

    def to_influx(self, connector):
        return  {
                                    "measurement": f"{str(connector)}_transactions",
                                    "tags": {
                                        "pair": self.pair,
                                        "exchange": self.exchange,
                                        "transaction_type": self.type,
                                        "id": self.id
                                    
                                    },
                                    "time": self.timestamp_utc,
                                    "fields": {
                                        "price": round(float(self.price),2),
                                        "amount": round(float(self.amount),2) 
                                    }
                                }

@dataclass
class AccountBalance:
    timestamp_utc:datetime
    pair: str
    exchange: str
    eth_available:float
    eur_available:float
    balance_total:float

    def to_influx(self, connector):
        return   {
                            "measurement": f"{str(connector)}_account_balance",
                            "tags": {
                                "pair": self.pair,
                                "exchange": self.exchange
                            
                            },
                            "time": datetime.utcnow(),
                            "fields": {
                                "eur_available": round(float(self.eur_available),2),
                                "eth_available": round(float(self.eth_available),2),
                                "balance_total": round(float(self.balance_total),2)
                                
                            }
                        }   

    def to_dict(self):
        return {'timestamp_utc': self.timestamp_utc,
                'pair': self.pair,
                'exchange': self.exchange,
                'eth_available': self.eth_available,
                'eur_available': self.eur_available,
                'balance_total': self.balance_total}                


@dataclass
class AccountConnector:
    account_balance:AccountBalance
    
    def _valid_transaction_volume(self, amount, price, transaction_type):
        eur_necessary = round(amount * price,2)
        eth_necessary = amount


        # print("eur_available",self.account_balance.eur_available )
        # print("eth_available",self.account_balance.eth_available )
        # print("eur_necessary",eur_necessary )
        # print("eth_necessary",eth_necessary )

        if(transaction_type == 'buy'):
            return self.account_balance.eur_available > eur_necessary
        if(transaction_type == 'sell'):
            return self.account_balance.eth_available > eth_necessary
        else:
            return False


    def _write_transaction(self,transaction:Transaction, connector):
        try:
            influx_connector = InfluxConnector()
            influx_connector.write_point(transaction.to_influx(connector=connector))
        except Exception as e:
            print(e)

    def _write_account_balance(self, acount_balance:AccountBalance, connector):
        try:
            influx_connector = InfluxConnector()
            print("influx_connector", influx_connector)
            print("account_balance.to_influx()", acount_balance.to_influx(connector=connector))
            influx_connector.write_point(acount_balance.to_influx(connector=connector))
        except Exception as e:
            print(e)
    


    def get_balance(self):
        pass

    def update_balance(self):
        pass

    def buy_eth(self,amount, price):
        pass

    def sell_eth(self,amount, price):
        pass

@dataclass
class InfluxConnector:
    client: InfluxDBClient

    def __init__(self):
        load_dotenv()
        user=os.getenv("INFLUX_DB_USER")
        password=os.getenv("INFLUX_DB_PASSWORD")
        self.client = InfluxDBClient('localhost', 8086, user, password, 'pi_influxdb')
    
    def get_client(self):
        return self.client

    def write_point(self,influx_point):
        self.client.write_points([influx_point])









        
        


