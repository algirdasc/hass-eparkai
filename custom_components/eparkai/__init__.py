import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_ID,
    UnitOfEnergy
)

from .coordinator import EParkaiCoordinator
from .eparkai_client import EParkaiClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eparkai"

CONF_POWER_PLANT_ID = "generation_id"
CONF_PERCENTAGE = "percentage"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Optional(CONF_PERCENTAGE): vol.All(int, vol.Range(min=0, max=100))
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN] = EParkaiCoordinator(hass, EParkaiClient(
        username=config[DOMAIN][CONF_USERNAME],
        password=config[DOMAIN][CONF_PASSWORD],
        client_id=config[DOMAIN][CONF_CLIENT_ID],
        percentage=config[DOMAIN][CONF_PERCENTAGE]
    ))

    return True
