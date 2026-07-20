"""Console entry point: register adapters, then launch the Textual app."""

from __future__ import annotations

import argparse
from importlib.metadata import version

from .adapters.androidtv import register as register_androidtv
from .adapters.appletv import register as register_appletv
from .adapters.firetv import register as register_firetv
from .adapters.lg import register as register_lg
from .adapters.roku import register as register_roku
from .adapters.samsung import register as register_samsung
from .devices.store import DeviceStore
from .registry import registry
from .tui.app import UniversalRemoteApp


def build_app(store: DeviceStore | None = None) -> UniversalRemoteApp:
    """Register the known adapters with the core registry and build the app."""
    register_samsung(registry)
    register_lg(registry)
    register_appletv(registry)
    register_roku(registry)
    register_firetv(registry)
    register_androidtv(registry)
    return UniversalRemoteApp(store=store, registry=registry)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Handle ``--version``/``--help`` before the TUI; both exit before returning."""
    parser = argparse.ArgumentParser(
        prog="universal-remote",
        description="A local, terminal-based universal TV remote.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('universal-remote')}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    _parse_args(argv)
    build_app().run()
