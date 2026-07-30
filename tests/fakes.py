"""In-memory test doubles for the adapter seam — no real TV required."""

from __future__ import annotations

import asyncio
from ipaddress import ip_address

from androidtvremote2 import remotemessage_pb2 as pb
from pyatv.const import Protocol

from universal_remote.adapters.firetv_api import (
    KEYBOARD_PATH,
    PIN_VERIFY_PATH,
    Request,
    Response,
)
from universal_remote.capabilities import Capabilities
from universal_remote.errors import PairingCancelledError
from universal_remote.keys import Key
from universal_remote.session import BaseSession


class FakeSession(BaseSession):
    """Records the keys and text sent through it; gating comes from BaseSession."""

    def __init__(self, capabilities: Capabilities) -> None:
        super().__init__(capabilities)
        self.sent_keys: list[Key] = []
        self.sent_text: list[str] = []
        self.closed = False
        # When set, dispatching any key raises it — stands in for a device-side
        # failure (timeout, dropped connection) the on-screen remote must survive.
        self.dispatch_error: Exception | None = None
        # The text-entry counterpart: when set, sending text raises it, standing in
        # for an unexpected device-side text failure the remote must survive.
        self.text_dispatch_error: Exception | None = None

    async def _dispatch_key(self, key: Key) -> None:
        if self.dispatch_error is not None:
            raise self.dispatch_error
        self.sent_keys.append(key)

    async def _dispatch_text(self, text: str) -> None:
        if self.text_dispatch_error is not None:
            raise self.text_dispatch_error
        self.sent_text.append(text)

    async def _release(self) -> None:
        self.closed = True


class FakeSamsungRemote:
    """Stands in for `SamsungTVWSAsyncRemote`; records sends and simulates the popup."""

    def __init__(
        self,
        host: str,
        token: str | None = None,
        token_file: str | None = None,
        port: int = 8001,
        timeout: float | None = None,
        key_press_delay: float = 1,
        name: str = "SamsungTvRemote",
    ) -> None:
        self.host = host
        self.token = token
        self.port = port
        self.timeout = timeout
        self.name = name
        self.opened = False
        self.closed = False
        self.popup_shown = False
        self.sent_payloads: list[str] = []
        self.send_error: Exception | None = None
        self.open_error: Exception | None = None

    async def open(self) -> object:
        # The real library enforces the connect timeout internally; a fake stands
        # in for that by raising a preset error (transport failure or timeout).
        if self.open_error is not None:
            raise self.open_error
        self.opened = True
        if self.token is None:
            # No token supplied → the TV shows its authorization popup and, on
            # accept, hands back a token.
            self.popup_shown = True
            self.token = "fresh-token"
        return object()

    async def send_command(self, command) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent_payloads.append(command.get_payload())

    async def close(self) -> None:
        self.closed = True


class FakeWebOsClient:
    """Stands in for `aiowebostv.WebOsClient`; records sends and simulates pairing."""

    def __init__(self, host: str, client_key: str | None = None, **_kwargs) -> None:
        self.host = host
        self.client_key = client_key
        self.connected = False
        self.disconnected = False
        self.prompt_shown = False
        self.sent_buttons: list[str] = []
        self.sent_text: list[str] = []
        self.send_error: Exception | None = None
        self.connect_error: Exception | None = None
        self.connect_hangs = False

    async def connect(self) -> bool:
        if self.connect_error is not None:
            raise self.connect_error
        if self.connect_hangs:
            # Block indefinitely so the adapter's own timeout must abort us.
            await asyncio.sleep(3600)
        self.connected = True
        if self.client_key is None:
            # No client-key supplied → the TV shows its authorization prompt and,
            # on accept, registers and hands back a client-key.
            self.prompt_shown = True
            self.client_key = "fresh-client-key"
        return True

    async def button(self, name: str) -> None:
        self.sent_buttons.append(name)

    async def request(self, uri: str, payload=None, **_kwargs) -> dict:
        if self.send_error is not None:
            raise self.send_error
        self.sent_text.append(payload["text"] if payload else "")
        return {}

    async def disconnect(self) -> None:
        self.disconnected = True


