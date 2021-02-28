from influxdb import InfluxDBClient

client = InfluxDBClient('localhost', 8086, 'root', 'Gotthard', "pi_influxdb")
print("client", client)

dbs = client.get_list_database()
print("dbs", dbs)

results = client.query('SELECT * FROM "pi_influxdb"."autogen"."bitcoin_price" order by time desc limit 10')

print("results", results)