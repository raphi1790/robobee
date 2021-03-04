import sys
from api.api import get_balance, get_current_eth_eur_value

if __name__ == "__main__":
    eur_available, eth_available = get_balance()
    print(eur_available)

    result = get_current_eth_eur_value()
    print("result", result)