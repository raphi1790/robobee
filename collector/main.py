from models import BinanceWebsocketConnector, InfluxConnector, Buffer

if __name__ == "__main__":
    # collect live-trades using websocket
    binance_connector = BinanceWebsocketConnector()
    influx_connector = InfluxConnector()
    buffer = Buffer()
    aggregation_level = 30
    print("aggregation-level [s]:", aggregation_level)
    try:
        binance_connector.connect_websocket(buffer, influx_connector, aggregation_level)
    except Exception as err:
        print(err)
        print("connect failed")

