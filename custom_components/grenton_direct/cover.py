"""Grenton blinds platform integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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

ROLLER_SHUTER_STATE_INDEX = 0
ROLLER_SHUTER_POSITION_INDEX = 7

ROLLER_SHUTER_STATE_OPENING = 1
ROLLER_SHUTER_STATE_CLOSING = 2

ROLLER_SHUTER_OPEN_METHOD = 0
ROLLER_SHUTER_CLOSE_METHOD = 1
ROLLER_SHUTER_STOP_METHOD = 3
ROLLER_SHUTER_SET_POSITION_METHOD = 10


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa: ARG001
) -> None:
    """Perform the setup for Cover devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]
    add_entities([GrentonCover(grenton_api, config)], update_before_add=True)


class GrentonCover(CoverEntity):
    """Grenton cover entity."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonCover."""
        super().__init__()
        self._api = grenton_api
        self._object_id = config[CONF_OBJ_ID]

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = DOMAIN + "." + self._object_id
        self._attr_device_class = CoverDeviceClass.BLIND
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.SET_POSITION
            | CoverEntityFeature.STOP
        )

        self._api.register_value_change_handler(
            self._object_id, ROLLER_SHUTER_STATE_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, ROLLER_SHUTER_POSITION_INDEX, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        if ctx.index == ROLLER_SHUTER_STATE_INDEX:
            self._attr_is_opening = ctx.value == ROLLER_SHUTER_STATE_OPENING
            self._attr_is_closing = ctx.value == ROLLER_SHUTER_STATE_CLOSING

        elif ctx.index == ROLLER_SHUTER_POSITION_INDEX:
            self._attr_is_closed = ctx.value == 0
            self._attr_current_cover_position = ctx.value

        self.schedule_update_ha_state()

    @override
    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover."""
        if not self._attr_is_opening:
            await self._api.execute_method_async(
                self._object_id, ROLLER_SHUTER_OPEN_METHOD, 0
            )

    @override
    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        if not self._attr_is_closing:
            await self._api.execute_method_async(
                self._object_id, ROLLER_SHUTER_CLOSE_METHOD, 0
            )

    @override
    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set cover position."""
        pos = kwargs[ATTR_POSITION]
        await self._api.execute_method_async(
            self._object_id, ROLLER_SHUTER_SET_POSITION_METHOD, pos
        )

    @override
    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop cover."""
        await self._api.execute_method_async(
            self._object_id, ROLLER_SHUTER_STOP_METHOD, 0
        )
