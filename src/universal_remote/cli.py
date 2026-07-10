"""Console entry point: register adapters, then launch the Textual app."""

from __future__ import annotations

from .adapters.lg import register as register_lg
from .adapters.samsung import register as register_samsung
from .devices.store import DeviceStore
from .registry import registry
from .tui.app import UniversalRemoteApp


def build_app(store: DeviceStore | None = None) -> UniversalRemoteApp:
    """Register the known adapters with the core registry and build the app."""
    register_samsung(registry)
    register_lg(registry)
    return UniversalRemoteApp(store=store, registry=registry)


def main() -> None:
    build_app().run()
