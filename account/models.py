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
                                        "amount": float(self.amount)//0.0001/10000 
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
                                "eth_available": float(self.eth_available)//0.0001/10000, # round down to 4 decimal 
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
    eth_reserve:float
    eur_reserve:float 
    fee:float
    
    def _valid_transaction_volume(self, amount, price, transaction_type):
        if price is None:
            return False
        eur_necessary = round(amount * price,2)
        eth_necessary = amount


        # print("eur_available",self.account_balance.eur_available )
        # print("eth_available",self.account_balance.eth_available )
        # print("eur_necessary",eur_necessary )
        # print("eth_necessary",eth_necessary )

        if(transaction_type == 'buy'):
            return self.account_balance.eur_available >= eur_necessary
        if(transaction_type == 'sell'):
            return self.account_balance.eth_available >= eth_necessary
        else:
            return False

    def tradeable_eth(self):
        return self.account_balance.eth_available - self.eth_reserve
    
    def tradeable_eur(self):
        return self.account_balance.eur_available - self.eur_reserve

    def _write_transaction(self,transaction:Transaction, connector):
        try:
            influx_connector = InfluxConnector()
            influx_connector.write_point(transaction.to_influx(connector=connector))
        except Exception as e:
            print(e)

    def _write_account_balance(self, acount_balance:AccountBalance, connector):
        try:
            influx_connector = InfluxConnector()
            print("account_balance.to_influx()", acount_balance.to_influx(connector=connector))
            influx_connector.write_point(acount_balance.to_influx(connector=connector))
        except Exception as e:
            print(e)
    
    def get_last_transaction(self, connector, **kwargs):
        try:
            influx_connector = InfluxConnector()
            client = influx_connector.get_client()
            if 'type' in kwargs:
                query_str = f"""SELECT * FROM {connector}_transactions WHERE transaction_type = '{kwargs['type']}' order by time desc limit 1"""
                
            else: 
                query_str = f"""SELECT * FROM {connector}_transactions order by time desc limit 1"""
            result_set = client.query(query_str)
            result_points = list(result_set.get_points(f"{connector}_transactions"))
            return Transaction(timestamp_utc=result_points[0]['time']
                    , exchange=result_points[0]['exchange']
                    , pair=result_points[0]['pair']
                    , amount=result_points[0]['amount']
                    , price=result_points[0]['price']
                    , id =result_points[0]['id']
                    , type=result_points[0]['transaction_type'] )
        except Exception as e:
           return Transaction(timestamp_utc=datetime.utcnow()
                    , exchange=None
                    , pair=None
                    , amount=None
                    , price=None
                    , id =None
                    , type=None )
    

        
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


@dataclass
class Strategy:
    name: str

    def apply(self, connector: AccountConnector, live_trades_connector_name):
        pass








        
        


