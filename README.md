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
   RESERVE=<Budget, which shouldn't be touched>
   FEE=0.005
   BUYING_MARGIN=0.02
   SELLING_MARGIN=0.02
   ```
8. Create a pipenv-environment using `pipenv install` on root directory
9. Create some nice charts on Grafana

## Running Code
After setup, we're good to go: 
1. Verify docker-containers for Influx-DB and Grafana are running (`docker ps -a`)
2. Open terminal and start pipenv-environment and run data_collector (`python3 collector/main.py`)
3. Open terminal and start pipenv-environment and run account-monitoring (`python3 account/account_manager.py`)
4. Open terminal and start pipenv-environment and run actually trading-bot (`python3 account/simple_robobee.py`)

