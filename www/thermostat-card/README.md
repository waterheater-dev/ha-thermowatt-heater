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

### Step 1: Download the Card File

**Download from GitHub:**
1. Go to: https://github.com/waterheater-dev/ha-thermowatt-heater
2. Navigate to `www/thermostat-card/thermowatt-thermostat-card.js`
3. Click the **Raw** button (top right)
4. Right-click → **Save As** → save as `thermowatt-thermostat-card.js`

**Direct download link:**  
[thermowatt-thermostat-card.js](https://raw.githubusercontent.com/waterheater-dev/ha-thermowatt-heater/main/www/thermostat-card/thermowatt-thermostat-card.js)

### Step 2: Copy to Home Assistant

You need to copy the file to your Home Assistant's `www` directory (`/config/www/`). Choose the method that works best for you:

**Method A: File Editor Add-on (Recommended)**
1. Install **File Editor** add-on if needed (Settings → Add-ons → Add-on Store)
2. Open File Editor
3. Navigate to `/config/www/` (create the `www` folder if it doesn't exist)
4. Click **Upload** or create new file `thermowatt-thermostat-card.js`
5. Paste the file contents and save

**Method B: Samba Share**
1. Enable **Samba share** add-on (Settings → Add-ons)
2. Access `\\homeassistant.local\config` from Windows or `smb://homeassistant.local/config` from Mac
3. Navigate to `www` folder (create if needed)
4. Copy `thermowatt-thermostat-card.js` into it

**Method C: SSH/Command Line**
```bash
# Create www directory if it doesn't exist
mkdir -p /config/www

# Copy the file (adjust the source path to where you downloaded it)
cp /path/to/downloaded/thermowatt-thermostat-card.js /config/www/
```

**Method D: Using Home Assistant Terminal Add-on**
1. Install **Terminal & SSH** add-on
2. Open terminal
3. Run:
   ```bash
   mkdir -p /config/www
   # Then use wget or curl to download directly:
   wget -O /config/www/thermowatt-thermostat-card.js https://raw.githubusercontent.com/waterheater-dev/ha-thermowatt-heater/main/www/thermostat-card/thermowatt-thermostat-card.js
   ```

### Step 3: Add as Lovelace Resource

1. In Home Assistant, go to **Settings** → **Dashboards** → **Resources**
   - Alternative path: **Developer Tools** → **Resources** tab
2. Click the **+ ADD RESOURCE** button (bottom right corner)
3. In the URL field, enter: `/local/thermowatt-thermostat-card.js`
   - ⚠️ Important: The URL must start with `/local/` (not `/www/` or `/config/www/`)
4. Set the resource type dropdown to **JavaScript Module**
5. Click **CREATE**
6. **Refresh your browser** (Ctrl+F5 on Windows/Linux, Cmd+Shift+R on Mac)

**Verify it's added:** You should see `thermowatt-thermostat-card.js` in your resources list.

### Step 4: Use in Your Dashboard

Add the card to your Lovelace dashboard:

**Via YAML:**
```yaml
type: custom:thermowatt-thermostat-card
entity: water_heater.thermowatt_boiler_12345
name: "My Boiler"
theme: default  # Optional
```

**Via UI:**
1. Go to your dashboard and click the **three dots** (⋮) → **Edit Dashboard**
2. Click **+ ADD CARD** (or click **+** in an empty spot)
3. Scroll down in the card picker and look for **Thermowatt Thermostat Card** or **Custom: Thermowatt Thermostat Card**
   - ⚠️ **If you don't see it:** Try adding it via YAML first (see below), then it should appear in future card additions
   - Make sure you completed Step 3 and **hard refreshed** your browser (Ctrl+F5 or Cmd+Shift+R)
4. Select your water heater entity from the dropdown
5. Optionally set a custom name
6. Click **SAVE**

**Alternative: Add via YAML Editor (If card doesn't appear in UI):**
1. Go to your dashboard → **three dots** (⋮) → **Edit Dashboard**
2. Click **three dots** on any card → **Edit Card** → Switch to **YAML mode** (top right)
3. Or click **three dots** → **Raw configuration editor**
4. Add the card configuration:
   ```yaml
   type: custom:thermowatt-thermostat-card
   entity: water_heater.thermowatt_boiler_12345
   name: "My Boiler"
   ```
5. Save and refresh

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

**Card doesn't appear in card picker:**
- ✅ Verify the file is in `/config/www/thermowatt-thermostat-card.js` (not in a subfolder)
- ✅ Check that the resource is added: Settings → Dashboards → Resources
- ✅ Make sure resource URL is exactly `/local/thermowatt-thermostat-card.js`
- ✅ Verify resource type is set to **JavaScript Module**
- ✅ **Hard refresh your browser** (Ctrl+F5 on Windows/Linux, Cmd+Shift+R on Mac)
- ✅ Clear browser cache completely
- ✅ Check browser console (F12 → Console tab) for JavaScript errors
- ✅ **Workaround:** Add the card via YAML mode first (see Step 4 instructions above), then it may appear in future UI additions
- ✅ Try restarting Home Assistant if nothing else works

**Card shows but displays "Entity not found":**
- ✅ Verify the entity ID is correct (check Settings → Devices & Services → MQTT)
- ✅ Make sure the entity is a `climate` or `water_heater` entity
- ✅ Check that the Thermowatt addon is running and has discovered your device
- ✅ Wait a few minutes after starting the addon for entities to appear

**Temperature control not working:**
- ✅ Ensure the entity supports temperature control
- ✅ Check entity attributes in Developer Tools → States
- ✅ Verify you have permission to call services on the entity
- ✅ Check addon logs for any MQTT errors

**Still having issues?**
- Check the browser console (F12 → Console tab) for error messages
- Verify file permissions: the file should be readable by Home Assistant
- Try removing and re-adding the resource
- Make sure you're using the latest version of the card file

## License

This card is based on Home Assistant's thermostat card and is licensed under the Apache License 2.0.

## References

- [Home Assistant Custom Cards Documentation](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/)
- [Lovelace Card Types](https://www.home-assistant.io/lovelace/types/)
- [Water Heater Integration](https://www.home-assistant.io/integrations/water_heater/)
