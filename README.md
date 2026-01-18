# Thermowatt Smart Boiler Bridge for Home Assistant

This add-on allows you to integrate Thermowatt-based smart water heaters into Home Assistant using MQTT. It bridges the gap between the Thermowatt cloud and your local Home Assistant instance.

[![Open your Home Assistant instance and show the add-on store with a specific repository pre-filled.](https://my.home-assistant.io/badges/add_addon_repository.svg)](https://my.home-assistant.io/redirect/add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FYOUR_USERNAME%2Fha-thermowatt-boiler)

## Features

- **Real-time Monitoring**: Track current water temperature (`T_Avg`).
- **Full Control**: Set target temperatures and toggle between Manual/Auto modes.
- **MQTT Discovery**: Automatically creates a "Water Heater" device in Home Assistant.
- **Diagnostic Sensors**: Monitor errors and system status.

## Installation

1. Click the **Add Repository** button above, or manually add `https://github.com/YOUR_USERNAME/ha-thermowatt-boiler` to your Home Assistant Add-on Store.
2. Install the **Thermowatt Smart Boiler** add-on.
3. Configure your Thermowatt account credentials in the **Configuration** tab.
4. Start the add-on.

## Configuration

```yaml
email: "your-email@example.com"
password: "your-password"
```
