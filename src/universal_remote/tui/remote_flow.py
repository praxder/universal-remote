"""Use Remote flow: pick a device, pair if needed (cancellable), then connect."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, OptionList
from textual.widgets.option_list import Option

from ..devices.models import Device
from ..errors import PairingCancelledError
from .remote_screen import RemoteScreen


class UseRemoteScreen(Screen[None]):
    """Choose a device; connect directly if credentialed, else run pairing first."""

    BINDINGS = [("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="use-remote"):
            yield Label("Use Remote", id="use-remote-title")
            yield OptionList(id="device-picker")
            yield Label("", id="no-devices")
        yield Footer()

    def on_mount(self) -> None:
        devices = self.app.store.list()
        picker = self.query_one("#device-picker", OptionList)
        if not devices:
            picker.display = False
            self.query_one("#no-devices", Label).update(
                "No devices saved — add one in Manage Devices first."
            )
            return
        for device in devices:
            picker.add_option(Option(device.name, id=device.id))
        picker.highlighted = 0
        picker.focus()

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        device = next(
            (d for d in self.app.store.list() if d.id == event.option.id), None
        )
        if device is None:
            return
        if device.credential is None:
            self.app.push_screen(PairingScreen(device))
        else:
            await self._open_remote(device)

    async def _open_remote(self, device: Device) -> None:
        adapter = self.app.registry.resolve(device.platform)
        session = await adapter.connect(device)
        self.app.push_screen(
            RemoteScreen(
                session=session, capabilities=adapter.capabilities(), device=device
            )
        )

    def action_back(self) -> None:
        self.app.pop_screen()


class PairingScreen(Screen[None]):
    """Runs pairing in a worker with on-screen guidance; cancellable via Esc/button."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, device: Device) -> None:
        super().__init__()
        self._device = device
        self._worker = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="pairing"):
            yield Label("Pairing…", id="pairing-title")
            yield Label(
                "Accept the authorization popup on your TV.",
                id="pairing-guidance",
            )
            yield Button("Cancel", id="cancel")
        yield Footer()

    def on_mount(self) -> None:
        self._worker = self.run_worker(self._pair_and_connect(), exclusive=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.app.pop_screen()

    async def _pair_and_connect(self) -> None:
        adapter = self.app.registry.resolve(self._device.platform)
        try:
            token = await adapter.pair(self._device)
        except PairingCancelledError:
            self.app.pop_screen()
            return
        self._device.credential = token
        self.app.store.update(self._device)
        session = await adapter.connect(self._device)
        self.app.switch_screen(
            RemoteScreen(
                session=session,
                capabilities=adapter.capabilities(),
                device=self._device,
            )
        )
