![World Map](/assets/worldmap.png)

# qbit-peers

Forked from: https://github.com/Roadeo/qbittorrent-peers-location-grafana

A python script (along with instructions) to display the locations of all the peers your qBittorrent client is connected to in a Grafana worldmap dashboard.

## Pre-requisites

The following instructions are assuming:

- Docker is already running and configured
- Grafana is already running and configured

## Instructions

### Clone the repository

```
git clone https://github.com/kaizensh/qbit-peers && cd qbit-peers
```

### Download the IP2Location database

- Create a data directory in the cloned repository
- Download the IP2Location LITE database from https://lite.ip2location.com/database/ip-country-region-city-latitude-longitude
- Extract the CSV file from the ZIP file and place it in the data directory

### Configure the docker compose file

`docker-compose.yml`

- Change /opt/qbit-peers to your desired location
- Change the password for the MariaDB root user

### Configure the python script

`qbit-peers.py`

- Configure the qbittorrent server ip, port, username and password
- Configure the MariaDB host, port, user, password and database name

### Run the docker compose file

`docker-compose up -d`

### Stop the qbit-peers container to avoid any potential issues before importing the IP2Location database

`docker stop qbit-peers`

## Import the IP2Location database

`IP2LOCATION-LITE-DB5.CSV`

### Enter the MariaDB container

```sh
docker exec -it qbit-peers-mariadb mariadb -uroot -p<password>
```

```sql
USE ip2location;
```

```sql
LOAD DATA LOCAL INFILE '/tmp/IP2LOCATION-LITE-DB5.CSV'
INTO TABLE ip2location_db5
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

```sql
EXIT;
```

### Start the qbit-peers container

```sh
docker start qbit-peers
```

## Configure Grafana

### Add the MariaDB datasource

In Grafana, go to Connections > Data Sources > Add new source > MySQL

- Name: `qbit-peers-mariadb`
- Host: `qbit-peers-mariadb`
- Database: `ip2location`
- User: `root`
- Password: `<password>`

Save & Test

### Add the Worldmap Panel

Install the Worldmap Panel plugin:
https://grafana.com/grafana/plugins/grafana-worldmap-panel/

### Create a new Dashboard

- Add a new Panel
- Change Visualization to Worldmap Panel
- Change the Datasource to qbit-peers-mariadb
- Change the Format to Table
- Change the Dataset to ip2location
- Change the Table to peer_list
- Change the Column value to geohash

### Configure the Worldmap Panel

- Change the Min circle size to 1 (or your desired size)
- Change the Max circle size to 1 (or your desired size)
- Change the Location data to geohash
- Change the Field mapping to geohash
