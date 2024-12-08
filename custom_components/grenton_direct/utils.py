"""Utils used by grenton_direct integration."""

from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_NAME

from .const import CONF_OBJ_ID, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from homeassistant.helpers.typing import ConfigType
    from pygrenton.clu_client import CluClient, UpdateContext


class GrentonObject:
    """Class that represents grenton object."""

    def __init__(self, grenton_api: CluClient, config: ConfigType) -> None:
        """Initialize GrentonObject."""
        self._api = grenton_api
        self._object_id = config[CONF_OBJ_ID]

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = DOMAIN + "." + self._object_id

    def register_update_handler(
        self, index: int | Iterable[int], handler: Callable[[UpdateContext], None]
    ) -> None:
        """Register feature value change handler."""
        self._api.register_value_change_handler(self._object_id, index, handler)

    async def execute_method(self, index: int, *args: Any) -> Any:
        """Execute object's method."""
        return await self._api.execute_method_async(self._object_id, index, args)

    async def set_value(self, index: int, value: Any) -> None:
        """Set value of a feature."""
        await self._api.set_value_async(self._object_id, index, value)

    async def get_value(self, index: int) -> Any:
        """Get value of a feature."""
        return await self._api.get_value_async(self._object_id, index)
