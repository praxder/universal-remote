"""The adapter seam: a platform's entry point to pairing and connecting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Protocol, runtime_checkable

from .capabilities import Capabilities
from .session import Session

if TYPE_CHECKING:
    from .devices.models import Device

# A hook the TUI supplies so an adapter can request a value (e.g. a PIN) during
# pairing. Samsung ignores it (popup only); a future PIN-based adapter uses it.
Prompt = Callable[[str], Awaitable[str]]


# An adapter may optionally declare `requires_pairing = False` (e.g. Roku, whose
# ECP is unauthenticated and issues no credential); the Use-Remote flow then
# connects directly instead of running pairing. Adapters that omit it are treated
# as requiring pairing (read via `getattr(adapter, "requires_pairing", True)`), so
# the popup/PIN adapters need not declare anything.
@runtime_checkable
class Adapter(Protocol):
    """Builds sessions for one TV platform; pairing is distinct from connecting."""

    platform: str
    display_name: str

    def capabilities(self) -> Capabilities: ...

    async def pair(self, device: "Device", *, prompt: Prompt | None = None) -> str: ...

    async def connect(self, device: "Device") -> Session: ...
