"""The root Textual application, holding the device store and adapter registry."""

from __future__ import annotations

from textual.app import App, SystemCommand
from textual.screen import Screen

from typing import Callable, Iterable

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
    #devices-title { width: 36; text-align: left; margin: 1 0 1 0; }
    /* wider than #devices-title so the "Add/Edit Device" banner never wraps */
    #add-title { width: 52; text-align: left; margin: 1 0 2 0; }
    /* wide enough for the "Select Device" banner; padded above and below */
    #use-remote-title { width: 58; text-align: left; margin: 1 0 1 0; }
    /* wide enough for the "Discover" banner; padded like the Devices banner */
    #discover-title { width: 40; text-align: left; margin: 1 0 1 0; }
    /* the "searching" indicator: an animated spinner + bold text, hidden once done */
    #discover-status { height: 1; margin-top: 1; }
    #discover-status LoadingIndicator { width: 8; height: 1; color: $accent; }
    #discover-status-text {
        width: auto; height: 1; margin-left: 2;
        text-style: bold; color: $accent;
    }
    /* slight left indent on Save to offset it from the fields above */
    #add-device #save { margin: 1 0 0 1; }
    /* duplicate-save error: hidden until there is a message, then shown in red */
    #add-device #error { display: none; color: $error; margin: 1 0 0 0; }
    #quote { width: 42; text-align: center; margin-top: 1; color: $text-muted; }
    /* delete confirmation: dim the device list behind a centered dialog box */
    ConfirmDeleteScreen { align: center middle; background: $background 60%; }
    #confirm-delete {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #confirm-message { text-align: center; margin-bottom: 1; }
    #confirm-delete Button { width: 16; margin-top: 1; }
    /* connecting: dim the device list behind a centered dialog box */
    ConnectingModal { align: center middle; background: $background 60%; }
    #connecting {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface; align: center middle;
    }
    #connecting-loading, #connecting-error { width: auto; height: auto; align: center middle; }
    #connecting LoadingIndicator { height: 1; margin-bottom: 1; }
    #connect-error { text-align: center; margin-bottom: 1; }
    #connecting Button { width: 16; margin-top: 1; }
    #cancel-row { width: 100%; }  /* full width so its centered button centers in the box */
    #error-buttons { width: 100%; }  /* full width so the retry/back column centers in the box */
    /* pairing: dim the device selection behind a centered dialog box */
    PairingScreen { align: center middle; background: $background 60%; }
    #pairing {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    /* guidance sets the box width; title/buttons fill it and center their content */
    #pairing-guidance { text-align: center; }
    #pairing-title { width: 100%; text-align: center; }
    /* PIN entry: hidden until an adapter (e.g. Apple TV) asks for a PIN */
    #pin-entry { display: none; width: 100%; height: auto; }
    #pin-entry Input { width: 100%; margin-top: 1; }
    #pairing #submit, #pairing #cancel { width: 100%; margin-top: 1; }
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

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Drop the Maximize and Screenshot commands from the command palette."""
        for command in super().get_system_commands(screen):
            if command.title in ("Maximize", "Screenshot"):
                continue
            yield command

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
