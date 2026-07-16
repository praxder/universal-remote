"""In-memory test doubles for the adapter seam — no real TV required."""

from __future__ import annotations

import asyncio

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

    async def _dispatch_key(self, key: Key) -> None:
        if self.dispatch_error is not None:
            raise self.dispatch_error
        self.sent_keys.append(key)

    async def _dispatch_text(self, text: str) -> None:
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


class FakeAdbSigner:
    """Stands in for `PythonRSASigner`; records the key material it was built from.

    A fresh pair builds it with a public key (so the TV can whitelist it); a
    connect replay builds it with the private key only, so a test can tell the
    two flows apart by whether `pub` is present.
    """

    def __init__(self, pub: str | None = None, priv: str | None = None) -> None:
        self.pub = pub
        self.priv = priv


def fake_keygen() -> tuple[str, str]:
    """Deterministic ADB keypair stand-in, returning (public, private) contents."""
    return "fake-public-key", "fake-private-pem"


# A `getevent -lp` listing with a d-pad-capable input node, so node discovery
# finds one and the fast `sendevent` path is exercised by default.
FAKE_GETEVENT_LP = """add device 1: /dev/input/event4
  name:     "amzkeyboard"
    KEY (0001): KEY_UP KEY_DOWN KEY_LEFT KEY_RIGHT KEY_ENTER KEY_SELECT KEY_BACK
add device 2: /dev/input/event3
  name:     "kcmouse"
    KEY (0001): BTN_MOUSE
"""


class FakeAdbDevice:
    """Stands in for `AdbDeviceTcpAsync`; records connects and dispatched commands."""

    def __init__(
        self,
        host: str,
        port: int = 5555,
        getevent_lp: str = FAKE_GETEVENT_LP,
        **_kwargs,
    ) -> None:
        self.host = host
        self.port = port
        # `getevent -lp` output used for input-node discovery at connect time.
        self.getevent_lp = getevent_lp
        # Each connect records the signer keys and auth timeout it was called with,
        # so a test can distinguish pair-time (public key present) from connect-time.
        self.connects: list[dict] = []
        self.commands: list[str] = []
        self.closed = False
        # When set, the connect handshake raises it — stands in for an unreachable,
        # refused, timed-out, or auth-rejected device.
        self.connect_error: Exception | None = None
        # When True, `input text` raises — stands in for an unfocused text field.
        self.reject_text = False

    async def connect(self, rsa_keys=None, auth_timeout_s=None, **_kwargs) -> bool:
        if self.connect_error is not None:
            raise self.connect_error
        self.connects.append({"rsa_keys": rsa_keys, "auth_timeout_s": auth_timeout_s})
        return True

    async def shell(self, command: str, **_kwargs) -> str:
        if command == "getevent -lp":
            return self.getevent_lp  # discovery probe, not a dispatched key
        if self.reject_text and command.startswith("input text"):
            raise RuntimeError("no focused text field")
        self.commands.append(command)
        return ""

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
    """Stands in for a scanned `BaseConfig`: carries an identity and takes credentials."""

    def __init__(self, identifier: str = "atv-id-123") -> None:
        self.identifier = identifier
        self.applied_credentials: dict[object, str] = {}

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


class FakeAndroidTvRemote:
    """Stands in for `androidtvremote2.AndroidTVRemote`; drives pairing and records sends.

    `async_generate_cert_if_missing` writes cert and key files to the constructed
    paths exactly as the real library does, so the adapter's pair flow reads them
    back to build the credential. Key and text sends are synchronous, matching the
    library, and `disconnect` is idempotent.
    """

    def __init__(
        self,
        client_name: str,
        certfile: str,
        keyfile: str,
        host: str,
        connect_error: Exception | None = None,
        reject_text: bool = False,
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
        self.sent_text: list[str] = []
        # When set, async_connect raises it — an unreachable, refused, timed-out,
        # or unauthorized device (the real library's CannotConnect/InvalidAuth).
        self.connect_error = connect_error
        # When True, send_text raises — stands in for an unfocused IME.
        self.reject_text = reject_text

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

    def send_key_command(self, key_code, direction=3) -> None:
        self.sent_keys.append(key_code)

    def send_text(self, text: str) -> None:
        if self.reject_text:
            raise RuntimeError("no focused IME")
        self.sent_text.append(text)

    def disconnect(self) -> None:
        self.disconnected = True


class FakeAndroidTvRemoteFactory:
    """Builds `FakeAndroidTvRemote`s and records each, so tests inspect the flow.

    Pairing and connect each construct one remote; `remotes[-1]` is the latest.
    """

    def __init__(
        self,
        connect_error: Exception | None = None,
        reject_text: bool = False,
    ) -> None:
        self.connect_error = connect_error
        self.reject_text = reject_text
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
            reject_text=self.reject_text,
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
