"""Platform for binary sensor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME

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
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_INDEX): int,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
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
        [GrentonBinarySensor(grenton_api, config)],
        update_before_add=True,
    )


class GrentonBinarySensor(GrentonObject, BinarySensorEntity):
    """Representation of a GrentonBinarySensor."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonBinarySensor."""
        super().__init__(grenton_api, config)
        self._index = config.get(CONF_INDEX, 0)

        self._attr_device_class = config.get(CONF_DEVICE_CLASS, "")

        self.register_update_handler(self._index, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        if ctx.value == 0:
            self._attr_is_on = False
        elif ctx.value == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = None

        self.schedule_update_ha_state()
