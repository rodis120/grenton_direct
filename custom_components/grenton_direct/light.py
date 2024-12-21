"""Platform for light integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, override

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
)
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

    device_prefix = config[CONF_OBJ_ID][:3]
    if device_prefix == "LED":
        entity = GrentonRGBW(grenton_api, config)
    elif device_prefix == "DIM":
        entity = GrentonDimmer(grenton_api, config)
    else:
        entity = GrentonLight(grenton_api, config)

    add_entities([entity], update_before_add=True)


class GrentonLight(GrentonObject, LightEntity):
    """Representation of a GrentonLoght."""

    RELAY_STATE_INDEX = 0

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonLight."""
        super().__init__(grenton_api, config)

        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}

        self.register_update_handler(self.RELAY_STATE_INDEX, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_is_on = ctx.value
        self._attr_state = ctx.value

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        await self.set_value(self.RELAY_STATE_INDEX, 1)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Tunr off light."""
        await self.set_value(self.RELAY_STATE_INDEX, 0)


class GrentonDimmer(GrentonObject, LightEntity):
    """Grenton Dimmer module representation."""

    BRIGHTNESS_INDEX = 0
    DIMMER_SWITCH_ON_INDEX = 2
    DIMMER_SWITCH_OFF_INDEX = 3

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonDimmer."""
        super().__init__(grenton_api, config)

        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        self.register_update_handler(self.BRIGHTNESS_INDEX, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        self._attr_brightness = int(ctx.value * 255)
        self._attr_is_on = ctx.value > 0

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness:
            await self.set_value(self.BRIGHTNESS_INDEX, brightness / 255)
        else:
            await self.execute_method(self.DIMMER_SWITCH_ON_INDEX, 0)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.execute_method(self.DIMMER_SWITCH_OFF_INDEX, 0)


class GrentonRGBW(GrentonObject, LightEntity):
    """Grenton RGBW module representation."""

    # feature indexes
    BRIGHTNESS_INDEX = 0
    COLOR_RED_INDEX = 3
    COLOR_GREEN_INDEX = 4
    COLOR_BLUE_INDEX = 5
    HEX_COLOR_INDEX = 6
    COLOR_WHITE_INDEX = 15

    # method indexes
    SET_BRIGHTNESS_INDEX = 0
    SET_RED_INDEX = 3
    SET_GREEN_INDEX = 4
    SET_BLUE_INDEX = 5
    SWITCH_ON_INDEX = 9
    SWITCH_OFF_INDEX = 10
    SET_WHITE_INDEX = 12

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Init GrentonRGBW."""
        super().__init__(grenton_api, config)

        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}

        self._attr_rgbw_color = (0, 0, 0, 0)

        features = (self.HEX_COLOR_INDEX, self.COLOR_WHITE_INDEX, self.BRIGHTNESS_INDEX)
        self.register_update_handler(features, self._update_handler)

    def _update_handler(self, ctx: UpdateContext) -> None:
        r, g, b, w = self._attr_rgbw_color or (0, 0, 0, 0)

        if ctx.index == self.HEX_COLOR_INDEX:
            hex_color = ctx.value
            r = int(hex_color[1:3], base=16)
            g = int(hex_color[3:5], base=16)
            b = int(hex_color[5:7], base=16)

            self._attr_rgbw_color = (r, g, b, w)
        elif ctx.index == self.COLOR_WHITE_INDEX:
            self._attr_rgbw_color = (r, g, b, ctx.value or 0)
        elif ctx.index == self.BRIGHTNESS_INDEX:
            self._attr_brightness = int(ctx.value * 255)
        else:
            return

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set RGBW color."""
        color = kwargs.get(ATTR_RGBW_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if color:
            await asyncio.gather(
                self.execute_method(self.SET_RED_INDEX, color[0]),
                self.execute_method(self.SET_GREEN_INDEX, color[1]),
                self.execute_method(self.SET_BLUE_INDEX, color[2]),
                self.execute_method(self.SET_WHITE_INDEX, color[3]),
            )

        elif brightness:
            await self.execute_method(self.BRIGHTNESS_INDEX, brightness / 255)

        else:
            await self.execute_method(self.SWITCH_ON_INDEX, 0)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        await self.execute_method(self.SWITCH_OFF_INDEX, 0)
