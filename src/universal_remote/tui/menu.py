"""The entry menu: Manage Devices and Use Remote, by key or by click."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from .devices_screen import DeviceListScreen
from .remote_flow import UseRemoteScreen
from .settings_screen import SettingsScreen
from .shortcuts import Scope, rebuild_shortcuts

TITLE_ART = r""" _   _       _                          _ 
| | | |_ __ (_)_   _____ _ __ ___  __ _| |
| | | | '_ \| \ \ / / _ \ '__/ __|/ _` | |
| |_| | | | | |\ V /  __/ |  \__ \ (_| | |
 \___/|_| |_|_| \_/ \___|_|  |___/\__,_|_|

 ____                      _       
|  _ \ ___ _ __ ___   ___ | |_ ___ 
| |_) / _ \ '_ ` _ \ / _ \| __/ _ \
|  _ <  __/ | | | | | (_) | ||  __/
|_| \_\___|_| |_| |_|\___/ \__\___|"""


class MenuScreen(Screen[None]):
    # The Manage Devices / Use Remote / Settings / Quit hotkeys are catalogued Home
    # actions, built from the override map on mount (see `on_mount`); only the
    # focus-navigation keys stay hard-coded here.
    SHORTCUT_SCOPES = frozenset({Scope.HOME})

    BINDINGS = [
        Binding("up", "app.focus_previous", "Previous", show=False),
        Binding("down", "app.focus_next", "Next", show=False),
        Binding("k", "app.focus_previous", "Previous", show=False),
        Binding("h", "app.focus_previous", "Previous", show=False),
        Binding("j", "app.focus_next", "Next", show=False),
        Binding("l", "app.focus_next", "Next", show=False),
    ]

    def on_mount(self) -> None:
        rebuild_shortcuts(self, self.app.shortcut_overrides, self.SHORTCUT_SCOPES)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu"):
            with Center():
                yield Static(TITLE_ART, id="title")
            with Center():
                yield Button("Manage Devices", id="manage")
            with Center():
                yield Button("Use Remote", id="use")
            quote = self.app.quote_provider()
            if quote:
                with Center():
                    yield Static(
                        f'"{escape(quote.text)}"\n'
                        f"— {escape(quote.character)}, {escape(quote.source)}",
                        id="quote",
                    )
        # Docked bottom-left above the Footer; kept out of #menu so the centered
        # title/buttons/quote are unaffected.
        with Horizontal(id="settings-bar"):
            yield Button("Settings", id="settings")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "manage":
            self.action_manage_devices()
        elif event.button.id == "use":
            self.action_use_remote()
        elif event.button.id == "settings":
            self.action_settings()

    def action_manage_devices(self) -> None:
        self.app.push_screen(DeviceListScreen())

    def action_use_remote(self) -> None:
        self.app.push_screen(UseRemoteScreen())

    def action_settings(self) -> None:
        self.app.push_screen(SettingsScreen())
