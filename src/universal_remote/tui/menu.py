"""The entry menu: Manage Devices and Use Remote, by key or by click."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label

from .devices_screen import DeviceListScreen
from .remote_flow import UseRemoteScreen


class MenuScreen(Screen[None]):
    BINDINGS = [
        ("d", "manage_devices", "Manage Devices"),
        ("r", "use_remote", "Use Remote"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu"):
            yield Label("Universal Remote", id="title")
            yield Button("Manage Devices", id="manage")
            yield Button("Use Remote", id="use")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "manage":
            self.action_manage_devices()
        elif event.button.id == "use":
            self.action_use_remote()

    def action_manage_devices(self) -> None:
        self.app.push_screen(DeviceListScreen())

    def action_use_remote(self) -> None:
        self.app.push_screen(UseRemoteScreen())
