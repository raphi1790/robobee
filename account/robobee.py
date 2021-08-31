import time
from connectors import DummyConnector
from models import AccountConnector, Strategy
from strategies import SimpleStrategy


def collect_honey(account_connector:AccountConnector, strategy: Strategy):
    while True:
        
        strategy.apply(connector=account_connector)
        account_connector.update_balance()

        print("updated...")
        time.sleep(30)
    
        

if __name__ == "__main__":
    dummy_connector = DummyConnector()
    simple_strategy = SimpleStrategy()
    collect_honey(account_connector=dummy_connector, strategy=simple_strategy)