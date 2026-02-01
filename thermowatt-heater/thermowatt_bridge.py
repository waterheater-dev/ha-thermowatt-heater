import sys, json, time, uuid, os, requests, urllib3
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

class MyThermowattBridge:
    API_KEY = "YVjArWssxKH631jv1dnnWOTr6gijsSAGz7rQJ4hJoUNRffxYvbQaMbePBEZalena"
    BASE_URL = "https://myapp-connectivity.com/api/v1"
    POLL_INTERVAL = 20  # seconds (matches their TimeBeforeNextRefresh)
    STATUS_LOG_INTERVAL = 300  # 5 minutes

    def __init__(self):
        self.config = self._load_config()
        # Create a SINGLE session instance - this preserves cookies from AWS load balancers
        self.session = requests.Session()
        self.mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2)
        if MQTT_USER: self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        # Polling state
        self.poll_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_status_log_time = time.time()
        self.rate_limit_backoff = 0  # 0 = no backoff, 1 = 20s, 2 = 40s, 3+ = 60s
        self.current_poll_interval = self.POLL_INTERVAL

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if 'devices' not in config:
                    config['devices'] = {}
                return config
        return {"device_uuid": str(uuid.uuid4()), "access_token": None, "refresh_token": None, "devices": {}}

    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f)

    def _reset_headers(self):
        """Reset headers like their ResetHeaders() - keeps Authorization, removes others, then adds app/platform/version/lang"""
        # Keep Authorization if it exists
        auth_header = self.session.headers.get("Authorization")
        
        # Clear all headers
        self.session.headers.clear()
        
        # Restore Authorization if it was there
        if auth_header:
            self.session.headers["Authorization"] = auth_header
        
        # Add required headers (exactly like their C# code)
        self.session.headers.update({
            "app": "MyThermowatt",
            "platform": "iOS",
            "version": "3.14",
            "lang": "en"
        })

    def _update_auth(self, access, refresh):
        self.config.update({"access_token": access, "refresh_token": refresh})
        self.session.headers["Authorization"] = f"Bearer {access}"
        self._save_config()

    def login(self):
        """Login using the SAME session instance to preserve cookies"""
        self._reset_headers()
        self.session.headers["x-api-key"] = self.API_KEY
        
        payload = {"username": EMAIL, "password": PASSWORD, "device_id": self.config["device_uuid"]}
        r = self.session.post(f"{self.BASE_URL}/login", json=payload, verify=False)
        r.raise_for_status()
        res = r.json()['result']
        self._update_auth(res['accessToken'], res['refreshToken'])

    def refresh_session(self):
        """Refresh token using the SAME session instance"""
        self._reset_headers()
        self.session.headers["x-api-key"] = self.API_KEY
        
        payload = {"username": EMAIL, "refreshToken": self.config["refresh_token"]}
        r = self.session.post(f"{self.BASE_URL}/refresh", json=payload, verify=False)
        if r.status_code == 200:
            res = r.json()['result']
            self._update_auth(res['accessToken'], res['refreshToken'])
            return True
        return False

    def request(self, method, endpoint, serial=None, **kwargs):
        """Make request using the SAME session instance - preserves cookies"""
        self._reset_headers()
        
        url = f"{self.BASE_URL}{endpoint}"
        if serial:
            self.session.headers["seriale"] = serial
        
        resp = self.session.request(method, url, verify=False, **kwargs)
        
        # Handle 401 - try refresh
        if resp.status_code == 401:
            if self.refresh_session():
                # Retry with refreshed token
                self._reset_headers()
                if serial:
                    self.session.headers["seriale"] = serial
                resp = self.session.request(method, url, verify=False, **kwargs)
        
        return resp

    def publish_discovery(self, serial, name):
        # Water Heater entity
        topic = f"homeassistant/water_heater/{serial}/config"
        payload = {
            "unique_id": f"thermowatt_{serial}_v314",
            "name": f"Boiler {name}",
            "temp_unit": "C", 
            "min_temp": 20, 
            "max_temp": 75,
            "optimistic": True,  
            "current_temperature_topic": f"P/{serial}/STATUS",
            "current_temperature_template": "{{ value_json.result.T_Avg | default(0) | float }}",
            "temperature_state_topic": f"P/{serial}/STATUS",
            "temperature_state_template": "{{ value_json.result.T_SetPoint | default(0) | float }}",
            "temperature_command_topic": f"P/{serial}/CMD/TEMP",
            "mode_state_topic": f"P/{serial}/STATUS",
            "mode_state_template": (
                "{% set cmd = value_json.result.Cmd | default(0) | int %}"
                "{% if cmd == 9 %}Manual"
                "{% elif cmd == 3 %}Eco"
                "{% elif cmd == 17 %}Auto"
                "{% elif cmd == 65 %}Holiday"
                "{% elif cmd == 16 %}off"
                "{% else %}Off{% endif %}" 
            ),
            "mode_command_topic": f"P/{serial}/CMD/MODE",
            "modes": ["Off", "Eco", "Manual", "Auto", "Holiday"],
            "json_attributes_topic": f"P/{serial}/STATUS",
            "json_attributes_template": "{{ value_json.result | tojson }}",
            "device": {"identifiers": [f"tw_{serial}"], "manufacturer": "Thermowatt", "name": name}
        }
        self.mqtt_client.publish(topic, json.dumps(payload), retain=True)
        
        # Binary Sensor for Heating Status (flame icon indicator)
        heating_topic = f"homeassistant/binary_sensor/{serial}/heating/config"
        heating_payload = {
            "unique_id": f"thermowatt_{serial}_heating",
            "name": f"Boiler {name} Heating",
            "state_topic": f"P/{serial}/STATUS",
            "value_template": "{{ (value_json.result.WaterHeaterSts | default(0) | int) & 1 != 0 }}",
            "device_class": "heat",
            "payload_on": "true",
            "payload_off": "false",
            "icon": "mdi:fire",
            "device": {
                "identifiers": [f"tw_{serial}"],
                "manufacturer": "Thermowatt",
                "name": name
            }
        }
        self.mqtt_client.publish(heating_topic, json.dumps(heating_payload), retain=True)

    def on_mqtt_message(self, client, userdata, msg):
        """Local HA -> REST API (Commands)"""
        try:
            payload = msg.payload.decode()
            parts = msg.topic.split('/')
            if len(parts) < 2:
                return
            sn = parts[1]
            
            device_config = self.config.get('devices', {}).get(sn, {})
            if not device_config:
                print(f"⚠️  Unknown device serial: {sn}")
                return
            
            current_fav = device_config.get("last_setpoint", 60)

            if f"P/{sn}/CMD/TEMP" in msg.topic:
                temp = int(float(payload))
                print(f"[CMD] Setting Temperature to {temp}C for {sn}...")
                self.request("POST", "/manual", serial=sn, json={"T_SetPoint": temp})
                device_config["last_setpoint"] = temp
                self.config['devices'][sn] = device_config
                self._inject_fake_status(sn, {"T_SetPoint": str(temp)})
            
            elif f"P/{sn}/CMD/MODE" in msg.topic:
                print(f"[CMD] Setting Mode to {payload} for {sn}...")
                
                if payload == "Manual":
                    self.request("POST", "/manual", serial=sn, json={"T_SetPoint": current_fav})
                    self._inject_fake_status(sn, {"Cmd": "9", "T_SetPoint": str(current_fav)})
                elif payload == "Eco":
                    self.request("POST", "/eco", serial=sn, headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "3"})
                elif payload == "Auto":
                    self.request("POST", "/auto", serial=sn, headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "17"})
                elif payload == "Holiday":
                    import datetime
                    future_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    print(f"[CMD] Setting Holiday Mode until {future_date} for {sn}...")
                    self.request("POST", "/holiday", serial=sn, json={"end_date": future_date})
                    self._inject_fake_status(sn, {"Cmd": "65"})
                elif payload == "Off":
                    print(f"[CMD] Turning Boiler OFF for {sn}...")
                    resp = self.request("POST", "/off", serial=sn, headers={"Content-Type": "text/plain"}, data="")
                    self._inject_fake_status(sn, {"Cmd": "16"})
                    if resp:
                        print(f"[SUCCESS] Boiler {sn} is now OFF: {resp.text}")
            self._save_config()
        except Exception as e:
            print(f"MQTT Cmd Error: {e}")

    def _inject_fake_status(self, serial, overrides):
        """Immediately updates HA state to prevent flipping while cloud syncs"""
        try:
            r = self.request("GET", "/status", serial=serial)
            status = r.json()
            mqtt_status = status.get('result', {})
            for k, v in overrides.items():
                mqtt_status[k] = str(v)
            # Compute and add heating status (bit 0 of WaterHeaterSts)
            water_heater_sts = int(mqtt_status.get('WaterHeaterSts', 0))
            mqtt_status['heating'] = (water_heater_sts & 1) != 0
            # Publish the full response format (with 'result' wrapper) to match HA templates
            self.mqtt_client.publish(f"P/{serial}/STATUS", json.dumps(status), retain=True)
        except Exception as e:
            print(f"⚠️  Status injection failed for {serial}: {e}")

    def poll_status(self, serial):
        """Poll status for a device - returns (success, status_code)"""
        try:
            r = self.request("GET", "/status", serial=serial)
            status_code = r.status_code
            
            if status_code == 200:
                # Parse JSON and add computed heating status
                status_data = r.json()
                if 'result' in status_data:
                    water_heater_sts = int(status_data['result'].get('WaterHeaterSts', 0))
                    # Heating is active if bit 0 is set (matches manufacturer's app logic)
                    status_data['result']['heating'] = (water_heater_sts & 1) != 0
                
                # Publish to MQTT with computed field
                self.mqtt_client.publish(f"P/{serial}/STATUS", json.dumps(status_data), retain=True)
                return (True, status_code)
            else:
                # Return status code for handling in main loop
                return (False, status_code)
        except Exception as e:
            print(f"Poll error for {serial}: {e}")
            return (False, None)

    def log_status_summary(self):
        """Log polling statistics every 5 minutes"""
        elapsed = time.time() - self.last_status_log_time
        if elapsed >= self.STATUS_LOG_INTERVAL:
            print(f"[STATUS] Polled {self.poll_count} times, got {self.success_count} x 200, {self.error_count} errors")
            self.poll_count = 0
            self.success_count = 0
            self.error_count = 0
            self.last_status_log_time = time.time()

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

        # 4. Backend Login (using the SAME session that will be used for polling)
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
            
            if 'devices' not in self.config:
                self.config['devices'] = {}
            
            print(f"OK: Step 5 - Found {len(devices)} thermostats.")
            
            for dev in devices:
                serial = dev['seriale']
                name = dev.get('nome', 'Boiler')
                
                if serial not in self.config['devices']:
                    self.config['devices'][serial] = {"name": name, "last_setpoint": 60}
                else:
                    self.config['devices'][serial]["name"] = name
                
                self.publish_discovery(serial, name)
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
        
        print(f"OK: Step 7 - Starting polling loop (interval: {self.POLL_INTERVAL}s).")
        
        # Main polling loop
        while True:
            try:
                rate_limited = False
                
                # Poll all devices
                for serial in self.config.get('devices', {}).keys():
                    self.poll_count += 1
                    success, status_code = self.poll_status(serial)
                    
                    if success:
                        self.success_count += 1
                        # Reset backoff on success
                        if self.rate_limit_backoff > 0:
                            self.rate_limit_backoff = 0
                            self.current_poll_interval = self.POLL_INTERVAL
                    else:
                        self.error_count += 1
                        if status_code == 429:
                            # Rate limited - implement exponential backoff
                            rate_limited = True
                            self.rate_limit_backoff += 1
                            if self.rate_limit_backoff == 1:
                                self.current_poll_interval = 20
                            elif self.rate_limit_backoff == 2:
                                self.current_poll_interval = 40
                            else:
                                self.current_poll_interval = 60  # Stick with 60s
                            print(f"[RATE LIMIT] 429 received, backing off to {self.current_poll_interval}s interval")
                            break  # Exit device loop, will sleep below
                        elif status_code is not None:
                            # Any other error - re-login
                            print(f"[ERROR] Got status {status_code}, re-logging in...")
                            try:
                                self.login()
                            except Exception as e:
                                print(f"[ERROR] Re-login failed: {e}")
                
                # Log status summary every 5 minutes
                self.log_status_summary()
                
                # Sleep for current interval (may be increased due to rate limiting)
                time.sleep(self.current_poll_interval)
                
            except KeyboardInterrupt:
                print("Stopping...")
                break
            except Exception as e:
                print(f"[ERROR] Polling loop error: {e}")
                # Try to re-login on any unexpected error
                try:
                    self.login()
                except Exception as e2:
                    print(f"[ERROR] Re-login failed: {e2}")
                time.sleep(self.current_poll_interval)
        
        self.mqtt_client.disconnect()

if __name__ == "__main__":
    bridge = MyThermowattBridge()
    bridge.run()
