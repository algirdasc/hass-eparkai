import datetime
import logging

from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.components.recorder import DOMAIN as RECORDER_DOMAIN, get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfEnergy

from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    async_import_statistics,
    statistics_during_period
)


from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .eparkai_client import EParkaiClient

_LOGGER = logging.getLogger(__name__)


class EParkaiCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, client: EParkaiClient, percentage: int | None):
        super().__init__(
            hass,
            _LOGGER,
            name="EParkaiCoordinator",
            update_interval=timedelta(hours=1),
        )

        self.hass = hass
        self.client = client
        self.percentage = percentage

    async def _async_update_data(self) -> dict:
        data = {}

        await self.hass.async_add_executor_job(self.client.login)

        for context in self.async_contexts():
            power_plant_id = context["power_plant_id"]

            await self.hass.async_add_executor_job(self.client.update_generation, power_plant_id, datetime.now())

            await self.import_statistics(context)

            data[power_plant_id] = self.client.get_latest_generation(power_plant_id)

        return data

    async def import_statistics(self, context: dict) -> None:
        entity_name = context["entity_name"]

        metadata: StatisticMetaData = {
            "source": RECORDER_DOMAIN,
            "name": None,
            "statistic_id": f"sensor.{entity_name}",
            "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
            "has_mean": False,
            "has_sum": True,
        }

        statistics = await self.get_statistics(context, metadata)

        async_import_statistics(self.hass, metadata, statistics)

    async def get_statistics(self, context: dict, metadata: StatisticMetaData) -> list[StatisticData]:
        statistics: list[StatisticData] = []
        power_plant_id = context["power_plant_id"]
        sum_ = None

        generation = self.client.get_generation(power_plant_id)
        if generation is None:
            return statistics

        _LOGGER.error("Got items: {}".format(generation.items()))

        for ts, generated_kwh in generation.items():
            dt_object = datetime.fromtimestamp(ts)

            if self.percentage is not None:
                generated_kwh = generated_kwh * (self.percentage / 100)

            if sum_ is None:
                sum_ = await self.get_yesterday_sum(dt_object, StatisticMetaData)

            statistic_data: StatisticData = {
                "start": dt_object.replace(tzinfo=dt_util.get_time_zone("Europe/Vilnius")),
                "state": generated_kwh,
                "sum": sum_
            }

            _LOGGER.error(f"{dt_object} generated {generated_kwh}, sum={sum_}")

            sum_ += generated_kwh
            statistics.append(statistic_data)

        return statistics

    async def get_yesterday_sum(self, date: datetime, metadata: StatisticMetaData) -> float:
        statistic_id = metadata["statistic_id"]
        start = date - timedelta(days=1)
        end = date - timedelta(minutes=1)

        _LOGGER.info(f"For {date} looking stats between {start} and {end}")

        stat = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            start,
            end,
            {statistic_id},
            "day",
            None,
            {"sum"},
        )

        if statistic_id not in stat:
            return 0.0

        sum_ = stat[statistic_id][0]["sum"]
        _LOGGER.error(f"{stat[statistic_id]} sum: {sum_}")

        return sum_