class FakeClientSession:
    """Stands in for `aiohttp.ClientSession`; records only that it was closed."""

    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeRoku:
    """Stands in for `rokuecp.Roku`; records sends and answers the reachability check."""

    def __init__(self, host: str, session: object | None = None, **_kwargs) -> None:
        self.host = host
        self.session = session  # the aiohttp session the client was built for
        self.sent_keys: list[str] = []
        self.sent_text: list[str] = []
        self.updated = False
        # When set, the reachability check (update) raises it — stands in for an
        # unreachable, refused, or timed-out device.
        self.update_error: Exception | None = None
        # When True, literal text entry raises — stands in for an unfocused keyboard.
        self.reject_text = False

    async def update(self, full_update: bool = False) -> object:
        if self.update_error is not None:
            raise self.update_error
        self.updated = True
        return object()

    async def remote(self, key: str) -> None:
        self.sent_keys.append(key)

    async def literal(self, text: str) -> None:
        if self.reject_text:
            raise RuntimeError("keyboard not focused")
        self.sent_text.append(text)


async def firetv_port_open(_ip: str, _port: int, _timeout: float) -> bool:
    """Fire TV control-port probe stand-in: it accepts at once, so no wake polling."""
    return True


class FakeFireTvTransport:
    """Stands in for the Fire TV HTTP transport; records requests, answers by route.

    Every request is recorded, so a test can assert the URL, headers, and body the
    API built. Routes answer 200 with what the device returns: a keyboard read
    reports the focused field's state and contents, and a PIN verify reports the
    pairing token in its `description`.
    """

    def __init__(
        self,
        *,
        keyboard: dict[str, str] | None = None,
        token: str = "AB1CD2E",
    ) -> None:
        self.requests: list[Request] = []
        # What a keyboard read reports; a "hidden" state stands in for a device with
        # no text field focused.
        self.keyboard = keyboard or {"state": "text", "text": ""}
        self.token = token
        self.closed = False
        # A URL fragment whose requests the device answers 400 — a rejected action.
        self.reject: str | None = None
        # A URL fragment whose first request fails at the transport, standing in for
        # a remote service that stopped while the session was idle.
        self.fail_once: str | None = None
        # A URL fragment whose every request fails at the transport, standing in for
        # a service that stays gone however often it is re-woken.
        self.fail: str | None = None
        self._failed = False

    async def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        if self.fail and self.fail in request.url:
            raise OSError("connection refused")
        if self.fail_once and self.fail_once in request.url and not self._failed:
            self._failed = True
            raise OSError("connection refused")
        if self.reject and self.reject in request.url:
            return Response(400, {})
        return Response(200, self._body(request))

    def _body(self, request: Request) -> dict[str, str]:
        if request.method == "GET" and request.url.endswith(KEYBOARD_PATH):
            return dict(self.keyboard)
        if request.url.endswith(PIN_VERIFY_PATH):
            return {"description": self.token}
        return {}

    async def close(self) -> None:
        self.closed = True


class _MethodRecorder:
    """Spy for a `pyatv` interface: records the names of async methods called on it.

    A wrong method name records happily, so tests assert the exact pyatv strings
    (e.g. `"select"`, `"menu"`, `"volume_up"`) to catch a mismapped key.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __getattr__(self, name: str):
        async def record(*_args, **_kwargs) -> None:
            self.calls.append(name)

        return record


class FakeAppleTvKeyboard:
    """Records text set on the device; can reject to exercise best-effort text."""

    def __init__(self, reject_text: bool = False) -> None:
        self.reject_text = reject_text
        self.text: list[str] = []

    async def text_set(self, text: str) -> None:
        if self.reject_text:
            raise RuntimeError("keyboard not focused")
        self.text.append(text)


class FakeAppleTv:
    """Stands in for `pyatv`'s connected `AppleTV`; volume routes through `remote_control`."""

    def __init__(self, reject_text: bool = False) -> None:
        self.remote_control = _MethodRecorder()
        self.audio = _MethodRecorder()
        self.keyboard = FakeAppleTvKeyboard(reject_text)
        self.closed = False

    def close(self) -> set:  # pyatv's close() is synchronous, returning tasks
        self.closed = True
        return set()


