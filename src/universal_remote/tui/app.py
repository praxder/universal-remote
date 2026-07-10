"""The root Textual application, holding the device store and adapter registry."""

from __future__ import annotations

from textual.app import App

from typing import Callable

from ..devices.store import DeviceStore
from ..registry import AdapterRegistry
from ..registry import registry as default_registry
from .menu import MenuScreen
from .quotes import Quote, random_quote


class UniversalRemoteApp(App[None]):
    """Launches into the entry menu; screens read `store` and `registry` off the app."""

    TITLE = "Universal Remote"

    CSS = """
    Screen { align: center middle; }
    #menu { width: 100%; height: auto; }
    #menu Button { width: 28; margin: 1 0; }
    /* #title width matches the TITLE_ART banner so it never wraps */
    #title { width: 42; text-align: center; margin-bottom: 1; }
    /* left-aligned so the multi-width banner lines keep their column alignment */
    #devices-title { width: 36; text-align: left; margin: 1 0 2 0; }
    /* wider than #devices-title so the "Add/Edit Device" banner never wraps */
    #add-title { width: 52; text-align: left; margin: 1 0 2 0; }
    /* indent Save so its left edge lines up with the cells' text above it */
    #add-device #save { margin: 1 0 0 3; }
    #quote { width: 42; text-align: center; margin-top: 1; color: $text-muted; }
    /* delete confirmation: dim the device list behind a centered dialog box */
    ConfirmDeleteScreen { align: center middle; background: $background 60%; }
    #confirm-delete {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #confirm-message { text-align: center; margin-bottom: 1; }
    #confirm-delete Button { width: 16; margin-top: 1; }
    """

    def __init__(
        self,
        store: DeviceStore | None = None,
        registry: AdapterRegistry | None = None,
        quote_provider: Callable[[], Quote | None] | None = None,
    ) -> None:
        super().__init__()
        self.store = store or DeviceStore()
        self.registry = registry or default_registry
        self.quote_provider = quote_provider or random_quote

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
