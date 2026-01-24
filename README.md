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
