"""Platform for light integration."""

from __future__ import annotations

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
HEX_COLOR_INDEX = 6
SET_WHITE_INDEX = 12
BRIGHTNESS_INDEX = 0


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
        self._attr_supported_color_modes = {
            ColorMode.RGBW,
            ColorMode.BRIGHTNESS,
            ColorMode.ONOFF,
        }

        self._attr_rgbw_color = (0, 0, 0, 0)

        self._api.register_value_change_handler(
            self._object_id, HEX_COLOR_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, COLOR_WHITE_INDEX, self._update_handler
        )
        self._api.register_value_change_handler(
            self._object_id, BRIGHTNESS_INDEX, self._update_handler
        )

    def _update_handler(self, ctx: UpdateContext) -> None:
        r, g, b, w = self._attr_rgbw_color or (0, 0, 0, 0)

        if ctx.index == HEX_COLOR_INDEX:
            hex_color = ctx.value
            r = int(hex_color[1:3], base=16)
            g = int(hex_color[3:5], base=16)
            b = int(hex_color[5:7], base=16)

            self._attr_rgbw_color = (r, g, b, w)
        elif ctx.index == COLOR_WHITE_INDEX:
            self._attr_rgbw_color = (r, g, b, ctx.value)
        elif ctx.index == BRIGHTNESS_INDEX:
            self._attr_brightness = ctx.value
            self._attr_is_on = ctx.value != 0
        else:
            return

        self.schedule_update_ha_state()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set RGBW color."""
        color = kwargs.get(ATTR_RGBW_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS, 0) / 255

        if color:
            hex_color = "#{:02x}{:02x}{:02x}".format(*color[:3])
            await self._api.execute_method_async(
                self._object_id, HEX_COLOR_INDEX, hex_color
            )
            await self._api.execute_method_async(
                self._object_id, SET_WHITE_INDEX, color[3]
            )
        elif brightness:
            await self._api.execute_method_async(
                self._object_id, BRIGHTNESS_INDEX, brightness
            )
        else:
            await self._api.execute_method_async(self._object_id, BRIGHTNESS_INDEX, 1)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        await self._api.execute_method_async(self._object_id, BRIGHTNESS_INDEX, 0)
