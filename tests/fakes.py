"""In-memory test doubles for the adapter seam — no real TV required."""

from __future__ import annotations

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

    async def _dispatch_key(self, key: Key) -> None:
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
        self.name = name
        self.opened = False
        self.closed = False
        self.popup_shown = False
        self.sent_payloads: list[str] = []
        self.send_error: Exception | None = None

    async def open(self) -> object:
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


class FakeAdapter:
    """A configurable adapter double with a scriptable pair result."""

    def __init__(
        self,
        platform: str = "fake-tv",
        capabilities: Capabilities | None = None,
        pair_token: str = "fake-token",
        pair_cancels: bool = False,
    ) -> None:
        self.platform = platform
        self._capabilities = capabilities or Capabilities(
            keys=frozenset(Key), text=True, power_on=True
        )
        self._pair_token = pair_token
        self._pair_cancels = pair_cancels
        self.paired_devices: list[object] = []
        self.sessions: list[FakeSession] = []

    def capabilities(self) -> Capabilities:
        return self._capabilities

    async def pair(self, device: object = None, *, prompt=None) -> str:
        if self._pair_cancels:
            raise PairingCancelledError()
        self.paired_devices.append(device)
        return self._pair_token

    async def connect(self, device: object = None) -> FakeSession:
        session = FakeSession(self._capabilities)
        self.sessions.append(session)
        return session
