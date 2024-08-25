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
    SensorDeviceClass,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIT_OF_MEASUREMENT

from .const import (
    CONF_OBJ_ID,
    DOMAIN,
    GRENTON_API,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
    from pygrenton.clu_client import CluClient, UpdateContext

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_OBJ_ID): cv.string,
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
    name = config[CONF_NAME]
    device_class = config.get(CONF_DEVICE_CLASS, "")
    state_class = config.get(CONF_STATE_CLASS, "measurement")
    unit = config.get(CONF_UNIT_OF_MEASUREMENT, "")
    object_id = config[CONF_OBJ_ID]
    grenton_api = hass.data[DOMAIN][GRENTON_API]
    add_entities(
        [GrentonSensor(grenton_api, object_id, name, device_class, state_class, unit)],
        update_before_add=True,
    )


class GrentonSensor(SensorEntity):
    """Representation of a GrentonSensor."""

    def __init__(  # noqa: PLR0913
        self,
        grenton_api: CluClient,
        object_id: str,
        name: str,
        device_class: SensorDeviceClass,
        state_class: str,
        unit: str,
    ) -> None:
        """Init GrentonSensor."""
        super().__init__()
        self._api = grenton_api
        self._object_id = object_id

        self._attr_name = name
        self._attr_unique_id = DOMAIN + "." + object_id

        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit

        self._api.register_value_change_handler(
            self._object_id, 0, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_native_value = ctx.value

        self.schedule_update_ha_state()
