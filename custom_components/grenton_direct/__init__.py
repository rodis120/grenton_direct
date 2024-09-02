"""The grenton_direct integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from pygrenton.clu_client import CluClient, GrentonCipher

from .const import (
    CONF_CLIENT_IP,
    CONF_CLIENT_PORT,
    CONF_IV,
    CONF_KEY,
    CONF_REFRESH_INTERVAL,
    CONNECTION_LIMIT,
    DOMAIN,
    GRENTON_API,
)

if TYPE_CHECKING:
    from homeassistant.helpers.typing import ConfigType

GRENTON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_PORT): int,
        vol.Required(CONF_KEY): cv.string,
        vol.Required(CONF_IV): cv.string,
        vol.Optional(CONF_REFRESH_INTERVAL): float,
        vol.Optional(CONF_CLIENT_IP): cv.string,
        vol.Optional(CONF_CLIENT_PORT): int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {vol.Required(DOMAIN): GRENTON_SCHEMA},
    extra=vol.ALLOW_EXTRA,
)

REQUEST_SCHEMA = vol.Schema(
    {
        vol.Required("payload"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up grenton from configuration."""
    gconfig: dict = config[DOMAIN]

    ip = gconfig[CONF_IP_ADDRESS]
    port = gconfig[CONF_PORT]
    key = gconfig[CONF_KEY]
    iv = gconfig[CONF_IV]
    client_refresh_interval = gconfig.get(CONF_REFRESH_INTERVAL, 60.0)
    client_ip = gconfig.get(CONF_CLIENT_IP, "")
    client_port = gconfig.get(CONF_CLIENT_PORT, 0)

    client = CluClient(
        ip,
        port,
        GrentonCipher(key, iv),
        client_refresh_interval=client_refresh_interval,
        client_ip=client_ip,
        client_port=client_port,
        max_connections=CONNECTION_LIMIT,
    )

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][GRENTON_API] = client

    async def clu_request(call: ServiceCall) -> ServiceResponse:
        payload = call.data["payload"]
        resp = await client.send_request_async(payload)

        return {"response": resp}

    async def lua_request(call: ServiceCall) -> ServiceResponse:
        payload = call.data["payload"]
        resp = await asyncio.to_thread(client._send_lua_request, payload)  # noqa: SLF001

        return {"response": resp}

    hass.services.async_register(
        DOMAIN,
        "clu_request",
        clu_request,
        schema=REQUEST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "lua_request",
        lua_request,
        schema=REQUEST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True
