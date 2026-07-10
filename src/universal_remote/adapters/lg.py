"""LG WebOS adapter — wraps `aiowebostv` behind the remote-control seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from aiowebostv import WebOsClient, endpoints
from wakeonlan import send_magic_packet

from ..capabilities import Capabilities
from ..errors import TextUnsupportedError
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "lg-webos"

# Generic key -> LG input-channel button name. Power is handled separately (no
# input-channel button; a session power press means power-off via SSAP).
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
}

_SUPPORTED_KEYS = frozenset(LG_BUTTONS) | {Key.POWER}
_CAPABILITIES = Capabilities(keys=_SUPPORTED_KEYS, text=True, power_on=True)

# Factory so tests can inject a fake client in place of the real WebOS client.
ClientFactory = Callable[..., WebOsClient]


@dataclass(frozen=True)
class PowerOnResult:
    """Outcome of a best-effort Wake-on-LAN power-on attempt."""

    packet_sent: bool
    best_effort: bool = True


class LgWebOsSession(BaseSession):
    """A live connection to an LG TV; maps generic keys to LG actions."""

    def __init__(self, client: WebOsClient, capabilities: Capabilities) -> None:
        super().__init__(capabilities)
        self._client = client

    async def _dispatch_key(self, key: Key) -> None:
        if key is Key.POWER:
            await self._client.power_off()
        else:
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

    def __init__(
        self,
        client_factory: ClientFactory = WebOsClient,
        wol: Callable[[str], None] = send_magic_packet,
    ) -> None:
        self._client_factory = client_factory
        self._wol = wol

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def pair(self, device: "Device", *, prompt=None) -> str:
        client = self._client_factory(host=device.ip, client_key=None)
        try:
            await client.connect()  # triggers the TV prompt; registers on accept
            return client.client_key
        finally:
            await client.disconnect()

    async def connect(self, device: "Device") -> LgWebOsSession:
        client = self._client_factory(host=device.ip, client_key=device.credential)
        await client.connect()
        return LgWebOsSession(client, _CAPABILITIES)

    def power_on(self, device: "Device") -> PowerOnResult:
        if not device.mac:
            return PowerOnResult(packet_sent=False)
        self._wol(device.mac)
        return PowerOnResult(packet_sent=True)


def register(registry: "AdapterRegistry") -> None:
    registry.register(LgWebOsAdapter())
