"""The saved-device model."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class Device:
    """A saved TV: identity, how to reach it, and its pairing credential."""

    name: str
    platform: str
    ip: str
    credential: str | None = None
    identifier: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    # Opt-in: send text over the system `adb` binary instead of Remote v2, so text
    # lands even when the Android TV "use your phone" IME overlay is up.
    text_via_adb: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        known = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})
