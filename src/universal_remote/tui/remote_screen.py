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
from .shortcuts import Scope, rebuild_shortcuts

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

    # Bordered buttons (three rows tall, padded) so the remote reads at a
    # comfortable size rather than a cramped one-row list. The `#remote` id scope
    # is deliberate: Textual sets Button borders per-variant (e.g.
    # `Button.-default`), whose class specificity beats a plain `RemoteScreen
    # Button` — so the `round` border only wins from an id-scoped selector.
    # A dimmed disabled look is set explicitly (Apple TV shows many disabled keys);
    # `!important` beats Textual's built-in disabled text-opacity (0.6).
    # The fill is transparent, not Textual's default `$surface`: a solid fill
    # paints the border cells too, so the thin `round` glyph sits in a filled cell
    # and the fill shows on the outer half of every border cell — a halo bleeding
    # past the outline. Transparent leaves the border alone to bound each button.
    # Disabled keys inherit that transparent fill (a dimmed label is their cue).
    # The fuller, bigger button set no longer fits a minimal 80×24 terminal — the
    # remote sizes to its content and the screen scrolls on very short terminals,
    # while filling a normal one. `test_..._does_not_scroll` pins the supported
    # baseline size.
    DEFAULT_CSS = """
    #remote Button {
        height: 3; border: round $primary; background: transparent;
        min-width: 0; padding: 0 1; margin: 0 1;
    }
    #remote Button:disabled { text-opacity: 40% !important; }
    /* Auto heights so the button set sizes to its content: if it exceeds the
       terminal the screen scrolls (a visible, testable signal) rather than the
       rows silently compressing. The row containers default to 1fr and would
       otherwise stretch to fill. Center the stack so it reads like a physical
       remote instead of a left-packed list. */
    #remote, RemoteScreen Horizontal, RemoteScreen Vertical { height: auto; }
    /* Every group is a full-width row whose content is centered, so narrow groups
       (D-pad, number pad) sit centered rather than packed to the left edge. */
    #row-top, #row-chan-vol, #row-media, #numpad-row, #dpad {
        align-horizontal: center; margin-bottom: 1;
    }
    /* Channel/volume and media transport sit flush as one cluster, so the
       channel/volume row drops the gap the shared rule adds below it. */
    #row-chan-vol { margin-bottom: 0; }
    /* D-pad forms a centered cross: each of the three rows centers its own
       content, so ▲/▼ line up over OK. (align-horizontal on the vertical #dpad
       would center the block but left-pack the narrow ▲/▼.) A uniform button
       width makes ▲/▼/OK center identically — a 1-char arrow and 2-char OK would
       otherwise round to slightly different centers. */
    #dpad-up, #dpad-mid, #dpad-down { align-horizontal: center; }
    #dpad Button { width: 7; }
    #numpad { grid-size: 3; grid-rows: 3; grid-columns: 7; grid-gutter: 0 1; width: auto; height: auto; }
    /* Fill the grid cell (no side margin) so the digit is not clipped: a grid
       cell minus the button's own margin left zero content width. */
    #numpad Button { margin: 0; width: 100%; }
    """

    # Every remote hotkey is a catalogued action, built from the override map on
    # mount. The D-pad directions (arrows + `hjkl`) are reserved and always bind;
    # OK/Back/Home/digits/text and the twelve formerly click-only keys are
    # rebindable. Go Back (the Global action, default Escape) is bound but kept out
    # of the footer — a ninth hint does not fit the supported 80-column width, and
    # Escape as go-back matches the rest of the app so it needs no prompt. While the
    # text field is focused the Input consumes Backspace and the letters/digits, so
    # they never reach these bindings.
    SHORTCUT_SCOPES = frozenset({Scope.REMOTE, Scope.GLOBAL})
    SHORTCUT_HIDE = frozenset({"global.go_back"})

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
        # The device name lives in the header (see on_mount), not a separate row,
        # so the button set gets that row back.
        yield Header()
        with Container(id="remote"):
            with Horizontal(id="row-top"):
                yield self._key_button(Key.MENU, "☰ Menu")
                yield self._key_button(Key.HOME, "⌂ Home")
                yield self._key_button(Key.BACK, "↩ Back")
            with Vertical(id="dpad"):
                with Horizontal(id="dpad-up"):
                    yield self._key_button(Key.UP, "▲")
                with Horizontal(id="dpad-mid"):
                    yield self._key_button(Key.LEFT, "◀")
                    yield self._key_button(Key.OK, "⏎")
                    yield self._key_button(Key.RIGHT, "▶")
                with Horizontal(id="dpad-down"):
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
            with Horizontal(id="numpad-row"):
                with Grid(id="numpad"):
                    for digit in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                        yield self._key_button(Key[f"NUM_{digit}"], str(digit))
                    # Empty first cell of the last row so 0 sits centered under 8.
                    yield Label("", id="numpad-spacer")
                    yield self._key_button(Key.NUM_0, "0")
            yield TextField(placeholder="Press 't' to type…", id="text", disabled=True)
            yield Label("", id="text-status")
        yield Footer()

    def on_mount(self) -> None:
        rebuild_shortcuts(
            self,
            self.app.shortcut_overrides,
            self.SHORTCUT_SCOPES,
            hide=self.SHORTCUT_HIDE,
        )
        # Show the device in the header instead of a dedicated title row; restore
        # the app title when the remote closes so other screens are unaffected.
        self._previous_title = self.app.title
        display_type = self.app.registry.resolve(self._device.platform).display_name
        self.app.title = (
            f"Name: {self._device.name} • Type: {display_type} • IP: {self._device.ip}"
        )
        for key in Key:
            if not self._capabilities.supports(key):
                self.query_one(f"#key-{key.name.lower()}", Button).disabled = True
        if not self._capabilities.text:
            self._status("Text entry is not supported on this device")

    def on_unmount(self) -> None:
        self.app.title = self._previous_title

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
            except Exception:
                # A failed text send (device timeout, dropped connection) must not
                # take down the remote — report it and stay, like the key-send path.
                self._status("Text entry failed — the device may be unreachable")
            else:
                # An opted-in ADB send that fell back to Remote v2 flags itself; say
                # so rather than leaving the user wondering why setup made no change.
                if getattr(self._session, "adb_text_unavailable", False):
                    self._status("ADB text unavailable — sent over the standard path")
        self._exit_text_mode()

    def on_text_field_exit_requested(self, event: TextField.ExitRequested) -> None:
        self._exit_text_mode()

    def _exit_text_mode(self) -> None:
        field = self.query_one("#text", TextField)
        field.value = ""
        field.disabled = True
        self.set_focus(None)

    async def action_go_back(self) -> None:
        # The remote's Go Back closes the live session before popping the screen;
        # every other screen's Go Back just pops.
        await self._session.close()
        self.app.pop_screen()
