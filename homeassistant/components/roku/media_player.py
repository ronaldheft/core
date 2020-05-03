"""Support for the Roku media player."""
import logging
from typing import List

from rokuecp import Roku, RokuError

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from homeassistant.const import STATE_HOME, STATE_IDLE, STATE_PLAYING, STATE_STANDBY

from .const import DEFAULT_MANUFACTURER, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_ROKU = (
    SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Roku config entry."""
    roku = hass.data[DOMAIN][entry.entry_id]
    unique_id = roku.device.info.serial_number
    async_add_entities([RokuMediaPlayer(unique_id, roku)], True)


class RokuMediaPlayer(RokuEntity, MediaPlayerEntity):
    """Representation of a Roku media player on the network."""

    def __init__(self, unique_id: str, roku: Roku) -> None:
        """Initialize the Roku device."""
        super().__init__(
            roku=roku,
            name=roku.device.info.name,
            device_id=unique_id,
        )

        self._available = False
        self._channels = []
        self._channel_ids = []

    async def async_update(self) -> None:
        """Retrieve latest state."""
        try:
            await self.roku.update()
            self._available = True
            self._channels = self.get_source_list()
            self._channel_ids = {app.name: app.app_id for app in self.roku.device.apps}
        except RokuError:
            self._available = False

    def get_source_list(self) -> List:
        """Get the list of applications to be used as sources."""
        return ["Home"] + sorted(app.name for app in self.roku.device.apps)

    @property
    def should_poll(self) -> bool:
        """Device should be polled."""
        return True

    @property
    def state(self) -> str:
        """Return the state of the device."""
        if self.roku.device.state.standby:
            return STATE_STANDBY

        if self.roku.device.app is None:
            return None

        if self.roku.device.app.name == "Power Saver" or self.roku.device.app.screensaver:
            return STATE_IDLE

        if self.roku.device.app.name == "Roku":
            return STATE_HOME

        if self.roku.device.app.name is not None:
            return STATE_PLAYING

        return None

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_ROKU

    @property
    def available(self) -> bool:
        """Return if able to retrieve information from device or not."""
        return self._available

    @property
    def media_content_type(self) -> str:
        """Content type of current playing media."""
        if self.roku.device.app is None or self.roku.device.app.name in ("Power Saver", "Roku"):
            return None

        return MEDIA_TYPE_CHANNEL

    @property
    def media_image_url(self) -> str:
        """Image url of current playing media."""
        if self.roku.device.app is None or self.roku.device.app.name in ("Power Saver", "Roku"):
            return None

        if self.roku.device.app.id is None:
            return None

        return self.roku.app_icon_url(self.roku.device.app.id)

    @property
    def app_name(self) -> str:
        """Name of the current running app."""
        if self.roku.device.app is not None:
            return self.roku.device.app.name

        return None

    @property
    def app_id(self) -> str:
        """Return the ID of the current running app."""
        if self.roku.device.app is not None:
            return self.roku.device.app.id

        return None

    @property
    def source(self) -> str:
        """Return the current input source."""
        if self.roku.device.app is not None:
            return self.roku.device.app.name

        return None

    @property
    def source_list(self) -> List:
        """List of available input sources."""
        return self._channels

    async def async_turn_on(self) -> None:
        """Turn on the Roku."""
        await self.roku.remote("poweron")

    async def async_turn_off(self) -> None:
        """Turn off the Roku."""
        await self.roku.remote("poweroff")

    async def async_media_play_pause(self) -> None:
        """Send play/pause command."""
        await self.roku.remote("play")

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.roku.remote("reverse")

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.roku.remote("forward")

    async def async_mute_volume(self, mute) -> None:
        """Mute the volume."""
        await self.roku.remote("volume_mute")

    async def async_volume_up(self) -> None:
        """Volume up media player."""
        await self.roku.remote("volume_up")

    async def async_volume_down(self) -> None:
        """Volume down media player."""
        await self.roku.remote("volume_down")

    async def async_play_media(self, media_type: str, media_id: str,  **kwargs) -> None:
        """Tune to channel."""
        if media_type != MEDIA_TYPE_CHANNEL:
            _LOGGER.error(
                "Invalid media type %s. Only %s is supported",
                media_type,
                MEDIA_TYPE_CHANNEL,
            )
            return

        await self.roku.tune(media_id)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source == "Home":
            await self.roku.remote("home")

        if source not in self._channel_ids:
            return

        await self.roku.launch(self._channel_ids[source])
