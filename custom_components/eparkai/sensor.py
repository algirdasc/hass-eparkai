import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import EParkaiCoordinator

_LOGGER = logging.getLogger(__name__)

CONF_POWER_PLANT_ID = "power_plant_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_POWER_PLANT_ID): cv.string,
})


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    coordinator: EParkaiCoordinator = hass.data[DOMAIN]
    async_add_entities([EParkaiSensor(hass, config, coordinator)])


class EParkaiSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, hass: HomeAssistant, config: ConfigType, coordinator):
        power_plant_id = config.get(CONF_POWER_PLANT_ID)

        self._coordinator = coordinator
        self._coordinator_context = config.get(CONF_POWER_PLANT_ID)
        self._hass = hass
        self._config = config
        self._attr_name = f"{DOMAIN}_{power_plant_id}"
        self._attr_unique_id = f"uid_{self._attr_name}"
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name
        )

        super().__init__(coordinator, context={"power_plant_id": power_plant_id, "entity_name": self._attr_name})

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_schedule_update_ha_state(force_refresh=True)

    # @callback
    # def _handle_coordinator_update(self) -> None:
    #     if self._coordinator.data is None or self._coordinator_context not in self._coordinator.data:
    #         return
    #
    #     self._attr_native_value = self._coordinator.data[self._coordinator_context]
    #     self.async_write_ha_state()
