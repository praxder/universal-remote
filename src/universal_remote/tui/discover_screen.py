"""Discover devices on the network, then add one by selecting it (manual fallback).

Sits between the saved-device list and the manual add form: one worker per adapter
scans the LAN concurrently (the reachability-picker idiom), and rows stream into the
list as each scan answers. "+ Add manually" is always the last row, selectable before
the scan finishes. Selecting a discovered row saves it directly (no pairing here).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, LoadingIndicator, OptionList, Static
from textual.widgets.option_list import Option

from ..devices.models import Device
from ..discovery import DiscoveredDevice, discover_one, exclude_saved, merge
from .device_option_list import DeviceOptionList
from .devices_screen import AdbTextHintScreen, AddDeviceScreen

ADD_MANUAL_ID = "__add_manual__"

TITLE_ART = r""" ____  _
|  _ \(_)___  ___ _____   _____ _ __
| | | | / __|/ __/ _ \ \ / / _ \ '__|
| |_| | \__ \ (_| (_) \ V /  __/ |
|____/|_|___/\___\___/ \_/ \___|_|"""


class DiscoverScreen(Screen[None]):
    """Lists devices found on the LAN; select one to add it, or add manually."""

    BINDINGS = [("escape", "back", "Back")]

    SCAN_TIMEOUT = 5.0  # seconds each adapter's scan runs before it is abandoned

    def __init__(self) -> None:
        super().__init__()
        self._saved_ips: list[str] = []
        self._found: list[DiscoveredDevice] = []
        # ip -> device, so a selected row resolves back to what to save.
        self._by_ip: dict[str, DiscoveredDevice] = {}
        self._pending = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="discover"):
            yield Static(TITLE_ART, id="discover-title")
            yield DeviceOptionList(id="discover-list")
            with Horizontal(id="discover-status"):
                yield LoadingIndicator()
                yield Label("Searching for devices…", id="discover-status-text")
        yield Footer()

    def on_mount(self) -> None:
        self._saved_ips = [device.ip for device in self.app.store.list()]
        self._reload()  # the manual row is present immediately
        adapters = [a for a in self.app.registry.adapters() if hasattr(a, "discover")]
        self._pending = len(adapters)
        if not adapters:
            self._finish_scan()
        for adapter in adapters:
            self.run_worker(self._scan(adapter))

    async def _scan(self, adapter) -> None:
        # Best-effort per adapter (bounded + isolated by discover_one): a failure or
        # timeout contributes nothing and never aborts the others.
        devices = await discover_one(adapter, self.SCAN_TIMEOUT)
        self._found.extend(devices)
        self._reload()
        self._pending -= 1
        if self._pending == 0:
            self._finish_scan()

    def _finish_scan(self) -> None:
        self.query_one("#discover-status").display = False

    def _reload(self) -> None:
        picker = self.query_one("#discover-list", DeviceOptionList)
        previous = picker.highlighted
        picker.clear_options()
        devices = exclude_saved(merge(self._found), self._saved_ips)
        self._by_ip = {device.ip: device for device in devices}
        for index, device in enumerate(devices):
            picker.add_option(Option(self._row_prompt(index, device), id=device.ip))
        picker.device_count = len(devices)
        if devices:  # a divider separates discovered rows from the manual fallback
            picker.add_option(None)
        picker.add_option(Option("+ Add manually", id=ADD_MANUAL_ID))
        picker.highlighted = (
            0 if previous is None else min(previous, picker.option_count - 1)
        )

    def _row_prompt(self, index: int, device: DiscoveredDevice) -> str:
        display = self.app.registry.resolve(device.platform).display_name
        return f"{index + 1}. {device.name} — {display} ({device.ip})"

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == ADD_MANUAL_ID:
            self.app.push_screen(AddDeviceScreen())
            return
        device = self._by_ip.get(event.option.id)
        if device is not None:
            self._add(device)

    def _add(self, device: DiscoveredDevice) -> None:
        # Saved IPs are already excluded, so only a name clash with a distinct
        # device can conflict; report it and skip rather than duplicate the name.
        conflict = self.app.store.find_conflict(device.name, device.ip)
        if conflict is not None:
            self.app.notify(conflict, severity="warning")
            return
        self.app.store.add(
            Device(
                name=device.name,
                platform=device.platform,
                ip=device.ip,
                identifier=device.identifier,
            )
        )
        self.app.pop_screen()
        # Android TV text can be swallowed by the IME overlay; hint at the ADB remedy
        # (a dismissible modal) instead of the plain toast for those devices.
        adapter = self.app.registry.resolve(device.platform)
        if getattr(adapter, "supports_adb_text", False):
            self.app.push_screen(AdbTextHintScreen(device.name))
        else:
            self.app.notify(f'Added "{device.name}".')

    def action_back(self) -> None:
        self.app.pop_screen()
