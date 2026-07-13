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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        known = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})
