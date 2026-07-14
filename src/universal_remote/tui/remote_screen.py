"""The on-screen remote surface: clickable buttons plus keyboard control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical
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

    # Compact one-row buttons so the fuller button set fits an 80×24 terminal
    # without scrolling. The `#remote` id scope is deliberate: Textual sets
    # Button borders per-variant (e.g. `Button.-default`), whose class specificity
    # beats a plain `RemoteScreen Button` — so `border: none` only wins from an
    # id-scoped selector. Without the border removed, box-sizing eats the single
    # row and the label renders on zero rows (blank buttons).
    # Borderless removes Textual's default disabled cue, so a dimmed disabled look
    # is set explicitly (Apple TV shows many disabled keys); `!important` beats
    # Textual's built-in disabled text-opacity (0.6), and the panel background is
    # a second, border-independent cue.
    DEFAULT_CSS = """
    #remote Button { height: 1; border: none; min-width: 0; }
    #remote Button:disabled { text-opacity: 40% !important; background: $panel; }
    /* Auto heights so the button set sizes to its content: if it ever exceeds the
       terminal the screen scrolls (a visible, testable signal) rather than the
       rows silently compressing into an unreadable smear. The row containers
       default to 1fr and would otherwise stretch to fill. */
    #remote, RemoteScreen Horizontal, RemoteScreen Vertical { height: auto; }
    #numpad { grid-size: 3; grid-rows: 1; grid-columns: 5; width: auto; height: auto; }
    """

    BINDINGS = [
        Binding("up", "send('UP')", "Up"),
        Binding("down", "send('DOWN')", "Down"),
        Binding("left", "send('LEFT')", "Left"),
        Binding("right", "send('RIGHT')", "Right"),
        Binding("k", "send('UP')", "Up", show=False),
        Binding("j", "send('DOWN')", "Down", show=False),
        Binding("h", "send('LEFT')", "Left", show=False),
        Binding("l", "send('RIGHT')", "Right", show=False),
        Binding("enter", "send('OK')", "OK"),
        Binding("escape", "send('BACK')", "Back"),
        Binding("space", "send('HOME')", "Home"),
        # Digit keys drive the number pad; hidden from the footer to avoid clutter.
        *(
            Binding(str(digit), f"send('NUM_{digit}')", show=False)
            for digit in range(10)
        ),
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
                yield self._key_button(Key.MENU, "☰ Menu")
                yield self._key_button(Key.HOME, "⌂ Home")
                yield self._key_button(Key.BACK, "↩ Back")
            with Vertical(id="dpad"):
                yield self._key_button(Key.UP, "▲")
                with Horizontal():
                    yield self._key_button(Key.LEFT, "◀")
                    yield self._key_button(Key.OK, "OK")
                    yield self._key_button(Key.RIGHT, "▶")
                yield self._key_button(Key.DOWN, "▼")
            with Horizontal(id="row-chan-vol"):
                yield self._key_button(Key.CH_UP, "Ch +")
                yield self._key_button(Key.CH_DOWN, "Ch −")
                yield self._key_button(Key.VOL_UP, "Vol +")
                yield self._key_button(Key.VOL_DOWN, "Vol −")
                yield self._key_button(Key.MUTE, "Mute")
            with Horizontal(id="row-media"):
                yield self._key_button(Key.REWIND, "◀◀")
                yield self._key_button(Key.PLAY, "▶")
                yield self._key_button(Key.PAUSE, "❚❚")
                yield self._key_button(Key.PLAY_PAUSE, "▶❚❚")
                yield self._key_button(Key.STOP, "■")
                yield self._key_button(Key.FAST_FORWARD, "▶▶")
            with Grid(id="numpad"):
                for digit in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0):
                    yield self._key_button(Key[f"NUM_{digit}"], str(digit))
            yield TextField(placeholder="Press 't' to type…", id="text", disabled=True)
            yield Label("", id="text-status")
        yield Footer()

    def on_mount(self) -> None:
        for key in Key:
            if not self._capabilities.supports(key):
                self.query_one(f"#key-{key.name.lower()}", Button).disabled = True
        if not self._capabilities.text:
            self._status("Text entry is not supported on this device")

    def _status(self, message: str) -> None:
        self.query_one("#text-status", Label).update(message)

    def _key_button(self, key: Key, label: str) -> Button:
        button = Button(label, id=f"key-{key.name.lower()}")
        button.can_focus = False  # keyboard drives bindings; mouse drives clicks
        return button

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("key-"):
            await self._send(Key[button_id.removeprefix("key-").upper()])

    async def action_send(self, key_name: str) -> None:
        key = Key[key_name]
        # A bound hotkey for an unsupported key (e.g. a digit on Apple TV) behaves
        # like its disabled button: nothing sent, no message. The click path never
        # reaches here — disabled buttons do not fire.
        if not self._capabilities.supports(key):
            return
        await self._send(key)

    async def _send(self, key: Key) -> None:
        try:
            await self._session.send_key(key)
        except UnsupportedKeyError:
            self._status(f"{key.name} is not supported on this device")
        except Exception:
            # A single failed key press (device timeout, dropped connection) must
            # not take down the remote — report it and stay on-screen.
            self._status(f"{key.name} failed — the device may be unreachable")

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
                self._status("Text entry is not supported on this device")
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
