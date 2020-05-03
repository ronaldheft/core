"""Support for the Roku media player."""
import logging

from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    ReadTimeout as RequestsReadTimeout,
)
from roku import RokuException

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

from .const import DATA_CLIENT, DEFAULT_MANUFACTURER, DEFAULT_PORT, DOMAIN

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
    roku = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    unique_id = roku.device.info.serial_number
    async_add_entities([RokuMediaPlayer(unique_id, roku)], True)


class RokuMediaPlayer(RokuEntity, MediaPlayerEntity):
    """Representation of a Roku media player on the network."""

    def __init__(self, unique_id: str, roku: Roku):
        """Initialize the Roku device."""
        super().__init__(
            roku=roku,
            name=roku.device.info.name,
            device_id=unique_id,
        )

        self.roku = roku
        self._available = False
        self._power_state = "Unknown"

    async def async_update(self):
        """Retrieve latest state."""
        try:
            await self.roku.update()
            self._available = True
        except RokuError:
            self._available = False

    def get_source_list(self):
        """Get the list of applications to be used as sources."""
        return ["Home"] + sorted(channel.name for channel in self.roku.apps)

    @property
    def should_poll(self):
        """Device should be polled."""
        return True

    @property
    def state(self):
        """Return the state of the device."""
        if self._power_state == "Off":
            return STATE_STANDBY

        if self.current_app is None:
            return None

        if self.current_app.name == "Power Saver" or self.current_app.is_screensaver:
            return STATE_IDLE

        if self.current_app.name == "Roku":
            return STATE_HOME

        if self.current_app.name is not None:
            return STATE_PLAYING

        return None

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_ROKU

    @property
    def available(self):
        """Return if able to retrieve information from device or not."""
        return self._available

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        if self.current_app is None or self.current_app.name in ("Power Saver", "Roku"):
            return None

        return MEDIA_TYPE_CHANNEL

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        if self.current_app is None or self.current_app.name in ("Power Saver", "Roku"):
            return None

        if self.current_app.id is None:
            return None

        return (
            f"http://{self.ip_address}:{DEFAULT_PORT}/query/icon/{self.current_app.id}"
        )

    @property
    def app_name(self):
        """Name of the current running app."""
        if self.current_app is not None:
            return self.current_app.name

    @property
    def app_id(self):
        """Return the ID of the current running app."""
        if self.current_app is not None:
            return self.current_app.id

    @property
    def source(self):
        """Return the current input source."""
        if self.current_app is not None:
            return self.current_app.name

    @property
    def source_list(self):
        """List of available input sources."""
        return self.channels

    async def async_turn_on(self):
        """Turn on the Roku."""
        await self.roku.remote("poweron")

    async def async_turn_off(self):
        """Turn off the Roku."""
        await self.roku.remote("poweroff")

    def media_play_pause(self):
        """Send play/pause command."""
        if self.current_app is not None:
            self.roku.play()

    def media_previous_track(self):
        """Send previous track command."""
        if self.current_app is not None:
            self.roku.reverse()

    def media_next_track(self):
        """Send next track command."""
        if self.current_app is not None:
            self.roku.forward()

    def mute_volume(self, mute):
        """Mute the volume."""
        if self.current_app is not None:
            self.roku.volume_mute()

    def volume_up(self):
        """Volume up media player."""
        if self.current_app is not None:
            self.roku.volume_up()

    def volume_down(self):
        """Volume down media player."""
        if self.current_app is not None:
            self.roku.volume_down()

    def play_media(self, media_type, media_id, **kwargs):
        """Tune to channel."""
        if media_type != MEDIA_TYPE_CHANNEL:
            _LOGGER.error(
                "Invalid media type %s. Only %s is supported",
                media_type,
                MEDIA_TYPE_CHANNEL,
            )
            return

        if self.current_app is not None:
            self.roku.tune(self.roku[media_id)

    def select_source(self, source):
        """Select input source."""
        if self.current_app is None:
            return

        if source == "Home":
            self.roku.home()
        else:
            channel = self.roku[source]
            channel.launch()
