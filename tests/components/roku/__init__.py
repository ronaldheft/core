"""Tests for the Roku component."""
from socket import gaierror as SocketGIAError

from homeassistant.components.roku.const import DOMAIN
from homeassistant.components.ssdp import ATTR_SSDP_LOCATION, ATTR_UPNP_FRIENDLY_NAME, ATTR_UPNP_SERIAL 
from homeassistant.const import CONF_HOST
from homeassistant.helpers.typing import HomeAssistantType

from tests.common import MockConfigEntry, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

HOST = "192.168.1.160"
NAME = "Roku 3"
SSDP_LOCATION = "http://192.168.1.160/"
UPNP_FRIENDLY_NAME = "My Roku 3"
UPNP_SERIAL = "1GU48T017973"

MOCK_SSDP_DISCOVERY_INFO = {
    ATTR_SSDP_LOCATION: SSDP_LOCATION,
    ATTR_UPNP_FRIENDLY_NAME: UPNP_FRIENDLY_NAME,
    ATTR_UPNP_SERIAL: UPNP_SERIAL,
}


def mock_connection(
    aioclient_mock: AiohttpClientMocker,
    device: str = "roku3",
    app: str = "roku",
    host: str = HOST,
    error: bool = False,
    server_error: bool = False,
) -> None:
    """Mock the Roku connection."""
    roku_url = f"http://{host}:8060"

    if error:
        mock_connection_error()
        return

    if server_error:
        mock_connection_server_error()
        return

    aioclient_mock.get(
        f"{roku_url}/query/device-info",
        text=load_fixture(f"roku/{device}-device-info.xml"),
    )

    apps_fixture = "roku/apps.xml"
    if device == "rokutv":
        apps_fixture = "roku/apps-tv.xml"

    aioclient_mock.get(
        f"{roku_url}/query/apps", text=load_fixture(apps_fixture),
    )

    aioclient_mock.get(
        f"{roku_url}/query/active-app", text=load_fixture(f"roku/active-app-{app}.xml"),
    )


def mock_connection_error(
    aioclient_mock: AiohttpClientMocker,
    device: str = "roku3",
    app: str = "roku",
    host: str = HOST,
) -> None:
    """Mock the Roku connection error."""
    roku_url = f"http://{host}:8060"

    aioclient_mock.get(f"{roku_url}/query/device-info", exc=SocketGIAError)

    apps_fixture = "roku/apps.xml"
    if device == "rokutv":
        apps_fixture = "roku/apps-tv.xml"

    aioclient_mock.get(f"{roku_url}/query/apps", exc=SocketGIAError)
    aioclient_mock.get(f"{roku_url}/query/active-app", exc=SocketGIAError)


def mock_connection_server_error(
    aioclient_mock: AiohttpClientMocker,
    device: str = "roku3",
    app: str = "roku",
    host: str = HOST,
) -> None:
    """Mock the Roku connection error."""
    roku_url = f"http://{host}:8060"

    aioclient_mock.get(f"{roku_url}/query/device-info", status=500)

    apps_fixture = "roku/apps.xml"
    if device == "rokutv":
        apps_fixture = "roku/apps-tv.xml"

    aioclient_mock.get(f"{roku_url}/query/apps", status=500)
    aioclient_mock.get(f"{roku_url}/query/active-app", status=500)


async def setup_integration(
    hass: HomeAssistantType,
    aioclient_mock: AiohttpClientMocker,
    device: str = "roku3",
    app: str = "roku",
    host: str = HOST,
    unique_id: str = UPNP_SERIAL,
    skip_entry_setup: bool = False,
) -> MockConfigEntry:
    """Set up the Roku integration in Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=unique_id, data={CONF_HOST: host})

    entry.add_to_hass(hass)

    if not skip_entry_setup:
        mock_connection(aioclient_mock, device, app=app, host=host)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry
