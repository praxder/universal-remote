"""Resolves a device's platform identifier to a registered adapter."""

from __future__ import annotations

from .adapter import Adapter
from .errors import UnsupportedPlatformError


class AdapterRegistry:
    """Maps platform identifiers to adapters without the UI or store knowing brands."""

    def __init__(self) -> None:
        self._adapters: dict[str, Adapter] = {}

    def register(self, adapter: Adapter) -> None:
        self._adapters[adapter.platform] = adapter

    def resolve(self, platform: str) -> Adapter:
        try:
            return self._adapters[platform]
        except KeyError as exc:
            raise UnsupportedPlatformError(platform) from exc

    def is_supported(self, platform: str) -> bool:
        return platform in self._adapters

    def platforms(self) -> list[str]:
        return list(self._adapters)

    def adapters(self) -> list[Adapter]:
        return list(self._adapters.values())


# The default registry adapters register into at startup.
registry = AdapterRegistry()
