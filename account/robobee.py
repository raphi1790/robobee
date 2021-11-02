import time
from connectors import BinanceConnector, DummyConnector
from models import AccountConnector, Strategy
from strategies import SimpleStrategy, EmaStrategy, NoLossStrategy


def collect_honey(account_connector:AccountConnector, strategy: Strategy, live_trades_connector_name):
    while True:
        
        strategy.apply(connector=account_connector, live_trades_connector_name=live_trades_connector_name)
        account_connector.update_balance()

        print("updated...")
        time.sleep(30)
    
        

if __name__ == "__main__":
    binance_connector = BinanceConnector()
    simple_strategy = SimpleStrategy()
    ema_strategy = EmaStrategy()
    live_trades_connector_name='binance'
    collect_honey(account_connector=binance_connector, strategy=ema_strategy, live_trades_connector_name=live_trades_connector_name)