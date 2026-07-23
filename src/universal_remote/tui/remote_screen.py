"""The on-screen remote surface: clickable buttons plus keyboard control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
)

from ..errors import TextUnsupportedError, UnsupportedKeyError
from ..keys import Key
from .actions import (
    ActionTypeListModal,
    action_type,
    present_result,
    run_action,
)
from .custom_buttons import (
    ButtonScope,
    default_title,
    resolve_action,
    resolve_scope,
    resolve_title,
    set_action,
    set_title,
)
from .shortcuts import Scope, rebuild_shortcuts

if TYPE_CHECKING:
    from ..capabilities import Capabilities
    from ..devices.models import Device
    from ..session import Session


class TextEntryModal(ModalScreen[None]):
    """On-demand text entry: type then Enter sends once and dismisses; Escape cancels.

    Owns the send path so the remote surface no longer reserves a docked field.
    Escape is bound here so it dismisses the modal rather than reaching the remote's
    Go Back (which would close the session). Transient outcomes — a failed send, or
    an ADB path that fell back — surface as app-level toasts that outlive the modal.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    TextEntryModal { align: center middle; background: $background 60%; }
    #text-entry {
        width: 60%; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #text-entry-title { width: 100%; text-align: center; margin-bottom: 1; }
    #text-entry-input { width: 100%; }
    """

    def __init__(self, session: "Session") -> None:
        super().__init__()
        self._session = session

    def compose(self) -> ComposeResult:
        with Vertical(id="text-entry"):
            yield Label("Enter text to send", id="text-entry-title")
            yield Input(
                placeholder="Type text, then Enter to send…", id="text-entry-input"
            )

    def on_mount(self) -> None:
        self.query_one("#text-entry-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value:
            await self._send(event.value)
        self.dismiss()

    async def _send(self, text: str) -> None:
        try:
            await self._session.send_text(text)
        except TextUnsupportedError:
            self.app.notify(
                "Text entry is not supported on this device", severity="warning"
            )
        except Exception:
            # A failed text send (device timeout, dropped connection) must not take
            # down the remote — report it and return, like the key-send path.
            self.app.notify(
                "Text entry failed — the device may be unreachable", severity="warning"
            )
        else:
            # An opted-in ADB send that fell back to Remote v2 flags itself; say so
            # rather than leaving the user wondering why setup made no change.
            if getattr(self._session, "adb_text_unavailable", False):
                self.app.notify("ADB text unavailable — sent over the standard path")

    def action_cancel(self) -> None:
        self.dismiss()


class ButtonConfigModal(ModalScreen[bool]):
    """Names, scopes, and assigns an action to a custom button; OK saves both.

    Dismisses with True when the button was saved (so the remote re-resolves that
    button's label) or False on Cancel/Escape. The Action Type control opens the
    action catalog; the entered title and any assigned action are saved together at
    the selected scope, so the whole button lives in one place.
    """

    # Scope options in display order; the radio's pressed index maps into this tuple.
    _SCOPES = (ButtonScope.DEVICE, ButtonScope.TYPE, ButtonScope.GLOBAL)

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    ButtonConfigModal { align: center middle; background: $background 60%; }
    #button-config {
        width: 60%; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #button-config-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #button-config-title-input { width: 100%; margin-bottom: 1; }
    #button-config-scope-label { width: 100%; }
    #button-config-scope { width: 100%; margin-bottom: 1; }
    #button-config-action-type { width: 100%; margin-bottom: 1; }
    #button-config-buttons { width: 100%; height: auto; align-horizontal: center; }
    #button-config-buttons Button { width: 16; margin: 0 1; }
    """

    def __init__(self, index: int, device: "Device") -> None:
        super().__init__()
        self._index = index
        self._device = device
        # The action assigned to the button, carried so OK writes it alongside the
        # title at the chosen scope even when the user only edits the title. Set from
        # the button's current action in compose (when the app is reachable) and
        # replaced when the user configures a new one.
        self._action: dict | None = None

    def compose(self) -> ComposeResult:
        self._action = self._current_action()
        selected = self._selected_scope_index()
        with Vertical(id="button-config"):
            yield Label("Configure Custom Button", id="button-config-title")
            yield Input(
                value=self._current_title(),
                placeholder="Button title",
                id="button-config-title-input",
            )
            yield Label("Scope", id="button-config-scope-label")
            with RadioSet(id="button-config-scope"):
                yield RadioButton("This Device", value=selected == 0, id="scope-device")
                yield RadioButton("Device Type", value=selected == 1, id="scope-type")
                yield RadioButton("Global", value=selected == 2, id="scope-global")
            yield Button(self._action_type_label(), id="button-config-action-type")
            with Horizontal(id="button-config-buttons"):
                yield Button("OK", id="button-config-ok", variant="primary")
                yield Button("Cancel", id="button-config-cancel")

    def _current_action(self) -> dict | None:
        """The button's currently assigned action, resolved for the active device."""
        return resolve_action(
            self.app.custom_buttons,
            self._index,
            device_id=self._device.id,
            platform=self._device.platform,
        )

    def _action_type_label(self) -> str:
        """The Action Type control's label, naming the assigned action or none."""
        entry = action_type(self._action.get("type")) if self._action else None
        return f"Action Type: {entry.label}" if entry else "Action Type: (none)"

    def _current_title(self) -> str:
        """The button's current resolved title, prefilled so it can be edited."""
        return resolve_title(
            self.app.custom_buttons,
            self._index,
            device_id=self._device.id,
            platform=self._device.platform,
        )

    def _selected_scope_index(self) -> int:
        """The radio index to preselect: the scope the shown title resolves from.

        Reopening the modal reflects where the title is actually stored; with no
        title configured at any scope it falls back to This Device (index 0).
        """
        scope = resolve_scope(
            self.app.custom_buttons,
            self._index,
            device_id=self._device.id,
            platform=self._device.platform,
        )
        return self._SCOPES.index(scope) if scope is not None else 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "button-config-ok":
            self._save()
        elif event.button.id == "button-config-cancel":
            self.dismiss(False)
        elif event.button.id == "button-config-action-type":
            self.app.push_screen(ActionTypeListModal(), self._action_chosen)

    def _action_chosen(self, action: dict | None) -> None:
        """Assign the action the catalog flow returned; None means the user cancelled."""
        if action is not None:
            self._action = action
            self.query_one(
                "#button-config-action-type", Button
            ).label = self._action_type_label()

    def _save(self) -> None:
        title = self.query_one("#button-config-title-input", Input).value
        scope = self._selected_scope()
        set_title(
            self.app.custom_buttons,
            self._index,
            title,
            scope,
            device_id=self._device.id,
            platform=self._device.platform,
        )
        set_action(
            self.app.custom_buttons,
            self._index,
            self._action,
            scope,
            device_id=self._device.id,
            platform=self._device.platform,
        )
        self.app.persist_preferences()
        self.dismiss(True)

    def _selected_scope(self) -> ButtonScope:
        return self._SCOPES[
            self.query_one("#button-config-scope", RadioSet).pressed_index
        ]

    def action_cancel(self) -> None:
        self.dismiss(False)


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
    #row-top, #row-chan-vol, #row-media, #numpad-row, #dpad, #custom-row {
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
        # When armed by the edit-mode key, the next custom-button activation opens its
        # config instead of running its action, then clears. See `action_edit_mode`.
        self._edit_mode = False

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
            with Horizontal(id="custom-row"):
                for index in range(1, 6):
                    yield self._custom_button(index)
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
        for index in range(1, 6):
            self._label_custom(index)

    def on_unmount(self) -> None:
        self.app.title = self._previous_title

    def _key_button(self, key: Key, label: str) -> Button:
        button = Button(label, id=f"key-{key.name.lower()}")
        button.can_focus = False  # keyboard drives bindings; mouse drives clicks
        return button

    def _custom_button(self, index: int) -> Button:
        # Mouse-click only in Phase 1: no hotkey binds them, and leaving them
        # unfocusable keeps Enter mapped to OK rather than pressing a focused button.
        button = Button(default_title(index), id=f"custom-{index}")
        button.can_focus = False
        return button

    def _label_custom(self, index: int) -> None:
        """Set button `index`'s label to its title resolved for the active device."""
        button = self.query_one(f"#custom-{index}", Button)
        button.label = resolve_title(
            self.app.custom_buttons,
            index,
            device_id=self._device.id,
            platform=self._device.platform,
        )
        # The `label` reactive repaints text but is `layout=False`, so the button's
        # auto width stays stale (it keeps its mount-time size until the remote is
        # reopened). Force a layout pass so a longer/shorter title resizes it now.
        button.refresh(layout=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("key-"):
            await self._send(Key[button_id.removeprefix("key-").upper()])
        elif button_id.startswith("custom-"):
            self._activate_custom(int(button_id.removeprefix("custom-")))

    def _activate_custom(self, index: int) -> None:
        # One dispatch shared by a click and the keyboard shortcut, so both behave
        # identically. Edit-mode armed → configure and disarm; otherwise run the
        # button's resolved action, or configure it when it has none.
        if self._edit_mode:
            self._edit_mode = False
            self._configure_custom(index)
            return
        action = resolve_action(
            self.app.custom_buttons,
            index,
            device_id=self._device.id,
            platform=self._device.platform,
        )
        if action:
            self._run_action(action)
        else:
            self._configure_custom(index)

    def action_activate_custom(self, index: int) -> None:
        self._activate_custom(index)

    def action_edit_mode(self) -> None:
        # Arm edit-mode: the next custom-button activation opens its config instead of
        # running it. A toast is the only cue, since the gesture is otherwise silent.
        self._edit_mode = True
        self.app.notify("Edit mode: activate a custom button to configure it.")

    def _run_action(self, action: dict) -> None:
        # Run in a worker so a slow script never blocks the remote; the outcome is
        # surfaced per the action's Results choice when it finishes.
        self.run_worker(self._execute(action))

    async def _execute(self, action: dict) -> None:
        result = await run_action(action, self._device.ip)
        present_result(self.app, result, show_results=bool(action.get("show_results")))

    def _configure_custom(self, index: int) -> None:
        def _relabel(saved: bool | None) -> None:
            if saved:
                self._label_custom(index)

        self.app.push_screen(ButtonConfigModal(index, self._device), _relabel)

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
            self.app.notify(
                f"{key.name} is not supported on this device", severity="warning"
            )
        except Exception:
            # A single failed key press (device timeout, dropped connection) must
            # not take down the remote — report it and stay on-screen.
            self.app.notify(
                f"{key.name} failed — the device may be unreachable",
                severity="warning",
            )

    def action_text_mode(self) -> None:
        # Text moved off the docked field into an on-demand modal; when the adapter
        # has no text support there is nothing to open, so surface a message instead.
        if not self._capabilities.text:
            self.app.notify(
                "Text entry is not supported on this device", severity="warning"
            )
            return
        self.app.push_screen(TextEntryModal(self._session))

    async def action_go_back(self) -> None:
        # The remote's Go Back closes the live session before popping the screen;
        # every other screen's Go Back just pops.
        await self._session.close()
        self.app.pop_screen()
