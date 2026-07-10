"""What an adapter declares it can do, readable without connecting."""

from __future__ import annotations

from dataclasses import dataclass

from .keys import Key


@dataclass(frozen=True)
class Capabilities:
    """Keys an adapter supports plus its text flag."""

    keys: frozenset[Key]
    text: bool = False

    def supports(self, key: Key) -> bool:
        return key in self.keys
