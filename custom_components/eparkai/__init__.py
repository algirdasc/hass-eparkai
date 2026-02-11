import logging
from datetime import timedelta, datetime

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMetaData, StatisticData
from homeassistant.components.recorder.statistics import async_add_external_statistics, statistics_during_period
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_ID,
    UnitOfEnergy,
    EVENT_HOMEASSISTANT_STARTED,
)
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .eparkai_client import EParkaiClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eparkai"

CONF_POWER_PLANTS = "power_plants"
CONF_OBJECT_ADDRESS = "object_address"
CONF_GENERATION_PERCENTAGE = "generation_percentage"
CONF_STATISTICS_ID_SUFFIX = "statistics_id_suffix"

POWER_PLANT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ID): cv.string,
        vol.Optional(CONF_OBJECT_ADDRESS, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_STATISTICS_ID_SUFFIX, default=""): cv.string,
        vol.Optional(CONF_GENERATION_PERCENTAGE, default=100): vol.All(int, vol.Range(min=1, max=100)),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_POWER_PLANTS): cv.ensure_list(POWER_PLANT_SCHEMA),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, config[DOMAIN])

    session = async_get_clientsession(hass)
    client = EParkaiClient(
        session=session,
        username=config[DOMAIN][CONF_USERNAME],
        password=config[DOMAIN][CONF_PASSWORD],
        client_id=config[DOMAIN][CONF_CLIENT_ID],
    )

    async def async_import_generation(now: datetime) -> None:
        if hass.is_stopping:
            _LOGGER.debug("HA is stopping, skipping generation import")
            return

        try:
            _LOGGER.debug("Logging in to %s site", DOMAIN)
            await client.login()
        except Exception as e:
            _LOGGER.error("eParkai login error: %s", e)
            return

        for power_plant in config[DOMAIN][CONF_POWER_PLANTS]:
            _LOGGER.debug("Fetching generation data for %s", power_plant[CONF_NAME])
            try:
                await client.fetch_generation_data(
                    power_plant[CONF_ID],
                    power_plant[CONF_OBJECT_ADDRESS],
                    now,
                )
            except Exception as e:
                _LOGGER.error("eParkai fetch generation data error [%s]: %s", power_plant[CONF_NAME], e)
                continue

            _LOGGER.debug("Importing generation data for %s", power_plant[CONF_NAME])
            await async_insert_statistics(
                hass,
                power_plant,
                client.get_generation_data(power_plant[CONF_ID]),
            )
            _LOGGER.debug("Imported generation data for %s", power_plant[CONF_NAME])

    async def async_first_start(event: Event) -> None:
        await async_import_generation(datetime.now())

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, async_first_start)

    async_track_time_interval(hass, async_import_generation, timedelta(hours=1))

    return True


async def async_insert_statistics(hass: HomeAssistant, power_plant: dict, generation_data: dict) -> None:
    id_suffix = power_plant[CONF_STATISTICS_ID_SUFFIX] if CONF_STATISTICS_ID_SUFFIX in power_plant else ""
    statistic_id = f"{DOMAIN}:energy_generation_{power_plant[CONF_ID]}_{id_suffix}".strip("_")

    _LOGGER.debug("Statistic ID for %s is %s", power_plant[CONF_NAME], statistic_id)

    if not generation_data:
        _LOGGER.error("Received empty generation data for %s", statistic_id)
        return

    metadata = StatisticMetaData(
        has_mean=False,
        has_sum=True,
        mean_type=None,
        name=power_plant[CONF_NAME],
        source=DOMAIN,
        statistic_id=statistic_id,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    )

    statistics = await _async_get_statistics(hass, metadata, power_plant, generation_data)
    async_add_external_statistics(hass, metadata, statistics)


async def _async_get_statistics(
    hass: HomeAssistant,
    metadata: StatisticMetaData,
    power_plant: dict,
    generation_data: dict,
) -> list[StatisticData]:
    statistic_id = metadata["statistic_id"]
    statistics: list[StatisticData] = []
    generation_percentage = power_plant[CONF_GENERATION_PERCENTAGE]
    sum_ = None

    tz = dt_util.get_time_zone("Europe/Vilnius")

    for ts in sorted(generation_data):
        generated_kwh = generation_data[ts]
        dt_object = datetime.fromtimestamp(ts, tz=tz)

        if generation_percentage != 100:
            generated_percentage_kwh = generated_kwh * (generation_percentage / 100)
            _LOGGER.debug(
                "Applying generation percentage of %s%% for %s: %s kWh -> %s kWh",
                generation_percentage,
                statistic_id,
                generated_kwh,
                generated_percentage_kwh,
            )
            generated_kwh = generated_percentage_kwh

        if sum_ is None:
            sum_ = await get_yesterday_sum(hass, metadata, dt_object)

        sum_ += generated_kwh

        statistics.append(StatisticData(start=dt_object, state=generated_kwh, sum=sum_))

    return statistics


async def get_yesterday_sum(hass: HomeAssistant, metadata: StatisticMetaData, date: datetime) -> float:
    statistic_id = metadata["statistic_id"]
    start = date - timedelta(days=1)
    end = date - timedelta(minutes=1)

    _LOGGER.debug("Looking history sum for %s for %s between %s and %s", statistic_id, date, start, end)

    stat = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        end,
        {statistic_id},
        "day",
        None,
        {"sum"},
    )

    if statistic_id not in stat:
        _LOGGER.debug("No history sum found")
        return 0.0

    sum_ = stat[statistic_id][0]["sum"]
    _LOGGER.debug("History sum for %s = %s", statistic_id, sum_)

    return sum_
