"""The Settings screen: theme, a key-bindings placeholder, links, and version."""

from __future__ import annotations

import webbrowser
from importlib.metadata import version
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

TITLE_ART = r""" ____       _   _   _
/ ___|  ___| |_| |_(_)_ __   __ _ ___
\___ \ / _ \ __| __| | '_ \ / _` / __|
 ___) |  __/ |_| |_| | | | | (_| \__ \
|____/ \___|\__|\__|_|_| |_|\__, |___/
                            |___/"""

REPO_URL = "https://github.com/praxder/universal-remote"
LICENSES_URL = f"{REPO_URL}/blob/main/THIRD_PARTY_LICENSES.md"


class SettingsScreen(Screen[None]):
    """App-level settings, reached from the home menu."""

    BINDINGS = [
        Binding("escape,q", "back", "Back"),
        Binding("up", "app.focus_previous", "Previous", show=False),
        Binding("down", "app.focus_next", "Next", show=False),
        Binding("k", "app.focus_previous", "Previous", show=False),
        Binding("h", "app.focus_previous", "Previous", show=False),
        Binding("j", "app.focus_next", "Next", show=False),
        Binding("l", "app.focus_next", "Next", show=False),
    ]

    def __init__(self, url_opener: Callable[[str], object] | None = None) -> None:
        super().__init__()
        self._open_url = url_opener or webbrowser.open

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings"):
            with Center():
                yield Static(TITLE_ART, id="settings-title")
            with Center():
                yield Button("Theme", id="theme")
            with Center():
                yield Button(
                    "Key Bindings (coming soon)", id="keybindings", disabled=True
                )
            with Center():
                yield Button("Third-party licenses", id="licenses")
            with Center():
                yield Button("Open in GitHub", id="repo")
            with Center():
                yield Static(f"Version {version('universal-remote')}", id="version")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "theme":
            self.app.search_themes()
        elif event.button.id == "licenses":
            self._open_url(LICENSES_URL)
        elif event.button.id == "repo":
            self._open_url(REPO_URL)

    def action_back(self) -> None:
        self.app.pop_screen()
