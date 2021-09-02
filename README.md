# robobee
**robobee** is a fully-automated trading-bot on the Bitstamp.net-exchange. It's main focus is trading ETH-EUR-pairs. <br />
This code runs on a Raspberry Pi 4.

## Setup
The following steps have to be executed in order to run the code on a Raspberry Pi 4:
1. Install python 3 and pip3.
2. Install pipenv using pip3 (`pip3 install --user pipenv`)
3. Install docker on the device following this tutorial https://phoenixnap.com/kb/docker-on-raspberry-pi
4. Create an Influx-DB and a Grafana-instance on the device basically following this tutorial: https://medium.com/@petey5000/monitoring-your-home-network-with-influxdb-on-raspberry-pi-with-docker-78a23559ffea
   1. Create an Influx-DB in a docker-container: `sudo docker run -d --name=influxdb --volume=/var/influxdb:/data -p 8086:8086 hypriot/rpi-influxdb`
      1. Create a DB with name *pi_influx*
      2. Create a user *root* with *password* on DB *pi_influx*
   2. Create a Grafana docker-container: `docker run -i -p 3000:3000 --name grafana fg2it/grafana-armhf:v4.1.2`
      1. Connect Grafana with Influx-DB via datasource
5. Clone this repository onto device
6. Create a Bitstamp.net-account and create API-access keys
7. Create a *.env*-file on root directory including the following parameters:
   ```
   INFLUX_DB_USER=root
   INFLUX_DB_PASSWORD=<password>
   API_KEY=<Bitstamp.net api-key>
   API_SECRET=<Bitstamp.net api-secret>
   CLIENT_ID=<Bitstamp.net client-id>
   RESERVE_EUR=<Budget, which shouldn't be touched>
   RESERVE_ETH=<amount of ETH, which shouldn't be touched>
   ```
8. Install TA-Lib library in project root directory following this tutorial https://sachsenhofer.io/install-ta-lib-ubuntu-server/
9. Create a pipenv-environment using `pipenv install` on root directory
10. Create some nice charts on Grafana


## Configuration
The project comes with two connectors; a DummyConnector and a BitstampConnector. The DummyConnector can be used to test strategies, whereas the BitstampConnector actually trades the coins on the exchange. The appropriate connector can be set in in file *account/robobee.py*.

Moreover, it's easy to come up with new trading strategies. You just have to follow the corresponding model-class in order to write your own strategy. In case you want to test it, please change the value in file *account/robobee.py*.

## Running Code
After setup, we're good to go: 
1. Verify docker-containers for Influx-DB and Grafana are running (`docker ps -a`)
2. Open terminal and start pipenv-environment and run data_collector (`python3 collector/main.py`)
3. Open terminal and start pipenv-environment and run robobee (`python3 account/robobee.py`)




