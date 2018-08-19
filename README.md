# Zabbix Alerts Engine

The Zabbix Alerts Engine gathers recently and previously activated Zabbix alerts and stores them in a configured Alerts Database.

## Requirements

Python:

```
Requests
Json
Time
Argparse
mysqlclient
```

OS:

```
sudo apt-get install libmysqlclient-dev #Required for mysqlclient to be installed on ubuntu
```


## Create Database
Database:

```
mysql> create database alerts_db;
```

Table:

```
mysql> use alerts_db;

mysql> CREATE TABLE `alerts` (
`monitoringSystem` varchar(10),
`entityName` varchar(20),
`alertSubject` varchar(255),
`entityId` int(100),
`triggerid` int(100),
`hostid` int(100),
`alertCriticality` int(1),
`alertStartTime` int(20),
`alertId` int(100),
`alertUpdateTime` int(20),
`alertStatus` varchar(255),
`alertCancelTime` int(20),
`alertUrl` varchar(255),
`alertMessage` varchar(255),
PRIMARY KEY (`alertId`),
)
```

## Usage

* Configure `self.url` to be the api url for you Zabbix instance
* `chmod +x Get-ZabbixAlerts.py`
* Query for new alerts `./Get-ZabbixAlerts.py`
* Query for active alerts from Alerts Database `./Get-ZabbixAlerts.py --active`

## Docker

To run this application as a docker continater you need to run the following:

* First you need to clone this repo

```
> git clone https://github.com/frenchtoasters/ZabbixAlerts.git
```

* Then you need to build the `dockerfile` within the repo

```
> cd ~/ZabbixAlerts
> docker build -t zabbixalerts .
```

* After that is complete you can run the container with

```
> docker run --rm --it --name zabbix_alerts zabbixalerts
```

* The class will be invoked in the container and results pushed to database 
