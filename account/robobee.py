import time
from connectors import DummyConnector
from models import AccountConnector, Strategy
from strategies import SimpleStrategy, EmaStrategy


def collect_honey(account_connector:AccountConnector, strategy: Strategy, live_trades_connector_name):
    while True:
        
        strategy.apply(connector=account_connector, live_trades_connector_name=live_trades_connector_name)
        account_connector.update_balance()

        print("updated...")
        time.sleep(30)
    
        

if __name__ == "__main__":
    dummy_connector = DummyConnector()
    simple_strategy = SimpleStrategy()
    ema_strategy = EmaStrategy()
    live_trades_connector_name='binance'
    collect_honey(account_connector=dummy_connector, strategy=ema_strategy, live_trades_connector_name=live_trades_connector_name)