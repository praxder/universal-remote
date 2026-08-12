"""The session seam: what an open connection to a device can do."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .capabilities import Capabilities
from .errors import SessionClosedError, TextUnsupportedError, UnsupportedKeyError
from .keys import Key


@runtime_checkable
class Session(Protocol):
    """An open connection able to send keys and text, and to be closed."""

    async def send_key(self, key: Key) -> None: ...

    async def send_text(self, text: str) -> None: ...

    async def close(self) -> None: ...


class BaseSession:
    """Gates sends against declared capabilities and session lifecycle.

    Subclasses implement the `_dispatch_*` and `_release` hooks; gating stays here
    so every adapter rejects unsupported keys and closed-session sends identically.
    """

    def __init__(self, capabilities: Capabilities) -> None:
        self._capabilities = capabilities
        self._closed = False

    async def send_key(self, key: Key) -> None:
        self._ensure_open()
        if not self._capabilities.supports(key):
            raise UnsupportedKeyError(key)
        await self._dispatch_key(key)

    async def send_text(self, text: str) -> None:
        self._ensure_open()
        if not self._capabilities.text:
            raise TextUnsupportedError()
        await self._dispatch_text(text)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._release()

    def _ensure_open(self) -> None:
        if self._closed:
            raise SessionClosedError()

    async def _dispatch_key(self, key: Key) -> None:
        raise NotImplementedError

    async def _dispatch_text(self, text: str) -> None:
        raise NotImplementedError

    async def _release(self) -> None:
        pass
