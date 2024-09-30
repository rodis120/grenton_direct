"""Platform for light integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, override

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import ATTR_RGBW_COLOR, ColorMode, LightEntity
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
COLOR_RED_INDEX = 3
COLOR_GREEN_INDEX = 4
COLOR_BLUE_INDEX = 5
COLOR_WHITE_INDEX = 15


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa: ARG001
) -> None:
    """Perform the setup for Light devices."""
    grenton_api = hass.data[DOMAIN][GRENTON_API]

    device_prefix = config[CONF_OBJ_ID][:3]
    if device_prefix == "LED":
        entity = GrentonRGBW(grenton_api, config)
    else:
        entity = GrentonLight(grenton_api, config)

    add_entities([entity], update_before_add=True)


class GrentonLight(LightEntity):
    """Representation of a GrentonLoght."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonLight."""
        super().__init__()
        self._api = grenton_api
        self._object_id = config[CONF_OBJ_ID]

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = DOMAIN + "." + self._object_id
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}

        self._api.register_value_change_handler(
            self._object_id, RELAY_STATE_INDEX, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_is_on = ctx.value
        self._attr_state = ctx.value

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        await self._api.set_value_async(self._object_id, RELAY_STATE_INDEX, 1)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Tunr off light."""
        await self._api.set_value_async(self._object_id, RELAY_STATE_INDEX, 0)


class GrentonRGBW(LightEntity):
    """Grenton RGBW module representation."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonRGBW."""
        super().__init__()
        self._api = grenton_api
        self._object_id = config[CONF_OBJ_ID]

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = DOMAIN + "." + self._object_id
        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGB, ColorMode.RGBW}

        self._api.register_value_change_handler(
            self._object_id, COLOR_RED_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, COLOR_GREEN_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, COLOR_BLUE_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, COLOR_WHITE_INDEX, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        r, g, b, w = self._attr_rgbw_color or (0, 0, 0, 0)

        if ctx.index == COLOR_RED_INDEX:
            self._attr_rgbw_color = (ctx.value, g, b, w)
        elif ctx.index == COLOR_GREEN_INDEX:
            self._attr_rgbw_color = (r, ctx.value, b, w)
        elif ctx.index == COLOR_BLUE_INDEX:
            self._attr_rgbw_color = (r, g, ctx.value, w)
        elif ctx.index == COLOR_WHITE_INDEX:
            self._attr_rgbw_color = (r, g, b, ctx.value)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set RGBW color."""
        await self._async_set_color(kwargs[ATTR_RGBW_COLOR])

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        await self._async_set_color((0, 0, 0, 0))

    async def _async_set_color(self, rgbw_color: tuple[int, int, int, int]) -> None:
        r, g, b, w = rgbw_color
        await asyncio.gather(
            self._api.set_value_async(self._object_id, COLOR_RED_INDEX, r),
            self._api.set_value_async(self._object_id, COLOR_GREEN_INDEX, g),
            self._api.set_value_async(self._object_id, COLOR_BLUE_INDEX, b),
            self._api.set_value_async(self._object_id, COLOR_WHITE_INDEX, w),
        )
