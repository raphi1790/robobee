
from data_collector import discover_flowers

if __name__ == "__main__":
    # collect live-trades using websocket
    discover_flowers( aggregation_level=30)
