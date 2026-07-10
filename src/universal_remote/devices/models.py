"""The saved-device model."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Device:
    """A saved TV: identity, how to reach it, and its pairing credential."""

    name: str
    platform: str
    ip: str
    mac: str | None = None
    model: str | None = None
    credential: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        return cls(**data)