class FakeAppleTvConfig:
    """Stands in for a scanned `BaseConfig`: identity, address, and taken credentials.

    `address` is a real `IPv4Address` like pyatv's, so an adapter that forgets to
    `str()` it is caught rather than silently passing.
    """

    def __init__(
        self,
        identifier: str = "atv-id-123",
        name: str = "Apple TV",
        address: str = "10.0.0.5",
        has_companion: bool = True,
    ) -> None:
        self.identifier = identifier
        self.name = name
        self.address = ip_address(address)
        self.applied_credentials: dict[object, str] = {}
        # A genuine Apple TV exposes Companion; an AirPlay-only device (an LG/Samsung
        # TV answering pyatv's scan via AirPlay 2) does not.
        self._has_companion = has_companion

    def get_service(self, protocol: object) -> object | None:
        if protocol is Protocol.Companion and self._has_companion:
            return object()
        return None

    def set_credentials(self, protocol: object, credentials: str) -> bool:
        self.applied_credentials[protocol] = credentials
        return True


class FakeAppleTvService:
    """The pairing handler's service; its credential appears once pairing finishes."""

    def __init__(self) -> None:
        self.credentials: str | None = None


class FakePairingHandler:
    """Drives the two-phase Companion PIN pairing: begin → pin → finish."""

    def __init__(self, credentials: str = "companion-cred") -> None:
        self.device_provides_pin = True
        self.began = False
        self.finished = False
        self.closed = False
        self.pin_value: int | None = None
        self._credentials = credentials
        self.service = FakeAppleTvService()

    async def begin(self) -> None:
        self.began = True

    def pin(self, value: int) -> None:
        self.pin_value = value

    async def finish(self) -> None:
        self.finished = True
        self.service.credentials = self._credentials

    @property
    def has_paired(self) -> bool:
        return self.finished

    async def close(self) -> None:
        self.closed = True


class FakePyatv:
    """Stands in for the `pyatv` module: scan/pair/connect over the confirmed API."""

    def __init__(
        self,
        config: FakeAppleTvConfig | None = None,
        atv: FakeAppleTv | None = None,
        pairing: FakePairingHandler | None = None,
        connect_error: Exception | None = None,
        scan_empty: bool = False,
    ) -> None:
        self.config = config or FakeAppleTvConfig()
        self.atv = atv or FakeAppleTv()
        self.pairing = pairing or FakePairingHandler()
        self.connect_error = connect_error
        self.scan_empty = scan_empty
        self.scanned_hosts: list[list[str] | None] = []

    async def scan(self, loop, hosts=None, **_kwargs) -> list[FakeAppleTvConfig]:
        self.scanned_hosts.append(hosts)
        return [] if self.scan_empty else [self.config]

    async def pair(self, config, protocol, loop, **_kwargs) -> FakePairingHandler:
        return self.pairing

    async def connect(self, config, loop, **_kwargs) -> FakeAppleTv:
        if self.connect_error is not None:
            raise self.connect_error
        return self.atv


def ime_show_request(counter: int, value: str) -> pb.RemoteMessage:
    """The device's field-state report, sent after every edit from any source."""
    message = pb.RemoteMessage()
    status = message.remote_ime_show_request.remote_text_field_status
    status.counter_field = counter
    status.value = value
    status.start = len(value)
    status.end = len(value)
    return message


def ime_key_inject(
    counter: int,
    value: str,
    app_counter: int = 1,
    package: str = "com.example.app",
) -> pb.RemoteMessage:
    """The device's report when a text field gains focus.

    Carries both the field's state and the focused editor's own counter
    (`app_info.counter`), which is the value an edit's `ime_counter` must match.
    """
    message = pb.RemoteMessage()
    inject = message.remote_ime_key_inject
    inject.app_info.app_package = package
    inject.app_info.counter = app_counter
    status = inject.text_field_status
    status.counter_field = counter
    status.value = value
    status.start = len(value)
    status.end = len(value)
    return message


def foreground_app(package: str, app_counter: int = 1) -> pb.RemoteMessage:
    """A key-inject carrying only the foreground app — no text field is focused.

    What the device sends in an app whose text field cannot be focused over Remote
    v2 (YouTube's search box), so field state must not be inferred from this.
    """
    message = pb.RemoteMessage()
    message.remote_ime_key_inject.app_info.app_package = package
    message.remote_ime_key_inject.app_info.counter = app_counter
    return message


