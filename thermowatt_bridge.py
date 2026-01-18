import sys
import json
import time
import ssl
import requests
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
EMAIL = sys.argv[1]
PASSWORD = sys.argv[2]
API_BASE = "https://myapp-connectivity.com"
AWS_HOST = "a29wru6dvi3p6q-ats.iot.eu-west-1.amazonaws.com"
AWS_PORT = 8883

MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
MQTT_HOST = os.getenv("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Global registry to track multiple heaters
aws_clients = {}

# --- 1. DISCOVERY LOGIC ---
def get_heaters():
    payload = {"email": EMAIL, "password": PASSWORD, "app": "thermowatt", "version": "01.03.21", "lang": "en"}
    try:
        r = requests.post(f"{API_BASE}/login.php", data=payload, verify=False, timeout=10)
        return r.json().get("termostati", [])
    except Exception as e:
        print(f"❌ API Error: {e}")
        return []

def publish_ha_discovery(local_client, serial, name):
    discovery_topic = f"homeassistant/water_heater/{serial}/config"
    payload = {
        "unique_id": f"thermowatt_{serial}_v8",
        "name": f"Boiler {name}",
        "optimistic": True,
        "temperature_unit": "C",
        "min_temp": 20,
        "max_temp": 70,
        "current_temperature_topic": f"P/{serial}/STATUS",
        "current_temperature_template": "{{ value_json.T_Avg | float }}",
        "temperature_state_topic": f"P/{serial}/STATUS",
        "temperature_state_template": "{{ value_json.T_SetPoint | float }}",
        "temperature_command_topic": f"P/{serial}/CMD/SET_STATUS",
        "temperature_command_template": "{\"Cmd\":\"9\",\"T_SetPoint\":\"{{ value | int }}\"}",

        "mode_state_topic": f"P/{serial}/STATUS",
        "mode_state_template": (
            "{% set cmd = value_json.Cmd | int %}"
            "{% if cmd == 9 %}performance"                # Manual
            "{% elif cmd == 3 %}eco"                     # Auto
            "{% elif (cmd // 64) % 2 == 1 %}electric"     # Holiday (Bit 6 / Val 64)
            "{% elif cmd == 17 %}auto"              # Eco (Learning)
            "{% else %}off{% endif %}"                    # Off
        ),
        "modes": ["off", "eco", "performance", "electric", "auto"],
        "mode_command_topic": f"P/{serial}/CMD/SET_STATUS",
        "mode_command_template": (
            "{% if value == 'performance' %}{\"Cmd\":\"9\",\"T_SetPoint\":\"60\"}"
            "{% elif value == 'eco' %}{\"Cmd\":\"3\"}"
            "{% elif value == 'electric' %}{\"Cmd\":\"65\",\"Time_Back_Cmd\":\"43200\"}" # 30 days default
            "{% elif value == 'auto' %}{\"Cmd\":\"17\"}"
            "{% else %}{\"Cmd\":\"16\"}{% endif %}"
        ),
        "device": {
            "identifiers": [f"thermowatt_{serial}"],
            "manufacturer": "Thermowatt",
            "name": f"Boiler {name}"
        }
    }
    local_client.publish(discovery_topic, json.dumps(payload), retain=True)


# --- 2. CALLBACKS ---

def on_aws_message(client, userdata, msg):
    """AWS -> Local (Status Updates)"""
    print(f"📡 AWS Status Update [{msg.topic}]")
    local_client.publish(msg.topic, msg.payload)

def on_local_message(client, userdata, msg):
    """Local -> AWS (Commands)"""
    try:
        # Extract serial from topic: P/SERIAL/CMD/SET_STATUS
        parts = msg.topic.split('/')
        if len(parts) >= 2:
            sn = parts[1]
            if sn in aws_clients:
                print(f"📤 Bridging HA Command to AWS for {sn}")
                aws_clients[sn].publish(msg.topic, msg.payload)
    except Exception as e:
        print(f"❌ Local Bridge Error: {e}")

# --- 3. INITIALIZATION ---

local_client = mqtt.Client(CallbackAPIVersion.VERSION2)
if MQTT_USER and MQTT_PASS:
    local_client.username_pw_set(MQTT_USER, MQTT_PASS)

local_client.on_message = on_local_message

try:
    local_client.connect(MQTT_HOST, MQTT_PORT)
    local_client.loop_start()
    print("✅ Connected to Local HA Broker")
except Exception as e:
    print(f"❌ Local Broker Connection Failed: {e}")
    sys.exit(1)

heaters = get_heaters()
for h in heaters:
    sn = h['seriale']
    name = h['nome']
    
    # Discovery
    publish_ha_discovery(local_client, sn, name)
    
    # Setup unique AWS client per heater
    aws_c = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=f"HA_Bridge_{sn}")
    aws_c.tls_set(ca_certs="root.pem", certfile="client.crt", keyfile="client.key", tls_version=ssl.PROTOCOL_TLSv1_2)
    aws_c.on_message = on_aws_message
    aws_c.connect(AWS_HOST, AWS_PORT)
    aws_c.subscribe(f"P/{sn}/STATUS")
    aws_c.loop_start()
    
    # Register and Subscribe
    aws_clients[sn] = aws_c
    local_client.subscribe(f"P/{sn}/CMD/SET_STATUS")
    
    # Refresh status
    aws_c.publish(f"P/{sn}/CMD/GET_STATUS", payload="")
    print(f"🌉 Bridge active for: {name} ({sn})")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")
    for c in aws_clients.values():
        c.disconnect()
    local_client.disconnect()
