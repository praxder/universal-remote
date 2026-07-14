"""Samsung Tizen adapter — wraps `samsungtvws` behind the remote-control seam."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from samsungtvws.async_remote import SamsungTVWSAsyncRemote
from samsungtvws.remote import SendInputString, SendRemoteKey

from ..capabilities import Capabilities
from ..errors import ConnectionFailedError, TextUnsupportedError
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "samsung-tizen"
APP_NAME = "UniversalRemote"
CONTROL_PORT = 8002  # wss control channel; 8001 would be plain ws
_PAIR_TIMEOUT = 30  # seconds to allow for tapping "Allow" on the TV
_CONNECT_TIMEOUT = 10  # seconds to reach the TV before treating it as unreachable

# Generic key -> Samsung remote key code.
SAMSUNG_KEYS: dict[Key, str] = {
    Key.UP: "KEY_UP",
    Key.DOWN: "KEY_DOWN",
    Key.LEFT: "KEY_LEFT",
    Key.RIGHT: "KEY_RIGHT",
    Key.OK: "KEY_ENTER",
    Key.BACK: "KEY_RETURN",
    Key.HOME: "KEY_HOME",
    Key.VOL_UP: "KEY_VOLUP",
    Key.VOL_DOWN: "KEY_VOLDOWN",
    Key.MUTE: "KEY_MUTE",
    Key.MENU: "KEY_MENU",
    Key.CH_UP: "KEY_CHUP",
    Key.CH_DOWN: "KEY_CHDOWN",
    # No combined PLAY_PAUSE on Samsung — that button stays unmapped (disabled).
    # These media codes were not found in the vendored library; verify on real
    # hardware (see tasks 4.4). A wrong code is a single dict-entry fix.
    Key.PLAY: "KEY_PLAY",
    Key.PAUSE: "KEY_PAUSE",
    Key.REWIND: "KEY_REWIND",
    Key.FAST_FORWARD: "KEY_FF",
    Key.STOP: "KEY_STOP",
    # Number pad: Samsung's digit codes are KEY_0–KEY_9.
    **{Key[f"NUM_{digit}"]: f"KEY_{digit}" for digit in range(10)},
}

# Text is attempted but not guaranteed on Samsung hardware.
_CAPABILITIES = Capabilities(keys=frozenset(SAMSUNG_KEYS), text=True)

# Factory so tests can inject a fake transport in place of the real remote.
RemoteFactory = Callable[..., SamsungTVWSAsyncRemote]


class SamsungSession(BaseSession):
    """A live connection to a Samsung TV; maps generic keys to Samsung codes."""

    def __init__(
        self, remote: SamsungTVWSAsyncRemote, capabilities: Capabilities
    ) -> None:
        super().__init__(capabilities)
        self._remote = remote

    async def _dispatch_key(self, key: Key) -> None:
        await self._remote.send_command(SendRemoteKey.click(SAMSUNG_KEYS[key]))

    async def _dispatch_text(self, text: str) -> None:
        try:
            await self._remote.send_command(SendInputString.send(text))
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this TV's firmware"
            ) from exc

    async def _release(self) -> None:
        await self._remote.close()


class SamsungTizenAdapter:
    """Builds Samsung sessions; pairing yields a token to persist and replay."""

    platform = PLATFORM
    display_name = "Samsung Tizen"

    def __init__(
        self,
        remote_factory: RemoteFactory = SamsungTVWSAsyncRemote,
        connect_timeout: float = _CONNECT_TIMEOUT,
    ) -> None:
        self._remote_factory = remote_factory
        self._connect_timeout = connect_timeout

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def pair(self, device: "Device", *, prompt=None) -> str:
        remote = self._remote_factory(
            host=device.ip,
            token=None,
            port=CONTROL_PORT,
            name=APP_NAME,
            timeout=_PAIR_TIMEOUT,
            key_press_delay=0,
        )
        try:
            await remote.open()  # triggers the TV popup; captures the token on accept
            return remote.token
        finally:
            await remote.close()

    async def connect(self, device: "Device") -> SamsungSession:
        remote = self._remote_factory(
            host=device.ip,
            token=device.credential,
            port=CONTROL_PORT,
            name=APP_NAME,
            timeout=self._connect_timeout,  # the library bounds the connect itself
            key_press_delay=0,
        )
        try:
            await remote.open()
        except Exception as exc:
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return SamsungSession(remote, _CAPABILITIES)


def register(registry: "AdapterRegistry") -> None:
    registry.register(SamsungTizenAdapter())
