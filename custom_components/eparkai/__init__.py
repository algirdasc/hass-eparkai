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

CONF_GENERATION_ID = "generation_id"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
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
        client_id=config[DOMAIN][CONF_CLIENT_ID]
    ))

    return True



# def _generate_mean_statistics(
#         start: datetime, end: datetime, init_value: float, max_diff: float
# ) -> list[StatisticData]:
#     statistics: list[StatisticData] = []
#     mean = init_value
#     now = start
#     while now < end:
#         mean = mean + random() * max_diff - max_diff / 2
#         statistics.append(
#             {
#                 "start": now,
#                 "mean": mean,
#                 "min": mean - random() * max_diff,
#                 "max": mean + random() * max_diff,
#             }
#         )
#         now = now + timedelta(hours=1)
#
#     return statistics
#
#
# async def _insert_statistics(hass: HomeAssistant) -> None:
#     now = dt_util.now()
#     yesterday = now - timedelta(days=1)
#     yesterday_midnight = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
#     today_midnight = yesterday_midnight + timedelta(days=1)
#
#     metadata = {
#         "source": DOMAIN,
#         "name": None,
#         "statistic_id": "sensor.eparkai_4419234",
#         "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
#         "has_mean": True,
#         "has_sum": False,
#     }
#     statistics = _generate_mean_statistics(yesterday_midnight, today_midnight, 15, 1)
#     async_import_statistics(hass, metadata, statistics)
