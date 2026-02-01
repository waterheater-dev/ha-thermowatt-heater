# Thermowatt Smart Boiler Bridge for Home Assistant

This add-on allows you to integrate Thermowatt-based smart water heaters into Home Assistant using MQTT. It bridges the gap between the Thermowatt cloud and your local Home Assistant instance.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fwaterheater-dev%2Fha-thermowatt-heater)

## Features

- **Real-time Monitoring**: Track current water temperature (`T_Avg`).
- **Full Control**: Set target temperatures and toggle between Manual/Auto modes.
- **MQTT Discovery**: Automatically creates a "Water Heater" device in Home Assistant.
- **Diagnostic Sensors**: Monitor errors and system status.

## Installation

1. Prerequisite: Install and start Mosquitto MQTT broker within Home Assistant.
2. Click the **Add Repository** button above, or manually add `https://github.com/waterheater-dev/ha-thermowatt-heater` to your Home Assistant Add-on Store.
3. Install the **Thermowatt Smart Boiler** add-on.
4. Configure your Thermowatt account credentials in the **Configuration** tab.
5. Start the add-on.

## Configuration

```yaml
email: "your-email@example.com"
password: "your-password"
```

## Dashboard

Once the add-on is running, a new entity will appear under your MQTT integration. We recommend using the Thermostat Card for the best experience.

### Custom Thermostat Card

This addon includes a standalone custom thermostat card that displays exactly like Home Assistant's default thermostat card, with added heating status indicator. The card supports both `climate` and `water_heater` entities and is perfect for controlling your Thermowatt boiler.

**Option 1: Use the Standalone Custom Card (Recommended)**

The custom card file is located in the addon repository at `www/thermostat-card/thermowatt-thermostat-card.js`. To install it:

#### Step 1: Download the Card File

1. Go to the [addon repository on GitHub](https://github.com/waterheater-dev/ha-thermowatt-heater)
2. Navigate to `www/thermostat-card/thermowatt-thermostat-card.js`
3. Click the **Raw** button to view the file
4. Right-click and **Save As** → save it as `thermowatt-thermostat-card.js`

Or download directly: [thermowatt-thermostat-card.js](https://raw.githubusercontent.com/waterheater-dev/ha-thermowatt-heater/main/www/thermostat-card/thermowatt-thermostat-card.js)

#### Step 2: Copy to Home Assistant

**Method A: Using File Editor Add-on (Easiest)**
1. Install the **File Editor** add-on if you haven't already
2. Open File Editor
3. Navigate to `/config/www/` folder
4. If the `www` folder doesn't exist, create it
5. Click **Upload** or create a new file named `thermowatt-thermostat-card.js`
6. Paste the contents of the downloaded file and save

**Method B: Using Samba Share**
1. Enable Samba share in Home Assistant (Settings → Add-ons → Samba share)
2. Access your Home Assistant via network share (e.g., `\\homeassistant.local\config`)
3. Navigate to the `www` folder (create it if it doesn't exist)
4. Copy `thermowatt-thermostat-card.js` into the `www` folder

**Method C: Using SSH**
1. Enable SSH add-on or use SSH access
2. Copy the file:
   ```bash
   # Create www directory if it doesn't exist
   mkdir -p /config/www
   
   # Copy the file (adjust path as needed)
   cp /path/to/thermowatt-thermostat-card.js /config/www/
   ```

#### Step 3: Add as Lovelace Resource

1. In Home Assistant, go to **Settings** → **Dashboards** → **Resources**
   - (Alternative: **Developer Tools** → **Resources** tab)
2. Click **+ ADD RESOURCE** button (bottom right)
3. Enter the URL: `/local/thermowatt-thermostat-card.js`
4. Set the resource type to **JavaScript Module**
5. Click **CREATE**
6. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)

#### Step 4: Use in Your Dashboard

**Via UI:**
1. Edit your dashboard (click the three dots → Edit Dashboard)
2. Click **+ ADD CARD**
3. Scroll down and look for **Thermowatt Thermostat Card** or **Custom: Thermowatt Thermostat Card**
   - ⚠️ **If you don't see it:** Use the YAML method below instead
4. Select your water heater entity
5. Configure name and other options
6. Click **SAVE**

**Via YAML (Always Works):**
1. Edit your dashboard → Click **three dots** on any card → **Raw configuration editor**
2. Or edit a card → Switch to **YAML mode** (top right)
3. Add the card configuration:
   ```yaml
   type: custom:thermowatt-thermostat-card
   entity: water_heater.thermowatt_boiler_12345
   name: "My Boiler"
   ```
4. Save and refresh

**Troubleshooting:**
- If the card doesn't appear, make sure the file is in `/config/www/` (not `/config/www/thermostat-card/`)
- Verify the resource URL is exactly `/local/thermowatt-thermostat-card.js`
- Clear browser cache and refresh
- Check browser console (F12) for any errors

**Option 2: Use Home Assistant's Built-in Card**

Home Assistant includes a thermostat card by default. Simply add it to your Lovelace dashboard:

```yaml
type: thermostat
entity: water_heater.thermowatt_boiler_12345
name: "My Boiler"
```

**Note:** The built-in card works great, but the custom card includes a heating status indicator (flame icon) that shows when the boiler is actively heating.

---

**Need Help?**

- See detailed installation guide: [`www/thermostat-card/README.md`](https://github.com/waterheater-dev/ha-thermowatt-heater/blob/main/www/thermostat-card/README.md)
- The card file is also available in the addon repository: `www/thermostat-card/thermowatt-thermostat-card.js`

## Troubleshooting

The add-on will log each step of its boot cycle, so that in case of a problem, you will be aware of exactly which step failed. A healthy log should look like this:

```code
s6-rc: info: service s6rc-oneshot-runner: starting
s6-rc: info: service s6rc-oneshot-runner successfully started
s6-rc: info: service fix-attrs: starting
s6-rc: info: service fix-attrs successfully started
s6-rc: info: service legacy-cont-init: starting
s6-rc: info: service legacy-cont-init successfully started
s6-rc: info: service legacy-services: starting
s6-rc: info: service legacy-services successfully started
[12:20:09] INFO: Starting Thermowatt Bridge for <email@example.com>...
--- BOOT SEQUENCE START ---
OK: Step 1 - Credentials present.
OK: Step 2 & 3 - Connected and authenticated with local MQTT.
OK: Step 4 - Logged in to Thermowatt backend.
OK: Step 5 - Found 1 thermostats. Using: Home
OK: Step 6 - Successfully fetched initial status.
OK: Step 7 - Booted successfully.
OK: Step 8 - Beginning 60s polling loop.
```

## Known to work on:

- **Home Assistant:**
  - _Installation method:_ `Home Assistant OS`
  - _Core:_ `2025.12.5`
  - _Supervisor:_ `2026.01.1`
  - _Operating System:_ `16.3`
  - _Frontend:_ `20251203.3`
- **Mosquitto MQTT Version:** `6.5.2`
- **MyThermowatt App Version:** `3.14`

Tip: Help others by adding your version here, if it works.

---

_Disclaimer: This project is not affiliated with or endorsed by Thermowatt or Ariston._

---

### Support my work

If this add-on saved you some frustration or made your home a bit smarter or helped someone avoid a cold shower, feel free to [buy me a beer on Ko-fi!](https://ko-fi.com/thermohacker)

[![support](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/thermohacker)
