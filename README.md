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
6. Install & configure component (see Configuration)
7. Restart HA

### Native

1. Upload `custom_components` directory to your HA `config` directory
2. Configure component (see Configuration)
3. Restart HA

# Configuration

| Name                          |  Type  | Default | Description                                                                     |
|-------------------------------|:------:|:-------:|---------------------------------------------------------------------------------|
| username ***(required)***     | string |         | eParkai.lt username / email                                                     |
| password ***(required)***     | string |         | eParkai.lt password                                                             |
| client_id ***(required)***    | string |         | Client ID. See *Getting client and generation IDs*                              |
| power_plants ***(required)*** |  dict  |         | Power plant name and power plant generation ID object (can be multiple)         |
| generation_percentage         |  int   |  `100`  | Reduce generation calculation by percentage (i.e: if generation tax is applied) |

1. Add entry to `configuration.yaml`, for example:
```yaml
eparkai:
  username: your_username
  password: your_password
  client_id: '12345'
  power_plants:
    My Power Plant: '123456'
    My Other Power Plant: '65431'
```
2. Restart Home Assistant
3. Add new statistic `eparkai:energy_generation_123456789` to your [Energy dashboard](https://my.home-assistant.io/redirect/config_energy/)

### Getting client and generation IDs

1. Login to your eParkai.lt account
2. Go to your generation page
3. Look to your browsers address bar - you'll see something like `eparkai.lt/user/12345/generation`. That `12345` is your `client_id`.
4. Now open source code of the page and look for `generation_electricity`, option value is your `power_plant_id`.

# TODO

 - [ ]  Test with multiple power plants
 - [x]  Add more logging
 - [x]  History import
 - [x]  Add generation percentage deduction (as a tax calculation)
 