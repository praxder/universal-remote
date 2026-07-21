"""The Settings screen: theme, a key-bindings placeholder, links, and version."""

from __future__ import annotations

import webbrowser
from importlib.metadata import version
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
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

    BINDINGS = [Binding("escape,q", "back", "Back")]

    def __init__(self, url_opener: Callable[[str], object] | None = None) -> None:
        super().__init__()
        self._open_url = url_opener or webbrowser.open

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings"):
            yield Static(TITLE_ART, id="settings-title")
            yield Button("Theme", id="theme")
            yield Button("Key Bindings (coming soon)", id="keybindings", disabled=True)
            yield Button("Third-party licenses", id="licenses")
            yield Button("GitHub repo", id="repo")
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
