import sys, json, time, uuid, os, requests, urllib3, ssl
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else None
CONFIG_FILE = "/data/thermowatt_config.json" if os.path.exists("/data") else "thermowatt_config.json"
MQTT_HOST = os.getenv("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASSWORD")

# AWS IoT MQTT Configuration
AWS_HOST = "a29wru6dvi3p6q-ats.iot.eu-west-1.amazonaws.com"
AWS_PORT = 8883
# Certificates are copied to root in Dockerfile
AWS_ROOT_CA = "/root.pem"
AWS_CERT = "/client.crt"
AWS_KEY = "/client.key"

class MyThermowattBridge:
    API_KEY = "YVjArWssxKH631jv1dnnWOTr6gijsSAGz7rQJ4hJoUNRffxYvbQaMbePBEZalena"
    BASE_URL = "https://myapp-connectivity.com/api/v1"

    def __init__(self):
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            "app": "MyThermowatt", "platform": "iOS", "version": "3.14",
            "x-api-key": self.API_KEY, "lang": "en"
        })
        self.mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2)
        if MQTT_USER: self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.aws_clients = {}  # Registry for AWS MQTT clients per device

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure devices structure exists
                if 'devices' not in config:
                    config['devices'] = {}
                return config
        return {"device_uuid": str(uuid.uuid4()), "access_token": None, "refresh_token": None, "devices": {}}

    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f)

    def _update_auth(self, access, refresh):
        self.config.update({"access_token": access, "refresh_token": refresh})
        self.session.headers.update({"Authorization": f"Bearer {access}"})
        self._save_config()

    def login(self):
        payload = {"username": EMAIL, "password": PASSWORD, "device_id": self.config["device_uuid"]}
        r = self.session.post(f"{self.BASE_URL}/login", json=payload, verify=False)
        r.raise_for_status()
        res = r.json()['result']
        self._update_auth(res['accessToken'], res['refreshToken'])

    def refresh_session(self):
        payload = {"username": EMAIL, "refreshToken": self.config["refresh_token"]}
        r = self.session.post(f"{self.BASE_URL}/refresh", json=payload, verify=False)
        if r.status_code == 200:
            res = r.json()['result']
            self._update_auth(res['accessToken'], res['refreshToken'])
            return True
        return False

    def request(self, method, endpoint, **kwargs):
        url = f"{self.BASE_URL}{endpoint}"
        resp = self.session.request(method, url, verify=False, **kwargs)
        if resp.status_code == 401 and self.refresh_session():
            return self.session.request(method, url, verify=False, **kwargs)
        return resp

    # --- AWS MQTT BRIDGE CALLBACKS ---
    def on_aws_message(self, client, userdata, msg):
        """AWS -> Local (Status Updates)"""
        try:
            print(f"📡 AWS Status Update [{msg.topic}]")
            # Forward AWS status directly to local HA MQTT
            self.mqtt_client.publish(msg.topic, msg.payload, retain=True)
        except Exception as e:
            print(f"❌ AWS Bridge Error: {e}")

    # --- MQTT HANDLING ---
    def publish_discovery(self, serial, name):
        topic = f"homeassistant/water_heater/{serial}/config"
        payload = {
            "unique_id": f"thermowatt_{serial}_v314",
            "name": f"Boiler {name}",
            "temp_unit": "C", 
            "min_temp": 20, 
            "max_temp": 75,
            "optimistic": True,  
            "current_temperature_topic": f"P/{serial}/STATUS",
            "current_temperature_template": "{{ value_json.T_Avg | default(0) | float }}",
            "temperature_state_topic": f"P/{serial}/STATUS",
            "temperature_state_template": "{{ value_json.T_SetPoint | default(0) | float }}",
            "temperature_command_topic": f"P/{serial}/CMD/TEMP",
            "mode_state_topic": f"P/{serial}/STATUS",
            "mode_state_template": (
                "{% set cmd = value_json.Cmd | default(0) | int %}"
                "{% if cmd == 9 %}Manual"
                "{% elif cmd == 3 %}Eco"
                "{% elif cmd == 17 %}Auto"
                "{% elif cmd == 65 %}Holiday"
                "{% elif cmd == 16 %}off"
                "{% else %}Off{% endif %}" 
            ),
            "mode_command_topic": f"P/{serial}/CMD/MODE",
            "modes": ["Off", "Eco", "Manual", "Auto", "Holiday"],
            "device": {"identifiers": [f"tw_{serial}"], "manufacturer": "Thermowatt", "name": name}
        }
        self.mqtt_client.publish(topic, json.dumps(payload), retain=True)

    def on_mqtt_message(self, client, userdata, msg):
        """Local HA -> REST API (Commands)"""
        try:
            payload = msg.payload.decode()
            # Extract serial from topic: P/SERIAL/CMD/...
            parts = msg.topic.split('/')
            if len(parts) < 2:
                return
            sn = parts[1]
            
            # Find device config or use default
            device_config = self.config.get('devices', {}).get(sn, {})
            if not device_config:
                print(f"⚠️  Unknown device serial: {sn}")
                return
            
            # Set serial in session headers for REST API
            self.session.headers.update({"seriale": sn})
            
            # Use the "favorite" temp if it exists, otherwise default 60
            current_fav = device_config.get("last_setpoint", 60)

            if f"P/{sn}/CMD/TEMP" in msg.topic:
                temp = int(float(payload))
                print(f"[CMD] Setting Temperature to {temp}C for {sn}...")
                self.request("POST", "/manual", json={"T_SetPoint": temp})
                device_config["last_setpoint"] = temp
                self.config['devices'][sn] = device_config
                # Force HA to show this temperature immediately
                self._inject_fake_status(sn, {"T_SetPoint": str(temp)})
            
            elif f"P/{sn}/CMD/MODE" in msg.topic:
                print(f"[CMD] Setting Mode to {payload} for {sn}...")
                if payload == "Manual":
                    self.request("POST", "/manual", json={"T_SetPoint": current_fav})
                    self._inject_fake_status(sn, {"Cmd": "9", "T_SetPoint": str(current_fav)})
                elif payload == "Eco":
                    self.request("POST", "/eco", headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "3"})
                elif payload == "Auto":
                    self.request("POST", "/auto", headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "17"})
                elif payload == "Holiday":
                    import datetime
                    # 1. Calculate future date (1 month)
                    future_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    print(f"[CMD] Setting Holiday Mode until {future_date} for {sn}...")
                    # 2. Issue the API command
                    resp = self.request("POST", "/holiday", json={"end_date": future_date})
                    # 3. Immediate state injection so HA doesn't flicker
                    self._inject_fake_status(sn, {"Cmd": "65"})
                elif payload == "Off":
                    print(f"[CMD] Turning Boiler OFF for {sn}...")
                    resp = self.request("POST", "/off", headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "16"})
                    if resp:
                        print(f"[SUCCESS] Boiler {sn} is now OFF: {resp.text}")
            self._save_config()
        except Exception as e:
            print(f"MQTT Cmd Error: {e}")

    def _inject_fake_status(self, serial, overrides):
        """Immediately updates HA state to prevent flipping while cloud syncs """
        try:
            # Get the base status to preserve T_Avg and other fields
            self.session.headers.update({"seriale": serial})
            status = self.request("GET", "/status").json()
            # Convert REST API format to AWS MQTT format (remove 'result' wrapper)
            mqtt_status = status.get('result', {})
            for k, v in overrides.items():
                mqtt_status[k] = str(v)  # API uses strings for values 
            self.mqtt_client.publish(f"P/{serial}/STATUS", json.dumps(mqtt_status), retain=True)
        except Exception as e:
            print(f"⚠️  Status injection failed for {serial}: {e}")

    def setup_aws_client(self, serial, name):
        """Create and configure AWS MQTT client for a device"""
        try:
            aws_client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=f"HA_Bridge_{serial}")
            aws_client.tls_set(
                ca_certs=AWS_ROOT_CA,
                certfile=AWS_CERT,
                keyfile=AWS_KEY,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            aws_client.on_message = self.on_aws_message
            aws_client.connect(AWS_HOST, AWS_PORT, 60)
            aws_client.subscribe(f"P/{serial}/STATUS")
            aws_client.loop_start()
            
            # Request initial status from AWS
            aws_client.publish(f"P/{serial}/CMD/GET_STATUS", payload="")
            
            self.aws_clients[serial] = aws_client
            print(f"✅ AWS MQTT connected for {name} ({serial})")
            return True
        except Exception as e:
            print(f"❌ AWS MQTT connection failed for {serial}: {e}")
            return False

    def run(self):
        print("--- BOOT SEQUENCE START ---")
        
        # 1. Credentials Check
        if not EMAIL or not PASSWORD:
            print("FAILED: Step 1 - Missing EMAIL/PASSWORD in addon config.")
            sys.exit(1)
        print("OK: Step 1 - Credentials present.")

        # 2 & 3. MQTT Check
        try:
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
            print("OK: Step 2 & 3 - Connected and authenticated with local MQTT.")
        except Exception as e:
            print(f"FAILED: Step 2/3 - MQTT Connection Error: {e}")
            sys.exit(1)

        # 4. Backend Login
        try:
            self.login()
            print("OK: Step 4 - Logged in to Thermowatt backend.")
        except Exception as e:
            print(f"FAILED: Step 4 - Backend authentication failed: {e}")
            sys.exit(1)

        # 5. Discover Heaters
        try:
            r = self.request("GET", "/user-info")
            devices = r.json().get('result', {}).get('termostati', [])
            if not devices: raise Exception("Zero devices returned")
            
            # Initialize devices config if needed
            if 'devices' not in self.config:
                self.config['devices'] = {}
            
            print(f"OK: Step 5 - Found {len(devices)} thermostats.")
            
            # Setup each device
            for dev in devices:
                serial = dev['seriale']
                name = dev.get('nome', 'Boiler')
                
                # Store device info
                if serial not in self.config['devices']:
                    self.config['devices'][serial] = {"name": name, "last_setpoint": 60}
                else:
                    self.config['devices'][serial]["name"] = name
                
                # Publish HA discovery
                self.publish_discovery(serial, name)
                
                # Setup AWS MQTT client for this device
                if not self.setup_aws_client(serial, name):
                    print(f"⚠️  Warning: AWS MQTT setup failed for {serial}, continuing...")
                
                # Subscribe to local MQTT commands for this device
                self.mqtt_client.subscribe(f"P/{serial}/CMD/#")
                
                print(f"🌉 Bridge active for: {name} ({serial})")
            
            self._save_config()
            
        except Exception as e:
            print(f"FAILED: Step 5 - Could not retrieve thermostat list: {e}")
            sys.exit(1)

        print("OK: Step 6 - Booted successfully.")
        
        # Setup local MQTT message handler for commands
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.loop_start()
        
        print("OK: Step 7 - AWS MQTT bridge active. Status updates via MQTT, commands via REST API.")
        
        # Keep the main loop running (no polling needed - status comes from AWS MQTT)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
            for aws_client in self.aws_clients.values():
                aws_client.disconnect()
            self.mqtt_client.disconnect()

if __name__ == "__main__":
    bridge = MyThermowattBridge()
    bridge.run()
