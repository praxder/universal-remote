"""Manage Devices screens: list saved devices and add/edit/delete them."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Select,
    Static,
    Switch,
)
from textual.widgets.option_list import Option

from ..devices.models import Device
from .device_option_list import DeviceOptionList

ADD_ID = "__add__"

TITLE_ART = r""" ____             _
|  _ \  _____   _(_) ___ ___  ___
| | | |/ _ \ \ / / |/ __/ _ \/ __|
| |_| |  __/\ V /| | (_|  __/\__ \
|____/ \___| \_/ |_|\___\___||___/"""

ADD_TITLE_ART = r"""    _       _     _   ____             _
   / \   __| | __| | |  _ \  _____   _(_) ___ ___
  / _ \ / _` |/ _` | | | | |/ _ \ \ / / |/ __/ _ \
 / ___ \ (_| | (_| | | |_| |  __/\ V /| | (_|  __/
/_/   \_\__,_|\__,_| |____/ \___| \_/ |_|\___\___|"""

EDIT_TITLE_ART = r""" _____    _ _ _     ____             _
| ____|__| (_) |_  |  _ \  _____   _(_) ___ ___
|  _| / _` | | __| | | | |/ _ \ \ / / |/ __/ _ \
| |__| (_| | | |_  | |_| |  __/\ V /| | (_|  __/
|_____\__,_|_|\__| |____/ \___| \_/ |_|\___\___|"""


class DeviceListScreen(Screen[None]):
    BINDINGS = [
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("backspace", "delete", "Delete"),
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="devices"):
            yield Static(TITLE_ART, id="devices-title")
            yield DeviceOptionList(id="device-list")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def on_screen_resume(self) -> None:
        self._reload()

    def _reload(self) -> None:
        option_list = self.query_one("#device-list", DeviceOptionList)
        option_list.clear_options()
        devices = self.app.store.list()
        for i, device in enumerate(devices):
            option_list.add_option(Option(f"{i + 1}. {device.name}", id=device.id))
        option_list.device_count = len(devices)
        if devices:
            option_list.add_option(None)  # divider between devices and the add row
        option_list.add_option(Option("+ Add", id=ADD_ID))
        option_list.highlighted = 0

    def _selected(self) -> Device | None:
        option_list = self.query_one("#device-list", OptionList)
        if option_list.highlighted is None:
            return None
        option = option_list.get_option_at_index(option_list.highlighted)
        return next((d for d in self.app.store.list() if d.id == option.id), None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == ADD_ID:
            self.action_add()
            return
        device = next(
            (d for d in self.app.store.list() if d.id == event.option.id), None
        )
        if device is not None:
            self.app.push_screen(AddDeviceScreen(existing=device))

    def action_add(self) -> None:
        # The add entry opens discovery first; manual entry is its last row. Imported
        # lazily because discover_screen imports AddDeviceScreen from this module.
        from .discover_screen import DiscoverScreen

        self.app.push_screen(DiscoverScreen())

    def action_edit(self) -> None:
        device = self._selected()
        if device is not None:
            self.app.push_screen(AddDeviceScreen(existing=device))

    def action_delete(self) -> None:
        device = self._selected()
        if device is None:
            return

        def _on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self.app.store.delete(device.id)
                self._reload()

        self.app.push_screen(ConfirmDeleteScreen(device.name), _on_confirm)

    def action_back(self) -> None:
        self.app.pop_screen()


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Confirm removing a device before it is deleted from the store."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("up", "focus_previous", "Previous"),
        ("left", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
        ("right", "focus_next", "Next"),
        Binding("k", "focus_previous", "Previous", show=False),
        Binding("h", "focus_previous", "Previous", show=False),
        Binding("j", "focus_next", "Next", show=False),
        Binding("l", "focus_next", "Next", show=False),
    ]

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self._device_name = device_name

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-delete"):
            yield Label(f"Delete {self._device_name}?", id="confirm-message")
            yield Button("Delete", id="confirm", variant="error")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_focus_next(self) -> None:
        self.focus_next()


class AdbTextSetupScreen(ModalScreen[bool]):
    """One-time ADB wireless-debugging pairing so text lands under the IME overlay.

    Guides the user to enable Developer options → Wireless debugging → Pair with
    code, collects the pairing address and code, and runs the adapter's ADB pairing.
    Dismisses with True on success and False on cancel; on failure it stays with a
    status. Persistence is the caller's job (the Add/Edit form records the opt-in on
    Save), so this screen only performs the pairing and reports the outcome.
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    _GUIDANCE = (
        "On the TV: Settings → System → Developer options → Wireless debugging → "
        "Pair device with pairing code. Enter the address and code it shows here."
    )

    def __init__(self, platform: str) -> None:
        super().__init__()
        self._platform = platform

    def compose(self) -> ComposeResult:
        with Vertical(id="adb-setup"):
            yield Label("Set up text input (ADB)", id="adb-setup-title")
            yield Label(self._GUIDANCE, id="adb-setup-guidance")
            yield Input(
                placeholder="Pairing address (e.g. 10.0.0.5:37000)", id="adb-address"
            )
            yield Input(placeholder="Pairing code", id="adb-code")
            yield Label("", id="adb-setup-status")
            yield Button("Set up", id="adb-setup-submit")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#adb-address", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "adb-setup-submit":
            await self._setup()
        elif event.button.id == "cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(False)

    async def _setup(self) -> None:
        address = self.query_one("#adb-address", Input).value.strip()
        code = self.query_one("#adb-code", Input).value.strip()
        adapter = self.app.registry.resolve(self._platform)
        self._status("Pairing…")
        if await adapter.pair_adb(address, code):
            self.dismiss(True)
        else:
            self._status("Pairing failed — check the address and code, then try again.")

    def _status(self, message: str) -> None:
        self.query_one("#adb-setup-status", Label).update(message)


class AdbTextHintScreen(ModalScreen[None]):
    """One-time hint after adding an Android TV device: text can be routed over ADB.

    Confirms the add and points the user to the Edit screen's text-input toggle, so a
    device whose text gets swallowed by the IME overlay has a discoverable remedy.
    """

    BINDINGS = [("escape,enter", "ok", "OK")]

    _BODY = (
        "If text input has trouble typing in some apps, edit this device in "
        "Manage Devices and switch text input to ADB."
    )

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self._device_name = device_name

    def compose(self) -> ComposeResult:
        with Vertical(id="adb-hint"):
            yield Label(f'Added "{self._device_name}"', id="adb-hint-title")
            yield Label(self._BODY, id="adb-hint-body")
            yield Button("OK", id="adb-hint-ok")

    def on_mount(self) -> None:
        self.query_one("#adb-hint-ok", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_ok()

    def action_ok(self) -> None:
        self.dismiss(None)


class DeviceTypeSelect(Select):
    """A Select that moves field focus on Up/Down and opens on Enter/Space.

    The base Select binds Up/Down to open its overlay, which would trap focus in
    the add form. Here Up/Down navigate the form instead; once the overlay is
    open, its own Up/Down still move between options.
    """

    BINDINGS = [
        Binding("enter,space", "show_overlay", "Show menu", show=False),
        Binding("up", "focus_previous_field", "Previous", show=False),
        Binding("down", "focus_next_field", "Next", show=False),
    ]

    def action_focus_previous_field(self) -> None:
        self.screen.focus_previous()

    def action_focus_next_field(self) -> None:
        self.screen.focus_next()


class AddDeviceScreen(Screen[None]):
    """Manual device-type, Name, and IP entry, then save (add or edit)."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("up", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
    ]

    def __init__(self, existing: Device | None = None) -> None:
        super().__init__()
        self._existing = existing
        # In-memory opt-in for ADB text; written to the device on Save. Seeded from
        # the existing device so editing reflects its current mode.
        self._opted_in = existing.text_via_adb if existing is not None else False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="add-device"):
            yield Static(
                EDIT_TITLE_ART if self._existing else ADD_TITLE_ART, id="add-title"
            )
            yield from self._device_type_cell()
            yield Input(placeholder="Name", id="name")
            yield Input(placeholder="IP address", id="ip")
            # Shown only for Android TV (see _update_text_adb_visibility). The initial
            # value is set via the constructor so mounting an opted-in device does not
            # fire Switch.Changed (which would re-open the pairing modal).
            with Horizontal(id="text-adb-cell"):
                yield Label("Send text over ADB", id="text-adb-label")
                yield Switch(value=self._opted_in, id="text-adb-switch")
            yield Label("", id="error")
            yield Button("Save", id="save")
        yield Footer()

    def _device_type_cell(self):
        """A platform picker when adding; a read-only label when editing."""
        if self._existing is not None:
            adapter = self.app.registry.resolve(self._existing.platform)
            yield Input(
                value=adapter.display_name, disabled=True, id="platform-display"
            )
            return
        adapters = self.app.registry.adapters()
        yield DeviceTypeSelect(
            [(adapter.display_name, adapter.platform) for adapter in adapters],
            value=adapters[0].platform,
            allow_blank=False,
            id="platform",
        )

    def on_mount(self) -> None:
        if self._existing is not None:
            self.query_one("#ip", Input).value = self._existing.ip
            self.query_one("#name", Input).value = self._existing.name
        self._update_text_adb_visibility()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._save()

    def on_select_changed(self, event: Select.Changed) -> None:
        # Only the add-form platform picker; changing type re-evaluates the toggle.
        if event.select.id == "platform":
            self._update_text_adb_visibility()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id != "text-adb-switch":
            return
        if event.value:
            # Switching to ADB requires a live pairing; the modal reports the outcome.
            self.app.push_screen(
                AdbTextSetupScreen(self._current_platform()), self._on_adb_setup_done
            )
        else:
            self._opted_in = False

    def _on_adb_setup_done(self, paired: bool | None) -> None:
        if paired:
            self._opted_in = True
        else:
            # Cancelled or failed: revert to standard, leaving the device not opted in.
            self._opted_in = False
            self.query_one("#text-adb-switch", Switch).value = False

    def _current_platform(self) -> str:
        if self._existing is not None:
            return self._existing.platform
        return self.query_one("#platform", Select).value

    def _update_text_adb_visibility(self) -> None:
        adapter = self.app.registry.resolve(self._current_platform())
        supported = getattr(adapter, "supports_adb_text", False)
        self.query_one("#text-adb-cell").display = supported
        if not supported and self._opted_in:
            # A hidden toggle must not carry a stale opt-in from another type.
            self._opted_in = False
            self.query_one("#text-adb-switch", Switch).value = False

    def _save(self) -> None:
        ip = self.query_one("#ip", Input).value.strip()
        name = self.query_one("#name", Input).value.strip() or ip
        exclude_id = self._existing.id if self._existing is not None else None
        conflict = self.app.store.find_conflict(name, ip, exclude_id=exclude_id)
        if conflict is not None:
            error = self.query_one("#error", Label)
            error.update(conflict)
            error.display = True
            return
        added = self._existing is None
        if self._existing is not None:
            self._existing.name = name
            self._existing.ip = ip
            self._existing.text_via_adb = self._opted_in
            self.app.store.update(self._existing)
        else:
            self.app.store.add(
                Device(
                    name=name,
                    platform=self._current_platform(),
                    ip=ip,
                    text_via_adb=self._opted_in,
                )
            )
        self.app.pop_screen()
        if added:
            self.app.notify(f'Added "{name}".')

    def action_focus_previous(self) -> None:
        self.focus_previous()

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_back(self) -> None:
        self.app.pop_screen()
