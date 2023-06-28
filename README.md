# Your support
This open-source project is developed in my free time. 
Your donation would help me dedicate more time and resources to improve project, add new features, fix bugs, 
as well as improve motivation and helps me understand, that this project is useful not only for me, but for more users.

<a href="https://www.buymeacoffee.com/Ua0JwY9" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Intro
While [eparkai.lt](https://www.eparkai.lt/) does not offer any kind of API for remote solar power plant users, 
this Home Assistant (HA) component scrapes solar power generation data every hour and imports to long-term HA statistics.

### Disclaimer

**This component is in testing stage! Errors or miscalculation, breaking changes should be expected! Any feedback or requests should be raised as an [issue](https://github.com/algirdasc/hass-eparkai/issues)**.

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

### Integration

| Name         |  Type  | Required | Default | Description                                                       |
|--------------|:------:|:--------:|:-------:|-------------------------------------------------------------------|
| username     | string |   yes    |         | eParkai.lt username / email                                       |
| password     | string |   yes    |         | eParkai.lt password                                               |
| client_id    | string |   yes    |         | Client ID (see below *How to get your client and generation IDs*) |
| power_plants |  list  |   yes    |         | List of power plants                                              |

### Power plant

| Name                  |  Type  | Required | Default | Description                                                                                                                   |
|-----------------------|:------:|:--------:|:-------:|-------------------------------------------------------------------------------------------------------------------------------|
| name                  | string |   yes    |         | Name of power plant (will be visible in energy dashboard)                                                                     |
| id                    | string |   yes    |         | Power plant generation ID (see below *How to get your client and generation IDs*)                                             |
| object_address        | string |    no    |         | Power plant object address, required when having more than one object (see below *How to get your client and generation IDs*) |
| statistics_id_suffix  | string |    no    |         | Unique statistics id. Useful when using same power plant generation id with percentage calculation                            |
| generation_percentage |  int   |    no    |  `100`  | Reduce generation calculation by percentage (i.e: if generation tax is applied)                                               |


### Example:
```yaml
eparkai:
  username: your_username
  password: your_password
  client_id: '12345'
  power_plants:
    - name: My Power Plant
      id: 123456
      object_address: Some street 1
    - name: My Other Power Plant
      id: 654321
      object_address: Some other street 2
```

### Object address
Object address is mandatory if you have multiple objects. This should be set exactly as is set in eparkai.lt site. 

### Generation percentage
If you have chosen power plant generation tax which reduces your generation, you might want to see taxed power and owned 
power separately. You can do this by adding same power plant twice and setting `generation_percentage` and `statistics_id_suffix` parameters.
Example:
```yaml
...
    - name: Power plant with taxes (TAXED)
      id: 123456
      statistics_id_suffix: taxed
      generation_percentage: 12
    - name: Power plant with taxes (OWNED)
      id: 123456
      statistics_id_suffix: owned
      generation_percentage: 88
...
```
This way two separate statistics will be created: `eparkai:energy_generation_123456_taxed` and`eparkai:energy_generation_123456_owned`. 
When you add both to your energy dashboard, you will see your owned part as 88% and taxed part as 12% of all generated power separately as stacked column.
`statistics_id_suffix` must be set to create non-ambiguous ID and prevent overwriting statistics data.

### How to get your client and generation IDs

1. Login to your eParkai.lt account
2. Go to your generation page
3. Look to your browsers address bar - you'll see something like `eparkai.lt/user/XXXXX/generation`. That `XXXXX` is your `client_id`.
4. Now open source code of the page (CTRL+U)
5. Look for `generation_electricity`, option value is your `power_plant_id`
5. Look for `edit-address`, option value is your `object_address`

# TODO

 - [x]  Test with multiple power plants
 - [x]  Add more logging
 - [x]  History import
 - [x]  Add generation percentage deduction (as a tax calculation)
 