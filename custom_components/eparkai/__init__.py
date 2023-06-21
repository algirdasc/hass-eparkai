import logging
from datetime import timedelta, datetime

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMetaData, StatisticData
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_ID,
    UnitOfEnergy, EVENT_HOMEASSISTANT_STARTED
)
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .eparkai_client import EParkaiClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eparkai"

CONF_POWER_PLANTS = "power_plants"
CONF_GENERATION_PERCENTAGE = "generation_percentage"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_POWER_PLANTS): vol.Schema({str: str}),
                vol.Optional(CONF_GENERATION_PERCENTAGE, default=100): vol.All(int, vol.Range(min=0, max=100))
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, config[DOMAIN])

    client = EParkaiClient(
        username=config[DOMAIN][CONF_USERNAME],
        password=config[DOMAIN][CONF_PASSWORD],
        client_id=config[DOMAIN][CONF_CLIENT_ID]
    )

    async def async_import_generation(now: datetime) -> None:
        if hass.is_stopping:
            _LOGGER.debug("HA is stopping, skipping generation import")
            return

        _LOGGER.debug(f"Logging in to {DOMAIN} site")
        await hass.async_add_executor_job(client.login)

        for power_plant_name, power_plant_id in config[DOMAIN][CONF_POWER_PLANTS].items():
            _LOGGER.debug(f"Fetching generation data for {power_plant_name}:{power_plant_id}")
            await hass.async_add_executor_job(client.update_generation, power_plant_id, now)

            _LOGGER.debug(f"Importing generation data for {power_plant_name}:{power_plant_id}")
            await async_insert_statistics(
                hass,
                power_plant_name,
                power_plant_id,
                client.get_generation_data(power_plant_id)
            )

    async def async_first_start(event: Event) -> None:
        await async_import_generation(datetime.now())

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, async_first_start)

    async_track_time_interval(hass, async_import_generation, timedelta(hours=1))

    return True


async def async_insert_statistics(
        hass: HomeAssistant,
        power_plant_name: str,
        power_plant_id: str,
        generation_data: dict
) -> None:
    statistic_id = f"{DOMAIN}:energy_generation_{power_plant_id}"

    _LOGGER.debug(f"Statistic ID = {statistic_id}")

    if not generation_data:
        _LOGGER.error(f"Received empty generation data for {power_plant_id}")
        return None

    metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name=power_plant_name,
                source=DOMAIN,
                statistic_id=statistic_id,
                unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    )

    statistics = await _async_get_statistics(hass, metadata, generation_data)

    async_add_external_statistics(hass, metadata, statistics)


async def _async_get_statistics(
        hass: HomeAssistant,
        metadata: StatisticMetaData,
        generation_data: dict
) -> list[StatisticData]:
    statistics: list[StatisticData] = []
    generation_percentage = hass.data[DOMAIN][CONF_GENERATION_PERCENTAGE]
    sum_ = None

    for ts, generated_kwh in generation_data.items():
        dt_object = datetime.fromtimestamp(ts)

        if generation_percentage != 100:
            generated_percentage_kwh = generated_kwh * (generation_percentage / 100)
            _LOGGER.debug(
                f"Applying generation percentage of {generation_percentage}%"
                f"to {generated_kwh} kWh -> {generated_percentage_kwh} kWh"
            )
            generated_kwh = generated_percentage_kwh

        if sum_ is None:
            sum_ = await get_yesterday_sum(hass, metadata, dt_object)

        statistics.append(StatisticData(
            start=dt_object.replace(tzinfo=dt_util.get_time_zone("Europe/Vilnius")),
            state=generated_kwh,
            sum=sum_
        ))

        sum_ += generated_kwh

    return statistics


async def get_yesterday_sum(hass: HomeAssistant, metadata: StatisticMetaData, date: datetime) -> float:
    statistic_id = metadata["statistic_id"]
    start = date - timedelta(days=1)
    end = date - timedelta(minutes=1)

    _LOGGER.debug(f"Looking history stats for {statistic_id} for {date} between {start} and {end}")

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
        return 0.0

    return stat[statistic_id][0]["sum"]
