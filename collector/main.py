
from models import BinanceWebsocketConnector
from data_collector import discover_flowers

if __name__ == "__main__":
    binance_connector = BinanceWebsocketConnector()
    # collect live-trades using websocket
    discover_flowers(binance_connector, aggregation_level=30)
