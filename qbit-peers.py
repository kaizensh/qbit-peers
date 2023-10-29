import requests
import json
import socket
import struct
import mariadb
import time
import pygeohash
import logging
from logging.handlers import RotatingFileHandler

# Define parameters for log rotation
LOG_FILE = '/app/logs/script.log'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep three backup copies

# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set up the rotating file handler
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# Configuration --- change me!
CONFIG = {
    "server_ip": "", # http/https is not required
    "qbusername": "",
    "qbport": 443, # 443 for https, 8080 for http are common ports for example
    "qbpassword": "",
    "db_host": "qbit-peers-mariadb", # docker-compose service name
    "db_port": 3306, # default port
    "db_user": "root", # default user
    "db_password": "", # docker compose environment variable
    "db_name": "ip2location"
}


def ip2long(ip):
    """Convert IP address to a decimal number."""
    try:
        # Check if it's an IPv4 address
        if "." in ip:
            packedIP = socket.inet_aton(ip)
            return struct.unpack("!L", packedIP)[0]
        # Check if it's an IPv6 address
        elif ":" in ip:
            packedIP = socket.inet_pton(socket.AF_INET6, ip)
            return int.from_bytes(packedIP, byteorder='big')
    except OSError:
        print(f"Invalid IP address: {ip}")
        return None


def main():
    server_address = f"https://{CONFIG['server_ip']}:{CONFIG['qbport']}"

    with requests.Session() as s:
        # Login to qbittorrent
        logging.info("Logging in to qbittorrent.")
        s.post(f"{server_address}/api/v2/auth/login",
               data={"username": CONFIG['qbusername'], "password": CONFIG['qbpassword']})

        # Get list of torrents
        response = s.get(f"{server_address}/api/v2/torrents/info")
        if response.status_code == 200:
            torrents = response.json()
            logging.info(f"Retrieved {len(torrents)} torrents.")
        else:
            logging.error(f"Error: Received status code {response.status_code}")
            logging.error(response.text)

        # Connect to MariaDB
        logging.info("Connecting to MariaDB.")
        with mariadb.connect(
            host=CONFIG['db_host'],
            port=CONFIG['db_port'],
            user=CONFIG['db_user'],
            password=CONFIG['db_password'],
            database=CONFIG['db_name'],
            autocommit=True
        ) as mydb:

            current_time = str(int(time.time()))

            for torrent in torrents:
                torrent_peers = s.get(
                    f"{server_address}/api/v2/sync/torrentPeers?hash={torrent['hash']}").json()

                # Prepare database statement
                mycursor = mydb.cursor()
                insert_query = "INSERT INTO ip2location.peer_list(time, ip_address, geohash) VALUES (%s, %s, %s)"

                # Collect data for batch insert
                data_to_insert = []

                for peer in torrent_peers["peers"]:
                    ip = peer.split(":")[0]
                    long_ip = ip2long(ip)
                    if long_ip is None:
                        continue

                    select_query = f"SELECT latitude,longitude FROM ip2location.ip2location_db5 WHERE {long_ip} BETWEEN ip_from AND ip_to;"
                    mycursor.execute(select_query)
                    results = mycursor.fetchone()

                    if results:
                        latitude, longitude = results

                        if latitude != 0 and longitude != 0:
                            geohash = pygeohash.encode(latitude, longitude)
                            data_to_insert.append((current_time, ip, geohash))

                # Batch insert data
                if data_to_insert:
                    logging.info(f"Inserting {len(data_to_insert)} records into the database.")
                    mycursor.executemany(insert_query, data_to_insert)
                
        # Logout from qbittorrent
        logging.info("Logging out from qbittorrent.")
        s.get(f"{server_address}/api/v2/auth/logout")


if __name__ == "__main__":
    main()
