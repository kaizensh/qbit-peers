CREATE DATABASE IF NOT EXISTS ip2location;

USE ip2location;

CREATE TABLE ip2location_db5(
    ip_from BIGINT NOT NULL,
    ip_to BIGINT NOT NULL,
    country_code CHAR(2) NOT NULL,
    country_name VARCHAR(64) NOT NULL,
    region_name VARCHAR(128) NOT NULL,
    city_name VARCHAR(128) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    PRIMARY KEY (ip_from, ip_to)
);

CREATE TABLE peer_list (
    time INT(11),
    ip_address VARCHAR(15),
    geohash VARCHAR(20)
);
