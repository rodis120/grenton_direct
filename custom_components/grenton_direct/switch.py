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

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
    from pygrenton.clu_client import CluClient, UpdateContext

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_OBJ_ID): cv.string, vol.Required(CONF_NAME): cv.string}
)

RELAY_STATE_INDEX = 0


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa: ARG001
) -> None:
    """Perform the setup for Light devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]
    add_entities([GrentonSwitch(grenton_api, config)], update_before_add=True)


class GrentonSwitch(SwitchEntity):
    """Representation of a GrentonLoght."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonSwitch."""
        super().__init__()
        self._api = grenton_api
        self._object_id = config[CONF_OBJ_ID]

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = DOMAIN + "." + self._object_id

        self._api.register_value_change_handler(
            self._object_id, RELAY_STATE_INDEX, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_is_on = ctx.value

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        await self._api.set_value_async(self._object_id, RELAY_STATE_INDEX, 1)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Tunr switch off."""
        await self._api.set_value_async(self._object_id, RELAY_STATE_INDEX, 0)
