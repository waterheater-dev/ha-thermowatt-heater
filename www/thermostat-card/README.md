# Thermowatt Thermostat Card

A standalone custom Lovelace card for Home Assistant that displays and controls thermostat and water heater entities. This card is designed specifically for Thermowatt water heaters but works with any `climate` or `water_heater` entity.

## Features

- **Temperature Display & Control**: Visual circular slider for setting target temperature
- **Mode Selection**: Support for all operation modes (Off, Eco, Manual, Auto, Holiday)
- **Real-time Updates**: Automatically updates when entity state changes
- **Theme Support**: Respects Home Assistant themes
- **Responsive Design**: Adapts to card size automatically
- **Water Heater & Climate Support**: Works with both entity types

## Installation

### Step 1: Copy the Card File

Copy `thermowatt-thermostat-card.js` to your Home Assistant `www` directory:

```bash
# If using Home Assistant OS or Supervised
# The www directory is typically at: /config/www/

cp thermowatt-thermostat-card.js /config/www/
```

Or if you're accessing via Samba/network share, copy it to the `www` folder in your Home Assistant configuration directory.

### Step 2: Add as Lovelace Resource

1. Go to **Settings** → **Dashboards** → **Resources** (or **Developer Tools** → **Resources**)
2. Click **+ ADD RESOURCE** (bottom right)
3. Enter the URL: `/local/thermowatt-thermostat-card.js`
4. Set the resource type to **JavaScript Module**
5. Click **CREATE**

### Step 3: Use in Your Dashboard

Add the card to your Lovelace dashboard:

**Via YAML:**
```yaml
type: custom:thermowatt-thermostat-card
entity: water_heater.thermowatt_boiler_12345
name: "My Boiler"
theme: default  # Optional
```

**Via UI:**
1. Edit your dashboard
2. Click **+ ADD CARD**
3. Scroll down and select **Custom: Thermowatt Thermostat Card**
4. Select your entity
5. Configure as needed

## Configuration

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `entity` | string | **Required** | Entity ID (climate or water_heater) |
| `name` | string | Entity name | Custom name for the card |
| `theme` | string | default | Theme to apply to the card |

## Example Configuration

```yaml
type: custom:thermowatt-thermostat-card
entity: water_heater.thermowatt_boiler_abc123
name: "Boiler"
theme: default
```

## How It Works

This card uses Home Assistant's built-in temperature control components (`ha-state-control-water-heater-temperature` and `ha-state-control-climate-temperature`) which are already available in your running Home Assistant instance. This means:

- ✅ No compilation needed
- ✅ No external dependencies
- ✅ Uses native HA components for consistent UI
- ✅ Automatically gets updates when HA updates

## Customization

The card source code is in `thermowatt-thermostat-card.js`. You can customize:

- Card styling and layout
- Temperature control behavior
- Additional features or indicators
- Thermowatt-specific enhancements

## File Structure

```
www/thermostat-card/
├── thermowatt-thermostat-card.js  # Standalone card (use this)
├── hui-thermostat-card.ts         # Original HA source (reference)
└── README.md                      # This file
```

## Troubleshooting

**Card not showing:**
- Make sure the file is in `/config/www/`
- Verify the resource is added and type is "JavaScript Module"
- Check browser console for errors
- Clear browser cache

**Entity not found:**
- Verify the entity ID is correct
- Make sure the entity is a `climate` or `water_heater` entity
- Check that the entity is available in Home Assistant

**Temperature control not working:**
- Ensure the entity supports temperature control
- Check entity attributes: `min_temp`, `max_temp`, `temperature`
- Verify you have permission to call services on the entity

## License

This card is based on Home Assistant's thermostat card and is licensed under the Apache License 2.0.

## References

- [Home Assistant Custom Cards Documentation](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/)
- [Lovelace Card Types](https://www.home-assistant.io/lovelace/types/)
- [Water Heater Integration](https://www.home-assistant.io/integrations/water_heater/)
