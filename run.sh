#!/usr/bin/with-contenv bashio
set -e


EMAIL=$(bashio::config 'email')
PASSWORD=$(bashio::config 'password')

export MQTT_HOST
export MQTT_PORT
export MQTT_USER
export MQTT_PASSWORD

MQTT_HOST="$(bashio::services mqtt "host")"
MQTT_PORT="$(bashio::services mqtt "port")"
MQTT_USER="$(bashio::services mqtt "username")"
MQTT_PASSWORD="$(bashio::services mqtt "password")"

bashio::log.info "Starting Thermowatt Bridge for $EMAIL..."

python3 -u /thermowatt_bridge.py "$EMAIL" "$PASSWORD"
