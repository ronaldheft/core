"""Support for the Roku remote."""
from typing import Callable, List

from rokuecp import Roku, RokuError

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from . import RokuDataUpdateCoordinator, RokuEntity
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistantType,
    entry: ConfigEntry,
    async_add_entities: Callable[[List, bool], None],
) -> bool:
    """Load Roku remote based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = roku.device.info.serial_number
    async_add_entities([RokuRemote(unique_id, coordinator)])


class RokuRemote(RokuEntity, RemoteEntity):
    """Device that sends commands to an Roku."""

    def __init__(self, unique_id: str, coordinator: RokuDataUpdateCoordinator) -> None:
        """Initialize the Roku device."""
        super().__init__(
            device_id=unique_id,
            coordinator=coordinator,
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return not self.coordinator.data.state.standby

    @property
    def should_poll(self) -> bool:
        """No polling needed for Roku."""
        return False

    async def async_send_command(self, command: List, **kwargs) -> None:
        """Send a command to one device."""
        num_repeats = kwargs[ATTR_NUM_REPEATS]

        for _ in range(num_repeats):
            for single_command in command:
                await self.coordinator.roku.remote(command)
