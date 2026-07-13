"""Use Remote flow: pick a device, pair if needed (cancellable), then connect."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, OptionList
from textual.widgets.option_list import Option

from ..devices.models import Device
from ..errors import ConnectionFailedError, PairingCancelledError
from ..session import Session
from .remote_screen import RemoteScreen


class ConnectingModal(ModalScreen[Session | None]):
    """Connects to a device in a cancellable worker, overlaid on device selection.

    Renders a loading spinner while connecting and, on failure, an in-place error
    state offering Retry and Back. Dismisses with the session on success, or with
    `None` on cancel/give-up; forward navigation is left to the caller.
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, device: Device) -> None:
        super().__init__()
        self._device = device
        self._worker = None

    def compose(self) -> ComposeResult:
        with Vertical(id="connecting"):
            with Vertical(id="connecting-loading"):
                yield LoadingIndicator()
                yield Label(f"Connecting to {self._device.name}…")
                yield Button("Cancel", id="cancel")
            with Vertical(id="connecting-error"):
                yield Label("", id="connect-error")
                yield Button("Retry", id="retry")
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        self._start()

    def _start(self) -> None:
        self.query_one("#connecting-error").display = False
        self.query_one("#connecting-loading").display = True
        self._worker = self.run_worker(self._connect(), exclusive=True)

    async def _connect(self) -> None:
        adapter = self.app.registry.resolve(self._device.platform)
        try:
            session = await adapter.connect(self._device)
        except ConnectionFailedError:
            self._show_error()
            return
        self.dismiss(session)

    def _show_error(self) -> None:
        self.query_one("#connecting-loading").display = False
        self.query_one("#connect-error", Label).update(
            f"Couldn't connect to {self._device.name}."
        )
        self.query_one("#connecting-error").display = True
        self.query_one("#retry", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "retry":
            self._start()
        else:  # cancel or back
            self.action_cancel()

    def action_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.dismiss(None)


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

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        device = next(
            (d for d in self.app.store.list() if d.id == event.option.id), None
        )
        if device is None:
            return
        if device.credential is None:
            self.app.push_screen(PairingScreen(device), self._after_pairing)
        else:
            self._connect(device)

    def _after_pairing(self, device: Device | None) -> None:
        if device is not None:
            self._connect(device)

    def _connect(self, device: Device) -> None:
        adapter = self.app.registry.resolve(device.platform)

        def _on_connected(session: Session | None) -> None:
            if session is not None:
                self.app.push_screen(
                    RemoteScreen(
                        session=session,
                        capabilities=adapter.capabilities(),
                        device=device,
                    )
                )

        self.app.push_screen(ConnectingModal(device), _on_connected)

    def action_back(self) -> None:
        self.app.pop_screen()


class PairingScreen(Screen[Device | None]):
    """Pairs in a worker with on-screen guidance; cancellable via Esc/button.

    Pairs and stores the credential only, then dismisses with the device on
    success or `None` on cancel; connecting is left to the caller.
    """

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
        self._worker = self.run_worker(self._pair(), exclusive=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.dismiss(None)

    async def _pair(self) -> None:
        adapter = self.app.registry.resolve(self._device.platform)
        try:
            token = await adapter.pair(self._device)
        except PairingCancelledError:
            self.dismiss(None)
            return
        self._device.credential = token
        self.app.store.update(self._device)
        self.dismiss(self._device)
