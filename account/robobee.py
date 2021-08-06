import time
from connectors import DummyConnector
from models import AccountConnector, Strategy


def collect_honey(account_connector:AccountConnector):
    while True:
        
        account_connector.update_balance()
        print("updated...")
        time.sleep(30)
    
        

if __name__ == "__main__":
    dummy_connector = DummyConnector()
    collect_honey(account_connector=dummy_connector)