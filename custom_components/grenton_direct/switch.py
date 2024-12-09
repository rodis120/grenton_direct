"""Platform for switch integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_NAME

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
    """Perform the setup for Light devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]
    add_entities([GrentonSwitch(grenton_api, config)], update_before_add=True)


class GrentonSwitch(GrentonObject, SwitchEntity):
    """Representation of a GrentonLoght."""

    RELAY_STATE_INDEX = 0

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonSwitch."""
        super().__init__(grenton_api, config)

        self.register_update_handler(self.RELAY_STATE_INDEX, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_is_on = ctx.value

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        await self.set_value(self.RELAY_STATE_INDEX, 1)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Tunr switch off."""
        await self.set_value(self.RELAY_STATE_INDEX, 0)
