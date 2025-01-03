"""Platform for sensor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIT_OF_MEASUREMENT

from .const import (
    CONF_INDEX,
    CONF_OBJ_ID,
    DOMAIN,
    GRENTON_API,
)
from .utils import GrentonObject

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
    from pygrenton.clu_client import CluClient, UpdateContext

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_OBJ_ID): cv.string,
        vol.Required(CONF_INDEX): int,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa: ARG001
) -> None:
    """Perform the setup for Sensor devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]
    add_entities(
        [GrentonSensor(grenton_api, config)],
        update_before_add=True,
    )


class GrentonSensor(GrentonObject, SensorEntity):
    """Representation of a GrentonSensor."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonSensor."""
        super().__init__(grenton_api, config)
        self._index = config[CONF_INDEX]

        self._attr_device_class = config.get(CONF_DEVICE_CLASS, "")
        self._attr_state_class = config.get(CONF_STATE_CLASS, "measurement")
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT, "")

        self.register_update_handler(self._index, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_native_value = ctx.value

        self.schedule_update_ha_state()
