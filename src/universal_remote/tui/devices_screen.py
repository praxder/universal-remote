"""Manage Devices screens: list saved devices and add/edit/delete them."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Select
from textual.widgets.option_list import Option

from ..devices.models import Device


class DeviceListScreen(Screen[None]):
    BINDINGS = [
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("delete", "delete", "Delete"),
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="devices"):
            yield Label("Manage Devices", id="devices-title")
            yield OptionList(id="device-list")
            yield Label("", id="devices-empty")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def on_screen_resume(self) -> None:
        self._reload()

    def _reload(self) -> None:
        option_list = self.query_one("#device-list", OptionList)
        option_list.clear_options()
        devices = self.app.store.list()
        for device in devices:
            option_list.add_option(Option(device.name, id=device.id))
        if devices:
            option_list.highlighted = 0
        empty = self.query_one("#devices-empty", Label)
        empty.update("No devices yet — press 'a' to add one." if not devices else "")

    def _selected(self) -> Device | None:
        option_list = self.query_one("#device-list", OptionList)
        if option_list.highlighted is None:
            return None
        option = option_list.get_option_at_index(option_list.highlighted)
        return next((d for d in self.app.store.list() if d.id == option.id), None)

    def action_add(self) -> None:
        self.app.push_screen(AddDeviceScreen())

    def action_edit(self) -> None:
        device = self._selected()
        if device is not None:
            self.app.push_screen(AddDeviceScreen(existing=device))

    def action_delete(self) -> None:
        device = self._selected()
        if device is not None:
            self.app.store.delete(device.id)
            self._reload()

    def action_back(self) -> None:
        self.app.pop_screen()


class AddDeviceScreen(Screen[None]):
    """IP entry with info-probe auto-fill, then confirm and save (add or edit)."""

    BINDINGS = [("escape", "back", "Back")]

    def __init__(self, existing: Device | None = None) -> None:
        super().__init__()
        self._existing = existing

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="add-device"):
            yield Label(
                "Edit Device" if self._existing else "Add Device", id="add-title"
            )
            yield Input(placeholder="IP address", id="ip")
            yield Button("Probe", id="probe")
            yield Input(placeholder="Name", id="name")
            yield Input(placeholder="Model", id="model")
            yield Input(placeholder="MAC", id="mac")
            yield from self._platform_selector()
            yield Button("Save", id="save")
        yield Footer()

    def _platform_selector(self):
        """A platform picker, shown when adding a device (hidden while editing)."""
        if self._existing is not None:
            return
        platforms = self.app.registry.platforms()
        yield Select(
            [(platform, platform) for platform in platforms],
            value=platforms[0],
            allow_blank=False,
            id="platform",
        )

    def on_mount(self) -> None:
        if self._existing is not None:
            self.query_one("#ip", Input).value = self._existing.ip
            self.query_one("#name", Input).value = self._existing.name
            self.query_one("#model", Input).value = self._existing.model or ""
            self.query_one("#mac", Input).value = self._existing.mac or ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "probe":
            self._probe()
        elif event.button.id == "save":
            self._save()

    def _probe(self) -> None:
        ip = self.query_one("#ip", Input).value.strip()
        if not ip:
            return
        result = self.app.probe(ip)
        if result is None:
            return  # probe failed → leave fields for manual entry, never block
        if result.name:
            self.query_one("#name", Input).value = result.name
        if result.model:
            self.query_one("#model", Input).value = result.model
        if result.mac:
            self.query_one("#mac", Input).value = result.mac

    def _selected_platform(self) -> str:
        return self.query_one("#platform", Select).value

    def _save(self) -> None:
        ip = self.query_one("#ip", Input).value.strip()
        name = self.query_one("#name", Input).value.strip() or ip
        model = self.query_one("#model", Input).value.strip() or None
        mac = self.query_one("#mac", Input).value.strip() or None
        if self._existing is not None:
            self._existing.name = name
            self._existing.ip = ip
            self._existing.model = model
            self._existing.mac = mac
            self.app.store.update(self._existing)
        else:
            self.app.store.add(
                Device(
                    name=name,
                    platform=self._selected_platform(),
                    ip=ip,
                    mac=mac,
                    model=model,
                )
            )
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()
