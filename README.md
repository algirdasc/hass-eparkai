# Your support
<a href="https://www.buymeacoffee.com/Ua0JwY9" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Intro
While [eparkai.lt](https://www.eparkai.lt/) does not offer any kind of API for remote solar power plant users, 
this Home Assistant (HA) component scrapes solar power generation data every hour and adds it as a sensor.  

**This component is in testing stage! Any feedback or requests should be raised as [issue](https://github.com/algirdasc/hass-eparkai/issues)**.

# Installation

### HACS
- Navigate to HACS Integrations
- Click `Custom repositories`
- Paste repository URL `https://github.com/algirdasc/hass-eparkai` to `Repository` field
- Choose `Integration` category
- Click `Add`
- Install & configure component 
- Restart HA

### Native

- Upload `custom_components` directory to your HA `config` directory
- Configure component
- Restart HA

# Configuration

- Add entry to `configuration.yaml`:
```yaml
eparkai:
  username: your_username
  password: your_password
  client_id: 12345
```
- Add new sensor:
```yaml
- platform: eparkai
  generation_id: 123456789
```
- Restart Home Assistant
- Add new sensor `sensor.eparkai_123456789` to your [Energy dashboard](https://my.home-assistant.io/redirect/config_energy/)