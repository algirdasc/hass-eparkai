# Your support
<a href="https://www.buymeacoffee.com/Ua0JwY9" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Intro
While [eparkai.lt](https://www.eparkai.lt/) does not offer any kind of API for remote solar power plant users, 
this Home Assistant (HA) component scrapes solar power generation data every hour and adds it as a sensor.

**This component is in testing stage! Any feedback or requests should be raised as an [issue](https://github.com/algirdasc/hass-eparkai/issues)**.

# Installation

### HACS
1. Navigate to HACS Integrations
2. Click `Custom repositories`
3. Paste repository URL `https://github.com/algirdasc/hass-eparkai` to `Repository` field
4. Choose `Integration` category
5. Click `Add`
6. Install & configure component 
7. Restart HA

### Native

1. Upload `custom_components` directory to your HA `config` directory
2. Configure component
3. Restart HA

# Configuration

1. Add entry to `configuration.yaml`:
```yaml
eparkai:
  username: your_username
  password: your_password
  client_id: 12345
```
2. Add new sensor:
```yaml
- platform: eparkai
  power_plant_id: 123456789
```
3. Restart Home Assistant
4. Add new sensor `sensor.eparkai_123456789` to your [Energy dashboard](https://my.home-assistant.io/redirect/config_energy/)

### Getting client and generation IDs

1. Login to your eParkai.lt account
2. Go to your generation page
3. Look to your browsers address bar - you'll see something like `eparkai.lt/user/12345/generation`. That `12345` is your `client_id`.
4. Now open source code of the page and look for `generation_electricity`, option value is your `power_plant_id`.

# TODO

 - [ ]  Add more logging
 - [ ]  Automatically add all power plants as a sensors
 - [ ]  UI config flow
 - [ ]  History import