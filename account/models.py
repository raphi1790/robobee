from dataclasses import dataclass
from datetime import datetime
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
class AccountConnector:
    
    def _valid_transaction_volume(self, amount, price, transaction_type):
        eur_available, eth_available = self.get_balance()
        eur_necessary = round(amount * price,2)
        eth_necessary = amount

        # print("eur_available",eur_available )
        # print("eth_available",eth_available )
        # print("eur_necessary",eur_necessary )
        # print("eth_necessary",eth_necessary )

        if(transaction_type == 'buy'):
            return eur_available > eur_necessary
        if(transaction_type == 'sell'):
            print("eth_available > eth_necessary",eth_available > eth_necessary)
            return eth_available > eth_necessary
        else:
            return False




    def get_balance(self):
        pass

    def buy_eth(self,amount, price):
        pass

    def sell_eth(self,amount, price):
        pass





        
        


