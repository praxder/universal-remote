"""LG WebOS adapter — wraps `aiowebostv` behind the remote-control seam."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Awaitable, Callable

from aiowebostv import WebOsClient, endpoints

from ..capabilities import Capabilities
from ..discovery import DiscoveredDevice, SsdpHit, resolve_upnp_name, search_ssdp
from ..errors import ConnectionFailedError, TextUnsupportedError
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "lg-webos"
_CONNECT_TIMEOUT = 10  # seconds to reach the TV before treating it as unreachable
# The LG SSDP search target; the friendly name comes from the UPnP device XML.
DISCOVERY_TARGET = "urn:lge-com:service:webos-second-screen:1"

# Generic key -> LG input-channel button name.
LG_BUTTONS: dict[Key, str] = {
    Key.UP: "UP",
    Key.DOWN: "DOWN",
    Key.LEFT: "LEFT",
    Key.RIGHT: "RIGHT",
    Key.OK: "ENTER",
    Key.BACK: "BACK",
    Key.HOME: "HOME",
    Key.VOL_UP: "VOLUMEUP",
    Key.VOL_DOWN: "VOLUMEDOWN",
    Key.MUTE: "MUTE",
    Key.MENU: "MENU",
    Key.CH_UP: "CHANNELUP",
    Key.CH_DOWN: "CHANNELDOWN",
    # No combined PLAY_PAUSE on LG — that button stays unmapped (disabled).
    Key.PLAY: "PLAY",
    Key.PAUSE: "PAUSE",
    Key.REWIND: "REWIND",
    Key.FAST_FORWARD: "FASTFORWARD",
    Key.STOP: "STOP",
    # Number pad: LG's button names are the bare digits "0"–"9".
    **{Key[f"NUM_{digit}"]: str(digit) for digit in range(10)},
}

_CAPABILITIES = Capabilities(keys=frozenset(LG_BUTTONS), text=True)

# Factory so tests can inject a fake client in place of the real WebOS client.
ClientFactory = Callable[..., WebOsClient]

# Discovery seams, injected so discovery is testable without a live network.
SsdpSearcher = Callable[[str, float], Awaitable[list[SsdpHit]]]
NameResolver = Callable[[str], Awaitable[str | None]]


class LgWebOsSession(BaseSession):
    """A live connection to an LG TV; maps generic keys to LG actions."""

    def __init__(self, client: WebOsClient, capabilities: Capabilities) -> None:
        super().__init__(capabilities)
        self._client = client

    async def _dispatch_key(self, key: Key) -> None:
        await self._client.button(LG_BUTTONS[key])

    async def _dispatch_text(self, text: str) -> None:
        try:
            await self._client.request(
                endpoints.INSERT_TEXT, {"text": text, "replace": 0}
            )
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this TV"
            ) from exc

    async def _release(self) -> None:
        await self._client.disconnect()


class LgWebOsAdapter:
    """Builds LG sessions; pairing yields a client-key to persist and replay."""

    platform = PLATFORM
    display_name = "LG WebOS"
    reachability_port = 3000  # aiowebostv tries ws://:3000 first

    def __init__(
        self,
        client_factory: ClientFactory = WebOsClient,
        connect_timeout: float = _CONNECT_TIMEOUT,
        search: SsdpSearcher = search_ssdp,
        resolve_name: NameResolver = resolve_upnp_name,
    ) -> None:
        self._client_factory = client_factory
        self._connect_timeout = connect_timeout
        self._search = search
        self._resolve_name = resolve_name

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def discover(self, timeout: float) -> list[DiscoveredDevice]:
        # SSDP finds LG IPs; the friendly name is a separate best-effort UPnP read,
        # so a failed name resolution still yields the device (named by IP).
        hits = await self._search(DISCOVERY_TARGET, timeout)
        devices = []
        for hit in hits:
            try:
                name = await self._resolve_name(hit.location)
            except Exception:
                name = None
            devices.append(
                DiscoveredDevice(name=name or "", platform=PLATFORM, ip=hit.ip)
            )
        return devices

    async def pair(self, device: "Device", *, prompt=None) -> str:
        client = self._client_factory(host=device.ip, client_key=None)
        try:
            await client.connect()  # triggers the TV prompt; registers on accept
            return client.client_key
        finally:
            await client.disconnect()

    async def connect(self, device: "Device") -> LgWebOsSession:
        client = self._client_factory(host=device.ip, client_key=device.credential)
        # The client factory takes no connect timeout, so bound it here; both a
        # transport failure and a timeout surface as ConnectionFailedError.
        try:
            await asyncio.wait_for(client.connect(), self._connect_timeout)
        except Exception as exc:
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return LgWebOsSession(client, _CAPABILITIES)


def register(registry: "AdapterRegistry") -> None:
    registry.register(LgWebOsAdapter())
