"""Roku adapter — wraps `rokuecp`'s ECP client behind the remote-control seam.

Roku's External Control Protocol is an unauthenticated HTTP API on the LAN, so
this adapter needs no pairing and issues no credential (`requires_pairing = False`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from aiohttp import ClientSession
from rokuecp import Roku, RokuError

from ..capabilities import Capabilities
from ..errors import ConnectionFailedError, PairingCancelledError, TextUnsupportedError
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "roku"

# Generic key -> rokuecp remote token. `Roku.remote` lower-cases its argument and
# looks it up in `rokuecp.const.VALID_REMOTE_KEYS`, whose keys are these snake_case
# tokens — not the ECP wire strings (`Rev`/`Fwd`/`VolumeUp`), which it would reject.
ROKU_KEYS: dict[Key, str] = {
    Key.UP: "up",
    Key.DOWN: "down",
    Key.LEFT: "left",
    Key.RIGHT: "right",
    Key.OK: "select",
    Key.BACK: "back",
    Key.HOME: "home",
    Key.VOL_UP: "volume_up",
    Key.VOL_DOWN: "volume_down",
    Key.MUTE: "volume_mute",
    Key.CH_UP: "channel_up",
    Key.CH_DOWN: "channel_down",
    # ECP exposes a single Play/Pause toggle, so no discrete PLAY/PAUSE/STOP.
    Key.PLAY_PAUSE: "play",
    Key.REWIND: "reverse",
    Key.FAST_FORWARD: "forward",
    # No number pad (Roku remotes have none) and no MENU (no ECP equivalent).
}

_CAPABILITIES = Capabilities(keys=frozenset(ROKU_KEYS), text=True)

# Factories so tests can inject a fake client and session in place of the real ones.
ClientFactory = Callable[..., Roku]
SessionFactory = Callable[[], ClientSession]


class RokuSession(BaseSession):
    """A live connection to a Roku; maps generic keys to ECP remote tokens."""

    def __init__(
        self, client: Roku, session: ClientSession, capabilities: Capabilities
    ) -> None:
        super().__init__(capabilities)
        self._client = client
        self._session = session

    async def _dispatch_key(self, key: Key) -> None:
        await self._client.remote(ROKU_KEYS[key])

    async def _dispatch_text(self, text: str) -> None:
        try:
            await self._client.literal(text)
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this Roku"
            ) from exc

    async def _release(self) -> None:
        # We own the aiohttp session (the client was handed one, so its own
        # close_session is a no-op); close it directly.
        await self._session.close()


class RokuAdapter:
    """Builds Roku sessions; no pairing, since ECP is unauthenticated."""

    platform = PLATFORM
    display_name = "Roku"
    requires_pairing = False
    reachability_port = 8060  # ECP HTTP port

    def __init__(
        self,
        client_factory: ClientFactory = Roku,
        session_factory: SessionFactory = ClientSession,
    ) -> None:
        self._client_factory = client_factory
        self._session_factory = session_factory

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def pair(self, device: "Device", *, prompt=None) -> str:
        # Roku needs no pairing; the UI never calls this. Fail loudly if reached.
        raise PairingCancelledError("Roku requires no pairing")

    async def connect(self, device: "Device") -> RokuSession:
        session = self._session_factory()
        client = self._client_factory(host=device.ip, session=session)
        # rokuecp bounds the request itself; a transport failure or timeout both
        # surface as a RokuError. Close the session we own before giving up.
        try:
            await client.update()
        except RokuError as exc:
            await session.close()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return RokuSession(client, session, _CAPABILITIES)


def register(registry: "AdapterRegistry") -> None:
    registry.register(RokuAdapter())
