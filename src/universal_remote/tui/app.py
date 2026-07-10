"""The root Textual application, holding the device store and adapter registry."""

from __future__ import annotations

from textual.app import App

from typing import Callable

from ..devices.probe import ProbeResult, probe_device
from ..devices.store import DeviceStore
from ..registry import AdapterRegistry
from ..registry import registry as default_registry
from .menu import MenuScreen


class UniversalRemoteApp(App[None]):
    """Launches into the entry menu; screens read `store` and `registry` off the app."""

    CSS = """
    Screen { align: center middle; }
    #menu { width: auto; height: auto; }
    #menu Button { width: 28; margin: 1 0; }
    #title { text-style: bold; margin-bottom: 1; }
    """

    def __init__(
        self,
        store: DeviceStore | None = None,
        registry: AdapterRegistry | None = None,
        probe: Callable[[str], ProbeResult | None] | None = None,
    ) -> None:
        super().__init__()
        self.store = store or DeviceStore()
        self.registry = registry or default_registry
        self.probe = probe or probe_device

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
