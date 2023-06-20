import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorExtraStoredData,
)

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_ID,
    UnitOfEnergy
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .coordinator import EParkaiCoordinator
from . import (
    DOMAIN,
    CONF_GENERATION_ID
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_GENERATION_ID): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    coordinator: EParkaiCoordinator = hass.data[DOMAIN]
    async_add_entities([EParkaiSensor(hass, config, coordinator)])


class EParkaiSensor(CoordinatorEntity, RestoreSensor, SensorEntity):

    def __init__(self, hass, config, coordinator):
        self._coordinator = coordinator
        self._coordinator_context = config.get(CONF_GENERATION_ID)
        self._hass = hass
        self._config = config
        self._attr_name = '{}_{}'.format(DOMAIN, config.get(CONF_GENERATION_ID))
        self._attr_unique_id = 'uid_{}_{}'.format(DOMAIN, config.get(CONF_GENERATION_ID))
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_value = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name
        )

        self.restored_data: SensorExtraStoredData | None = None

        super().__init__(coordinator, context=self._coordinator_context)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_sensor_data()
        if state:
            self._attr_native_value = state.native_value
        self.async_schedule_update_ha_state(force_refresh=True)

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._coordinator_context not in self._coordinator.data:
            return

        self._attr_native_value = self._coordinator.data[self._coordinator_context]
        self.async_write_ha_state()
