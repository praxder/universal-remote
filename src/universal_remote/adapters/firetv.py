"""Amazon Fire TV adapter — drives the device's remote-control REST API.

Fire OS exposes the undocumented HTTPS API that Amazon's own remote app uses, so
this adapter needs no ADB and no developer mode (see `firetv_api` for the transport).
Pairing shows a PIN on the television that the user reads back — the same PIN shape
as Apple TV and Android TV — and yields a short opaque token later connections
replay in a header.

The API is one request per key with no persistent connection, which is why a session
holds only its HTTP transport. The device's remote service can stop while idle, so a
request that finds it gone re-wakes the device and is sent once more.

Two platforms answer it identically for every navigation and transport key, so only
text entry branches. An Android Fire OS device takes a whole string in one keyboard
write and reports the field's contents back, which is what confirms the send landed.
A Vega accepts that same write and discards it, and takes text through a route that
carries one character at a time and appends it — so no character may be sent twice,
and a failure part-way through a string can only say that part of it may already have
been typed. A Vega reports neither which field has focus nor what one holds, so a
send there is reported as successful without a read-back that cannot be obtained.
Which of the two writers a session holds is settled once, while connecting.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol, TypeVar

from ..capabilities import Capabilities
from ..discovery import DiscoveredDevice, MdnsHit, browse_mdns
from ..errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
    UniversalRemoteError,
)
from ..keys import Key
from ..session import BaseSession
from .firetv_api import (
    DIAL_PORT,
    KEYBOARD_STATE_HIDDEN,
    PLATFORM_TYPE_NATIVE,
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
DISCARDED_MESSAGE = "The Fire TV discarded the text — refocus the field, then retry"
VEGA_CHARACTER_MESSAGE = "This Fire TV can only type printable ASCII characters"
VEGA_PARTIAL_MESSAGE = (
    "The Fire TV stopped answering — part of the text may already have been typed"
)
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


async def _retrying(api: RemoteApi, send: Callable[[], Awaitable[_Result]]) -> _Result:
    """Send one request, re-waking and retrying it once if the service has gone.

    Only a transport failure is retried: a request the device answered and refused
    would be refused again. Retried requests are individual and idempotent — each
    keyboard write sends the whole intended value, never a delta. The Vega text path
    sends deltas, which is why it does not come through here.
    """
    try:
        return await send()
    except ServiceUnavailableError:
        await api.wake()
        return await send()


class TextWriter(Protocol):
    """How a session enters text; which one it holds is settled at connect.

    A digit is its own operation rather than one-character text, because on the
    keyboard path a write replaces the field — routing a digit through `send_text`
    there would wipe a search box the user had already typed into.
    """

    async def send_text(self, text: str) -> None: ...

    async def type_digit(self, digit: str) -> None: ...


class KeyboardTextWriter:
    """Enters text by setting the focused field's contents, then reading them back.

    The path an Android Fire OS Fire TV answers: one write carries the whole value,
    and the field reports what it holds, so a send can be confirmed.
    """

    def __init__(self, api: RemoteApi) -> None:
        self._api = api

    async def send_text(self, text: str) -> None:
        await _retrying(self._api, lambda: self._api.set_keyboard_text(text))
        await self._confirm(text)

    async def type_digit(self, digit: str) -> None:
        """Type one digit by writing the field's contents back with it appended.

        The keyboard route replaces the field rather than appending to it, and offers
        no append mode, so the current contents have to be read first.
        """
        _state, current = await _retrying(self._api, self._api.keyboard_state)
        await self.send_text(current + digit)

    async def _confirm(self, expected: str) -> None:
        """Read the field back, since a write that typed nothing also answers 200.

        The reported state cannot carry this: a field with focus that has never been
        typed into reports `visible` rather than `text`, so trusting the state name
        refuses the commonest case — opening search and typing from the remote. What
        the field actually holds is the one honest signal.
        """
        state, text = await _retrying(self._api, self._api.keyboard_state)
        # Checked before the contents, so an empty send cannot confirm itself against
        # the empty contents a device with nothing focused reports.
        if state == KEYBOARD_STATE_HIDDEN:
            raise TextUnsupportedError(NO_FIELD_MESSAGE)
        if text != expected:
            raise TextUnsupportedError(DISCARDED_MESSAGE)


def _refuse_unacceptable(text: str) -> None:
    """Refuse the whole send when the text holds a character the route rejects.

    A Vega answers non-ASCII with `500 Error in performing the operation on the Fire
    TV`, so the check runs before the first request: reported afterwards it would
    arrive over a half-typed field the user has to clear by hand. Printable ASCII
    rather than everything `str.isascii()` admits, since control characters pass that
    test and were never exercised on the device.
    """
    if all(character.isascii() and character.isprintable() for character in text):
        return
    raise TextUnsupportedError(VEGA_CHARACTER_MESSAGE)


class VegaTextWriter:
    """Enters text one character at a time over the Vega single-character route.

    The route appends, so no character may be sent twice: an ambiguous transport
    failure — the device typed it, the answer was lost — would repeat it, and the
    re-wake a retry performs launches a DIAL app that can move focus while the rest
    of the string is still queued. The service is readied once up front instead, and
    a failure part-way through says what the adapter cannot check for itself.

    Nothing here reads the keyboard state: a Vega reports it hidden with null
    contents whether or not a field has focus, so it can neither confirm a send nor
    refuse one.
    """

    def __init__(self, api: RemoteApi) -> None:
        self._api = api

    async def send_text(self, text: str) -> None:
        _refuse_unacceptable(text)
        await self._api.wake()
        try:
            for character in text:
                await self._api.type_character(character)
        except UniversalRemoteError as exc:
            # Any failure here leaves the same half-typed field, whether the device
            # went away or refused the character.
            raise TextUnsupportedError(VEGA_PARTIAL_MESSAGE) from exc

    async def type_digit(self, digit: str) -> None:
        """One request: the route takes a single character, and a digit is one.

        Not sent through `_retrying`, for the reason a string is not: the route
        appends, so a digit the device typed before its answer was lost would land
        twice. A press that finds the remote service stopped therefore fails outright
        rather than re-waking, which the keyboard path's read-modify-write recovers
        from.
        """
        await self._api.type_character(digit)


async def _text_writer(api: RemoteApi, info: dict[str, Any]) -> TextWriter:
    """Choose the device's text path, once, from the platform it reports.

    The properties route is asked only when the device's own info says it exists,
    since an Android Fire OS device answers it 405. A read that fails is suppressed
    rather than left to fail the connection: a device whose platform could not be
    established keeps the keyboard path, so every navigation and transport key still
    works — the larger share of the remote — and only text entry is wrong.
    """
    if info.get("isPropertiesApiSupported"):
        with suppress(UniversalRemoteError):
            properties = await api.properties()
            if properties.get("platformType") == PLATFORM_TYPE_NATIVE:
                return VegaTextWriter(api)
    return KeyboardTextWriter(api)


class FireTvSession(BaseSession):
    """A session over a Fire TV's remote-control API.

    Owns the HTTP transport and nothing else — the API keeps no connection open, so
    releasing the session is closing that transport. The text writer it holds was
    chosen for the device's platform while connecting.
    """

    def __init__(
        self,
        api: RemoteApi,
        capabilities: Capabilities,
        transport: Transport,
        writer: TextWriter,
    ) -> None:
        super().__init__(capabilities)
        self._api = api
        self._transport = transport
        self._writer = writer

    async def _dispatch_key(self, key: Key) -> None:
        if key in DIGIT_KEYS:
            await self._writer.type_digit(DIGIT_KEYS[key])
        elif key in FIRETV_MEDIA_ACTIONS:
            await _retrying(
                self._api, lambda: self._api.send_media(FIRETV_MEDIA_ACTIONS[key])
            )
        else:
            await _retrying(
                self._api, lambda: self._api.send_action(FIRETV_ACTIONS[key])
            )

    async def _dispatch_text(self, text: str) -> None:
        await self._writer.send_text(text)

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
            # rather than mid-session on the first keypress. Its body also says
            # whether this device answers the properties route.
            info = await api.info()
            # Inside the try so a failure it does not suppress still closes the
            # transport, rather than leaking it out of a connect that never returns.
            writer = await _text_writer(api, info.body)
        except Exception as exc:
            await transport.close()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return FireTvSession(api, _CAPABILITIES, transport, writer)

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