class FakeRemoteProtocol:
    """Stands in for `androidtvremote2`'s `RemoteProtocol`, the text seam's contact point.

    Records outbound messages and delivers inbound ones the way the real transport
    does — serialized bytes through `_handle_message` — so a seam that taps that hook
    is exercised against the library's real protobuf types.
    """

    def __init__(self, ime_counter: int = 0, echo: bool = True) -> None:
        # The library keeps this fresh from inbound batch edits; the seam reads it.
        self.ime_counter = ime_counter
        self.sent: list[pb.RemoteMessage] = []
        # Raw bytes the library's own handler received, so a tap that swallows
        # inbound messages (breaking ping replies and key state) is caught.
        self.handled: list[bytes] = []
        # When set, sending raises it — stands in for a torn-down transport.
        self.send_error: Exception | None = None
        # Whether an accepted edit is reported back the way the device reports one.
        # False stands in for a device that discards the edit in silence.
        self.echo = echo
        self._echo_counter = 0
        self._echo_value = ""

    def _handle_message(self, raw_msg: bytes) -> None:
        self.handled.append(raw_msg)

    def _send_message(
        self, msg: pb.RemoteMessage, should_debug_log: bool = True
    ) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(msg)
        if self.echo and msg.HasField("remote_ime_batch_edit"):
            self._echo(msg.remote_ime_batch_edit)

    def _echo(self, edit: pb.RemoteImeBatchEdit) -> None:
        """Report the edit back the way the device reports one it accepted."""
        inserted = edit.edit_info[0].text_field_status.value if edit.edit_info else ""
        # The counter advances by an unpredictable step, so never by exactly one.
        self.receive(
            ime_show_request(self._echo_counter + 3, self._echo_value + inserted)
        )

    def receive(self, message: pb.RemoteMessage) -> None:
        """Deliver `message` inbound exactly as the transport would."""
        status = None
        if message.remote_ime_key_inject.HasField("text_field_status"):
            status = message.remote_ime_key_inject.text_field_status
        elif message.remote_ime_show_request.HasField("remote_text_field_status"):
            status = message.remote_ime_show_request.remote_text_field_status
        if status is not None:
            # Track what the device would now hold, so a later echo appends to it.
            self._echo_counter = status.counter_field
            self._echo_value = status.value
        self._handle_message(message.SerializeToString())


class FakeAndroidTvRemote:
    """Stands in for `androidtvremote2.AndroidTVRemote`; drives pairing and records sends.

    `async_generate_cert_if_missing` writes cert and key files to the constructed
    paths exactly as the real library does, so the adapter's pair flow reads them
    back to build the credential. Key sends are synchronous, matching the library,
    and `disconnect` is idempotent. The protocol object appears only once connected,
    as it does in the library, so the text seam cannot be installed before then.
    """

    def __init__(
        self,
        client_name: str,
        certfile: str,
        keyfile: str,
        host: str,
        connect_error: Exception | None = None,
    ) -> None:
        self.client_name = client_name
        self.certfile = certfile
        self.keyfile = keyfile
        self.host = host
        self.cert_generated = False
        self.pairing_started = False
        self.finished_code: str | None = None
        self.connected = False
        self.disconnected = False
        self.sent_keys: list[str] = []
        self._remote_message_protocol: FakeRemoteProtocol | None = None
        # When set, async_connect raises it — an unreachable, refused, timed-out,
        # or unauthorized device (the real library's CannotConnect/InvalidAuth).
        self.connect_error = connect_error

    async def async_generate_cert_if_missing(self) -> bool:
        # Multi-line PEM shape (like the real library), so a credential packed from
        # it exercises real newline escaping when the store serializes it to JSON.
        with open(self.certfile, "w") as cert_file:
            cert_file.write(
                "-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----\n"
            )
        with open(self.keyfile, "w") as key_file:
            key_file.write(
                "-----BEGIN PRIVATE KEY-----\nZmFrZQ==\n-----END PRIVATE KEY-----\n"
            )
        self.cert_generated = True
        return True

    async def async_start_pairing(self) -> None:
        self.pairing_started = True

    async def async_finish_pairing(self, pairing_code: str) -> None:
        self.finished_code = pairing_code

    async def async_connect(self) -> None:
        if self.connect_error is not None:
            raise self.connect_error
        self.connected = True
        self._remote_message_protocol = FakeRemoteProtocol()

    def send_key_command(self, key_code, direction=3) -> None:
        self.sent_keys.append(key_code)

    def disconnect(self) -> None:
        self.disconnected = True


