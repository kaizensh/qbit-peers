import requests
import json
import socket
import struct
import mariadb
import time
import pygeohash

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
        s.post(f"{server_address}/api/v2/auth/login",
               data={"username": CONFIG['qbusername'], "password": CONFIG['qbpassword']})

        # Get list of torrents
        response = s.get(f"{server_address}/api/v2/torrents/info")
        if response.status_code == 200:
            torrents = response.json()
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)

        # Connect to MariaDB
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
                    mycursor.executemany(insert_query, data_to_insert)
                
        # Logout from qbittorrent
        s.get(f"{server_address}/api/v2/auth/logout")


if __name__ == "__main__":
    main()
