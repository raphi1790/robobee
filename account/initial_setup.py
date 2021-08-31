# Initial account-balance
from models import InfluxConnector, AccountBalance
from datetime import datetime

influx_connector = InfluxConnector()
client = influx_connector.client

current_account_balance = AccountBalance(timestamp_utc=datetime.utcnow(), pair="ETH-EUR", exchange="Bitstamp", eth_available=1.5, eur_available=1000, balance_total=5247.65)
influx_connector.write_point(current_account_balance.to_influx(connector="simulator"))