class FakeAndroidTvRemoteFactory:
    """Builds `FakeAndroidTvRemote`s and records each, so tests inspect the flow.

    Pairing and connect each construct one remote; `remotes[-1]` is the latest.
    """

    def __init__(self, connect_error: Exception | None = None) -> None:
        self.connect_error = connect_error
        self.remotes: list[FakeAndroidTvRemote] = []

    def __call__(
        self, *, client_name: str, certfile: str, keyfile: str, host: str, **_kwargs
    ) -> FakeAndroidTvRemote:
        remote = FakeAndroidTvRemote(
            client_name,
            certfile,
            keyfile,
            host,
            connect_error=self.connect_error,
        )
        self.remotes.append(remote)
        return remote


class FakeAdapter:
    """A configurable adapter double with a scriptable pair result."""

    def __init__(
        self,
        platform: str = "fake-tv",
        capabilities: Capabilities | None = None,
        pair_token: str = "fake-token",
        pair_cancels: bool = False,
        connect_error: Exception | None = None,
        display_name: str | None = None,
        prompt_message: str | None = None,
        pair_identifier: str | None = None,
        requires_pairing: bool = True,
        reachability_port: int | None = None,
    ) -> None:
        self.platform = platform
        self.display_name = display_name or platform
        self.requires_pairing = requires_pairing
        # None mirrors an adapter that declares no port (device stays unknown).
        self.reachability_port = reachability_port
        self._capabilities = capabilities or Capabilities(
            keys=frozenset(Key), text=True
        )
        self._pair_token = pair_token
        self._pair_cancels = pair_cancels
        self.connect_error = connect_error
        # When set, pair asks for a value through the prompt (a PIN adapter);
        # when None it pairs popup-only like Samsung/LG.
        self._prompt_message = prompt_message
        self._pair_identifier = pair_identifier
        # When set, connect blocks on this event so a test can keep a connect
        # in flight (e.g. to exercise cancellation).
        self.connect_gate: asyncio.Event | None = None
        self.paired_devices: list[object] = []
        self.entered_values: list[str] = []
        self.sessions: list[FakeSession] = []

    def capabilities(self) -> Capabilities:
        return self._capabilities

    async def pair(self, device: object = None, *, prompt=None) -> str:
        if self._pair_cancels:
            raise PairingCancelledError()
        if self._prompt_message is not None:
            if prompt is None:
                raise PairingCancelledError()
            self.entered_values.append(await prompt(self._prompt_message))
            if self._pair_identifier is not None and device is not None:
                device.identifier = self._pair_identifier
        self.paired_devices.append(device)
        return self._pair_token

    async def connect(self, device: object = None) -> FakeSession:
        if self.connect_error is not None:
            raise self.connect_error
        if self.connect_gate is not None:
            await self.connect_gate.wait()
        session = FakeSession(self._capabilities)
        self.sessions.append(session)
        return session


class FakeDiscoverAdapter:
    """An adapter double that discovers canned devices, optionally gated mid-scan.

    Only the surface the discovery screen touches — `platform`, `display_name`, and
    `discover` — is provided. Pass a held `asyncio.Event` as `gate` to keep the scan
    in flight so a test can assert streaming/manual-row behaviour before it finishes.
    """

    def __init__(
        self,
        platform: str = "fake-tv",
        display_name: str | None = None,
        devices: list | None = None,
        gate: asyncio.Event | None = None,
    ) -> None:
        self.platform = platform
        self.display_name = display_name or platform
        self._devices = devices or []
        self.gate = gate

    async def discover(self, timeout: float) -> list:
        if self.gate is not None:
            await self.gate.wait()
        return list(self._devices)
