"""Amazon Fire TV adapter — drives the device's remote-control REST API.

Fire OS exposes the undocumented HTTPS API that Amazon's own remote app uses, so
this adapter needs no ADB and no developer mode (see `firetv_api` for the transport).
Pairing shows a PIN on the television that the user reads back — the same PIN shape
as Apple TV and Android TV — and yields a short opaque token later connections
replay in a header.

The API is one request per key with no persistent connection, which is why a session
holds only its HTTP transport. The device's remote service can stop while idle, so a
request that finds it gone re-wakes the device and is sent once more.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar

from ..capabilities import Capabilities
from ..discovery import DiscoveredDevice, MdnsHit, browse_mdns
from ..errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
)
from ..keys import Key
from ..session import BaseSession
from .firetv_api import (
    DIAL_PORT,
    KEYBOARD_STATE_TEXT,
    WAKE_TIMEOUT,
    AiohttpTransport,
    CommandRejectedError,
    PortProbe,
    RemoteApi,
    ServiceUnavailableError,
    Transport,
    TransportFactory,
    tcp_port_open,
)

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "firetv"
CLIENT_NAME = "Universal Remote"  # the label the television shows when pairing
PAIR_PROMPT = "Enter the PIN shown on your Fire TV"
NO_FIELD_MESSAGE = "No text field is focused on this Fire TV"
# The Amazon mDNS service; the friendly name is in the TXT "n" key, since the
# instance name is a device code (e.g. "AFTMM").
DISCOVERY_SERVICE = "_amzn-wplay._tcp.local."
_NAME_TXT_KEY = "n"

# Generic key -> remote-control API action, dispatched as `?action=<action>`.
# Volume up, volume down, and mute are absent: the device reports it cannot control
# volume (`isVolumeControlsSupported: false`) and was verified to ignore them. The
# combined play/pause key and stop are absent because the API offers no action for
# either, and the channel keys because a streamer has no tuner.
FIRETV_ACTIONS: dict[Key, str] = {
    Key.UP: "dpad_up",
    Key.DOWN: "dpad_down",
    Key.LEFT: "dpad_left",
    Key.RIGHT: "dpad_right",
    Key.OK: "select",
    Key.BACK: "back",
    Key.HOME: "home",
    Key.MENU: "menu",
    # The API has no scrub action — every candidate returns 400 — but a Fire TV
    # player skips ±10s per d-pad press, so scrubbing rides that convention.
    Key.FAST_FORWARD: "dpad_right",
    Key.REWIND: "dpad_left",
}

# Generic key -> media action. Play and pause live on their own route.
FIRETV_MEDIA_ACTIONS: dict[Key, str] = {Key.PLAY: "play", Key.PAUSE: "pause"}

# Generic key -> the character a digit types. The API exposes no arbitrary-keycode
# path, so digits go into the focused text field like any other character, which
# means they only work while a field holds focus (see FireTvSession).
DIGIT_KEYS: dict[Key, str] = {Key[f"NUM_{digit}"]: str(digit) for digit in range(10)}

_CAPABILITIES = Capabilities(
    keys=frozenset(FIRETV_ACTIONS)
    | frozenset(FIRETV_MEDIA_ACTIONS)
    | frozenset(DIGIT_KEYS),
    text=True,
)

# The mDNS browse seam, injected so discovery is testable without a live network.
MdnsBrowser = Callable[[str, float], Awaitable[list[MdnsHit]]]

_Result = TypeVar("_Result")


class FireTvSession(BaseSession):
    """A session over a Fire TV's remote-control API.

    Owns the HTTP transport and nothing else — the API keeps no connection open, so
    releasing the session is closing that transport.
    """

    def __init__(
        self, api: RemoteApi, capabilities: Capabilities, transport: Transport
    ) -> None:
        super().__init__(capabilities)
        self._api = api
        self._transport = transport

    async def _dispatch_key(self, key: Key) -> None:
        if key in DIGIT_KEYS:
            await self._type_digit(DIGIT_KEYS[key])
        elif key in FIRETV_MEDIA_ACTIONS:
            await self._retrying(
                lambda: self._api.send_media(FIRETV_MEDIA_ACTIONS[key])
            )
        else:
            await self._retrying(lambda: self._api.send_action(FIRETV_ACTIONS[key]))

    async def _dispatch_text(self, text: str) -> None:
        # A write with nothing focused returns a hollow 200 and types nothing, so the
        # field's state is read first and a missing field reported rather than faked.
        await self._retrying(self._focused_text)
        await self._retrying(lambda: self._api.set_keyboard_text(text))

    async def _type_digit(self, digit: str) -> None:
        """Type one digit by writing the field's contents back with it appended.

        The keyboard route replaces the field rather than appending to it, and offers
        no append mode, so the current contents have to be read first.
        """
        current = await self._retrying(self._focused_text)
        await self._retrying(lambda: self._api.set_keyboard_text(current + digit))

    async def _focused_text(self) -> str:
        state, text = await self._api.keyboard_state()
        if state != KEYBOARD_STATE_TEXT:
            raise TextUnsupportedError(NO_FIELD_MESSAGE)
        return text

    async def _retrying(self, send: Callable[[], Awaitable[_Result]]) -> _Result:
        """Send one request, re-waking and retrying it once if the service has gone.

        Only a transport failure is retried: a request the device answered and refused
        would be refused again. Retried requests are individual and idempotent — each
        keyboard write sends the whole intended value, never a delta.
        """
        try:
            return await send()
        except ServiceUnavailableError:
            await self._api.wake()
            return await send()

    async def _release(self) -> None:
        await self._transport.close()


class FireTvAdapter:
    """Builds Fire TV sessions; pairing yields the client token to persist."""

    platform = PLATFORM
    display_name = "Fire TV"
    # DIAL, which a stock device answers whether or not the remote service has been
    # woken; the control port is closed until then, so it would read unreachable.
    reachability_port = DIAL_PORT

    def __init__(
        self,
        transport_factory: TransportFactory = AiohttpTransport,
        browse: MdnsBrowser = browse_mdns,
        port_open: PortProbe = tcp_port_open,
        wake_timeout: float = WAKE_TIMEOUT,
    ) -> None:
        self._transport_factory = transport_factory
        self._browse = browse
        self._port_open = port_open
        self._wake_timeout = wake_timeout

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def discover(self, timeout: float) -> list[DiscoveredDevice]:
        # The friendly name is in the TXT "n" key; a blank one falls back to the IP.
        hits = await self._browse(DISCOVERY_SERVICE, timeout)
        return [
            DiscoveredDevice(
                name=hit.properties.get(_NAME_TXT_KEY, ""),
                platform=PLATFORM,
                ip=hit.ip,
            )
            for hit in hits
        ]

    async def pair(self, device: "Device", *, prompt=None) -> str:
        # A PIN adapter cannot pair without a way to ask for the PIN.
        if prompt is None:
            raise PairingCancelledError()
        transport = self._transport_factory()
        try:
            return await self._exchange_pin(self._api(device.ip, transport), prompt)
        finally:
            await transport.close()

    async def connect(self, device: "Device") -> FireTvSession:
        transport = self._transport_factory()
        api = self._api(device.ip, transport, device.credential)
        try:
            await api.wake()
            # An authenticated read, so a stale or missing token is refused here
            # rather than mid-session on the first keypress.
            await api.info()
        except Exception as exc:
            await transport.close()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return FireTvSession(api, _CAPABILITIES, transport)

    async def _exchange_pin(self, api: RemoteApi, prompt) -> str:
        await api.wake()
        await api.display_pin(CLIENT_NAME)  # the television now shows its PIN
        try:
            token = await api.verify_pin(await prompt(PAIR_PROMPT))
        except CommandRejectedError as exc:
            raise PairingCancelledError("The Fire TV did not accept that PIN") from exc
        if not token:
            # A wrong PIN is answered with an empty token rather than a failed request.
            raise PairingCancelledError("The Fire TV did not accept that PIN")
        return token

    def _api(
        self, ip: str, transport: Transport, token: str | None = None
    ) -> RemoteApi:
        return RemoteApi(
            ip,
            transport,
            token=token,
            port_open=self._port_open,
            wake_timeout=self._wake_timeout,
        )


def register(registry: "AdapterRegistry") -> None:
    registry.register(FireTvAdapter())
