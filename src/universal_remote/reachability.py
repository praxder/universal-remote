"""Non-invasive network reachability: a bounded TCP connect probe, no session.

Standalone by design — no imports from `adapters` or `tui` — so it stays unit-
testable without a running app and free of platform concerns.
"""

from __future__ import annotations

import asyncio
from enum import Enum, auto


class Reachability(Enum):
    """Whether a saved device is on the network, without connecting to it."""

    REACHABLE = auto()
    UNREACHABLE = auto()
    UNKNOWN = auto()


async def probe(ip: str, port: int, timeout: float) -> Reachability:
    """Report reachable if a TCP connection to `ip:port` opens within `timeout`.

    A refused connection, a timeout, or any network error yields unreachable.
    No pairing, credential, or control session is involved; the transport opened
    to prove reachability is closed immediately.
    """
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout
        )
    except (asyncio.TimeoutError, OSError):
        return Reachability.UNREACHABLE
    writer.close()
    return Reachability.REACHABLE
