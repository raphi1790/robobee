from models import BinanceWebsocketConnector, InfluxConnector, Buffer

if __name__ == "__main__":
    # collect live-trades using websocket
    binance_connector = BinanceWebsocketConnector()
    try:
        binance_connector.connect_websocket()
    except Exception as err:
        print(err)
        print("connect failed")

