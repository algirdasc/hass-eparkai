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
    get_last_statistics,
)


from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .eparkai_client import EParkaiClient

_LOGGER = logging.getLogger(__name__)


class EParkaiCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, client: EParkaiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="EParkaiCoordinator",
            update_interval=timedelta(hours=1),
        )

        self.hass = hass
        self.client = client

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
        statistic_id = metadata["statistic_id"]
        power_plant_id = context["power_plant_id"]
        sum_ = 0.0

        generation = self.client.get_generation(power_plant_id)
        if generation is None:
            return statistics

        last_stats = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics, self.hass, 1, statistic_id, False, {"sum"}
        )

        if statistic_id in last_stats:
            sum_ = last_stats[statistic_id][0]["sum"] or 0

        for ts, generated_kwh in generation.items():
            dt_object = datetime.fromtimestamp(ts).replace(tzinfo=dt_util.get_time_zone("Europe/Vilnius"))
            sum_ += generated_kwh
            statistic_data: StatisticData = {
                "start": dt_object,
                "sum": sum_
            }
            statistics.append(statistic_data)

        return statistics
