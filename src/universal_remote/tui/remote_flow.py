"""Use Remote flow: pick a device, pair if needed (cancellable), then connect."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    OptionList,
    Static,
)
from textual.widgets.option_list import Option

from ..devices.models import Device
from ..errors import ConnectionFailedError, PairingCancelledError
from ..reachability import Reachability, probe
from ..session import Session
from .device_option_list import DeviceOptionList
from .remote_screen import RemoteScreen

# Reachability state -> Rich-markup bubble colour.
_BUBBLE_COLORS = {
    Reachability.REACHABLE: "green",
    Reachability.UNREACHABLE: "red",
    Reachability.UNKNOWN: "yellow",
}

TITLE_ART = r""" ____       _           _     ____             _
/ ___|  ___| | ___  ___| |_  |  _ \  _____   _(_) ___ ___
\___ \ / _ \ |/ _ \/ __| __| | | | |/ _ \ \ / / |/ __/ _ \
 ___) |  __/ |  __/ (__| |_  | |_| |  __/\ V /| | (_|  __/
|____/ \___|_|\___|\___|\__| |____/ \___| \_/ |_|\___\___|"""


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
                with Center(id="cancel-row"):
                    yield Button("Cancel", id="cancel")
            with Vertical(id="connecting-error"):
                yield Label("", id="connect-error")
                with Center(id="error-buttons"):
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
    """Choose a device; connect directly if credentialed, else run pairing first.

    Each row carries a reachability bubble that starts yellow (unknown) and is
    refreshed on an interval by a non-invasive TCP probe of the device's adapter
    port; the bubble is advisory and never blocks selection.
    """

    BINDINGS = [("escape", "back", "Back")]

    POLL_INTERVAL = 5.0  # seconds between reachability refreshes while open
    PROBE_TIMEOUT = 2.0  # seconds to reach a device (strictly below the interval)

    def __init__(self) -> None:
        super().__init__()
        self._devices: list[Device] = []
        # Device ids with a probe in flight, so a slow probe does not stack.
        self._inflight: set[str] = set()
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="use-remote"):
            yield Static(TITLE_ART, id="use-remote-title")
            yield DeviceOptionList(id="device-picker")
            yield Label("", id="no-devices")
        yield Footer()

    def on_mount(self) -> None:
        devices = self.app.store.list()
        picker = self.query_one("#device-picker", DeviceOptionList)
        if not devices:
            picker.display = False
            self.query_one("#no-devices", Label).update(
                "No devices saved — add one in Manage Devices first."
            )
            return
        self._devices = devices
        for i, device in enumerate(devices):
            prompt = self._row_prompt(Reachability.UNKNOWN, i, device.name)
            picker.add_option(Option(prompt, id=device.id))
        picker.device_count = len(devices)
        picker.highlighted = 0
        picker.focus()
        self._probe_cycle()  # resolve reachability right away, then on the interval
        self._timer = self.set_interval(self.POLL_INTERVAL, self._probe_cycle)

    def on_unmount(self) -> None:
        # Leaving the screen stops probing; workers are cancelled by Textual.
        if self._timer is not None:
            self._timer.stop()

    def _row_prompt(self, status: Reachability, index: int, name: str) -> str:
        color = _BUBBLE_COLORS[status]
        return f"[{color}]●[/] {index + 1}. {name}"

    def _probe_cycle(self) -> None:
        for index, device in enumerate(self._devices):
            if device.id in self._inflight:
                continue
            adapter = self.app.registry.resolve(device.platform)
            port = getattr(adapter, "reachability_port", None)
            if port is None:
                continue  # no port declared: the row stays yellow (unknown)
            self._inflight.add(device.id)
            self.run_worker(self._probe_device(index, device, port))

    async def _probe_device(self, index: int, device: Device, port: int) -> None:
        try:
            status = await probe(device.ip, port, self.PROBE_TIMEOUT)
        finally:
            self._inflight.discard(device.id)
        picker = self.query_one("#device-picker", DeviceOptionList)
        picker.replace_option_prompt_at_index(
            index, self._row_prompt(status, index, device.name)
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        device = next(
            (d for d in self.app.store.list() if d.id == event.option.id), None
        )
        if device is None:
            return
        # An adapter may declare it needs no pairing (e.g. Roku's unauthenticated
        # ECP); such a device connects directly even without a stored credential.
        adapter = self.app.registry.resolve(device.platform)
        if device.credential is None and getattr(adapter, "requires_pairing", True):
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


class PairingScreen(ModalScreen[Device | None]):
    """Pairs in a worker with on-screen guidance; cancellable via Esc/button.

    Pairs and stores the credential only, then dismisses with the device on
    success or `None` on cancel; connecting is left to the caller.
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, device: Device) -> None:
        super().__init__()
        self._device = device
        self._worker = None
        # Bridges the pairing worker and the UI: set by the submit handler when
        # an adapter (e.g. Apple TV) asks for a PIN. None until the adapter asks.
        self._pin_future: asyncio.Future[str] | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="pairing"):
            yield Label("Pairing…", id="pairing-title")
            yield Label(
                "Accept the authorization popup on your TV.",
                id="pairing-guidance",
            )
            with Vertical(id="pin-entry"):
                yield Input(id="pin-input")
                yield Button("Submit", id="submit")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self._worker = self.run_worker(self._pair(), exclusive=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self._submit_pin()
        elif event.button.id == "cancel":
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit_pin()

    def action_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.dismiss(None)

    async def _prompt(self, message: str) -> str:
        """Show a PIN-entry state and await the value the user submits."""
        self.query_one("#pairing-guidance", Label).update(message)
        self.query_one("#pin-entry").display = True
        pin_input = self.query_one("#pin-input", Input)
        pin_input.value = ""
        pin_input.focus()
        self._pin_future = asyncio.get_running_loop().create_future()
        return await self._pin_future

    def _submit_pin(self) -> None:
        if self._pin_future is not None and not self._pin_future.done():
            self._pin_future.set_result(self.query_one("#pin-input", Input).value)

    async def _pair(self) -> None:
        adapter = self.app.registry.resolve(self._device.platform)
        try:
            token = await adapter.pair(self._device, prompt=self._prompt)
        except PairingCancelledError:
            self.dismiss(None)
            return
        self._device.credential = token
        self.app.store.update(self._device)
        self.dismiss(self._device)
