"""The on-screen remote surface: clickable buttons plus keyboard control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label

from ..errors import TextUnsupportedError, UnsupportedKeyError
from ..keys import Key

if TYPE_CHECKING:
    from ..capabilities import Capabilities
    from ..devices.models import Device
    from ..session import Session


class TextField(Input):
    """A text input whose Escape exits the field (rather than firing the Back key)."""

    BINDINGS = [Binding("escape", "exit_field", "Exit field")]

    class ExitRequested(Message):
        """Posted when the user presses Escape to leave the field."""

    def action_exit_field(self) -> None:
        self.post_message(self.ExitRequested())


class RemoteScreen(Screen[None]):
    """A physical-remote-like surface driven by clicks and by the keyboard."""

    BINDINGS = [
        Binding("up", "send('UP')", "Up"),
        Binding("down", "send('DOWN')", "Down"),
        Binding("left", "send('LEFT')", "Left"),
        Binding("right", "send('RIGHT')", "Right"),
        Binding("enter", "send('OK')", "OK"),
        Binding("escape", "send('BACK')", "Back"),
        Binding("h", "send('HOME')", "Home"),
        Binding("t", "text_mode", "Text"),
        Binding("q", "exit_remote", "Exit"),
    ]

    def __init__(
        self,
        session: "Session",
        capabilities: "Capabilities",
        device: "Device",
    ) -> None:
        super().__init__()
        self._session = session
        self._capabilities = capabilities
        self._device = device

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Remote — {self._device.name}", id="remote-title")
        with Container(id="remote"):
            with Horizontal(id="row-top"):
                yield self._key_button(Key.HOME, "⌂ Home")
                yield self._key_button(Key.BACK, "↩ Back")
            with Vertical(id="dpad"):
                yield self._key_button(Key.UP, "▲")
                with Horizontal():
                    yield self._key_button(Key.LEFT, "◀")
                    yield self._key_button(Key.OK, "OK")
                    yield self._key_button(Key.RIGHT, "▶")
                yield self._key_button(Key.DOWN, "▼")
            with Horizontal(id="row-vol"):
                yield self._key_button(Key.VOL_UP, "Vol +")
                yield self._key_button(Key.VOL_DOWN, "Vol −")
                yield self._key_button(Key.MUTE, "Mute")
            yield TextField(placeholder="Press 't' to type…", id="text", disabled=True)
            yield Label("", id="text-status")
        yield Footer()

    def on_mount(self) -> None:
        for key in Key:
            if not self._capabilities.supports(key):
                self.query_one(f"#key-{key.name.lower()}", Button).disabled = True
        if not self._capabilities.text:
            self.query_one("#text-status", Label).update(
                "Text entry is not supported on this device"
            )

    def _key_button(self, key: Key, label: str) -> Button:
        button = Button(label, id=f"key-{key.name.lower()}")
        button.can_focus = False  # keyboard drives bindings; mouse drives clicks
        return button

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("key-"):
            await self._send(Key[button_id.removeprefix("key-").upper()])

    async def action_send(self, key_name: str) -> None:
        await self._send(Key[key_name])

    async def _send(self, key: Key) -> None:
        try:
            await self._session.send_key(key)
        except UnsupportedKeyError:
            self.query_one("#text-status", Label).update(
                f"{key.name} is not supported on this device"
            )

    def action_text_mode(self) -> None:
        if not self._capabilities.text:
            return
        field = self.query_one("#text", TextField)
        field.disabled = False
        field.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        if text:
            try:
                await self._session.send_text(text)
            except TextUnsupportedError:
                self.query_one("#text-status", Label).update(
                    "Text entry is not supported on this device"
                )
        self._exit_text_mode()

    def on_text_field_exit_requested(self, event: TextField.ExitRequested) -> None:
        self._exit_text_mode()

    def _exit_text_mode(self) -> None:
        field = self.query_one("#text", TextField)
        field.value = ""
        field.disabled = True
        self.set_focus(None)

    async def action_exit_remote(self) -> None:
        await self._session.close()
        self.app.pop_screen()
