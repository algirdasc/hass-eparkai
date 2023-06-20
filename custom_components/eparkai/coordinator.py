import requests
import datetime
import logging

from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
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

        try:
            await self.hass.async_add_executor_job(self.client.login)

            for generation_id in self.async_contexts():
                await self.hass.async_add_executor_job(
                    self.client.update_generation, generation_id, datetime.now()
                )

                data[generation_id] = self.client.get_latest_generation(generation_id)

        except requests.exceptions.RequestException as err:
            _LOGGER.exception(err)
            raise UpdateFailed(f"Error communicating with API: {err}")
        finally:
            return data
