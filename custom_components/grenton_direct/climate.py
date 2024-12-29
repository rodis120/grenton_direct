"""Platform for climate integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import CONF_NAME
from homeassistant.helpers.typing import ConfigType
from pygrenton.clu_client import CluClient

from .const import (
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
    {vol.Required(CONF_OBJ_ID): cv.string, vol.Required(CONF_NAME): cv.string}
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa: ARG001
) -> None:
    """Perform the setup for Climate devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]

    add_entities([GrentonThermostat(grenton_api, config)], update_before_add=True)


class GrentonThermostat(GrentonObject, ClimateEntity):
    """Representation of grenton thermostatat."""

    # feature indexes
    POINT_VALUE_INDEX = 3
    HYSTERESIS_INDEX = 5
    STATE_INDEX = 6
    CONTROLL_DIRECTION_INDEX = 7
    MODE_INDEX = 8
    CURRENT_TEMP_INDEX = 14

    # method indexes
    START_INDEX = 0
    STOP_INDEX = 1

    def __init__(self, grenton_api: CluClient, config: dict[str, Any]) -> None:
        """Init GrentonThermostat."""
        super().__init__(grenton_api, config)

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_modes = [HVACMode.HEAT_COOL, HVACMode.OFF]
        self._attr_supported_features = (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TARGET_TEMPERATURE
        )

        features = [
            self.POINT_VALUE_INDEX,
            self.HYSTERESIS_INDEX,
            self.STATE_INDEX,
            self.CONTROLL_DIRECTION_INDEX,
            self.MODE_INDEX,
            self.CURRENT_TEMP_INDEX,
        ]
        self.register_update_handler(features, self._update_handeler)

    def _update_handeler(self, ctx: UpdateContext) -> None:
        pass

    @override
    async def async_turn_on(self) -> None:
        await self.execute_method(self.START_INDEX)

    @override
    async def async_turn_off(self) -> None:
        await self.execute_method(self.STOP_INDEX)
