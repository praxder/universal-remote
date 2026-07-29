"""The on-screen remote surface: clickable buttons plus keyboard control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable

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
    Rule,
)

from ..errors import TextUnsupportedError, UnsupportedKeyError
from ..keys import Key
from ..macros.models import Macro, action_step, insert_after, key_step, text_step
from ..macros.registry import add, create, delete, get
from .actions import (
    RUN_MACRO,
    ActionContext,
    ActionTypeListModal,
    action_type,
    present_result,
    run_action,
)
from .macros_screen import (
    ADD_STEP,
    CREATE_MACRO,
    DELETE_MACRO,
    OPEN_MACRO,
    PLAY_MACRO,
    SAVE_MACRO,
    MacroDetailModal,
    MacrosListModal,
    RecordingHintModal,
)
from .custom_buttons import (
    ButtonScope,
    clear_entry,
    clear_more_specific,
    default_title,
    resolve_action,
    resolve_scope,
    resolve_title,
    set_action,
    set_title,
)
from .shortcuts import Scope, rebuild_shortcuts

if TYPE_CHECKING:
    from textual.timer import Timer

    from ..capabilities import Capabilities
    from ..devices.models import Device
    from ..session import Session


class RecordMode(Enum):
    """How a macro recording ends.

    `APPEND_UNTIL_STOP` runs until the user stops it (recording a whole macro);
    `CAPTURE_ONE` ends itself after a single interaction (adding one step to a draft).
    """

    APPEND_UNTIL_STOP = "append_until_stop"
    CAPTURE_ONE = "capture_one"


@dataclass
class Recording:
    """A recording in progress: its mode, what it captured, and where it returns.

    `on_done` receives the captured steps, or None when the recording was cancelled,
    so whatever started the recording decides what each outcome means.
    """

    mode: RecordMode
    on_done: Callable[[list[dict] | None], None]
    steps: list[dict] = field(default_factory=list)


# The header's recording indicator. Kept to eleven columns because the header also
# holds the device's name, type, and IP: a longer text (naming the cancelling key, say)
# ellipsizes that at the supported 80-column width.
RECORDING_TEXT = "● RECORDING"

# The indicator's pulse: `text_opacity` stops, cycled in order, one step per interval.
# Fading the opacity keeps the text red the whole way, where cycling colors would not,
# and the floor stays high enough that the dim end still reads as red rather than as
# the header's background showing through.
PULSE_OPACITIES = (1.0, 0.85, 0.7, 0.55, 0.45, 0.55, 0.7, 0.85)
PULSE_STEP_SECONDS = 0.12


class RecordingIndicator(Label):
    """`● RECORDING`, fading in and out while a recording is in progress.

    The fade is stepped by a timer rather than by Textual's animation system: a
    never-ending animation leaves the animator permanently busy, and `Pilot.press`
    waits for it to finish, so an animated pulse hangs every test that presses a key
    while recording.
    """

    def __init__(self) -> None:
        super().__init__("", id="recording-indicator")
        self._pulse: Timer | None = None
        self._step = 0

    def start_pulse(self) -> None:
        """Show the indicator and fade it in and out until stopped."""
        if self._pulse is not None:
            return
        self.update(RECORDING_TEXT)
        self.display = True
        self._step = 0
        self._pulse = self.set_interval(PULSE_STEP_SECONDS, self._fade)

    def stop_pulse(self) -> None:
        """Hide the indicator and end the fade, leaving it fully opaque."""
        if self._pulse is not None:
            self._pulse.stop()
            self._pulse = None
        self.styles.text_opacity = 1.0
        self.display = False

    def _fade(self) -> None:
        self._step = (self._step + 1) % len(PULSE_OPACITIES)
        self.styles.text_opacity = PULSE_OPACITIES[self._step]


class RemoteHeader(Header):
    """The header bar, plus a recording indicator on its right side.

    The indicator lives here rather than among the remote's buttons because it
    reports application state (a recording is running), not a key you can press —
    the same bar already carries the device's name, type, and IP. It takes the slot
    Textual reserves for the optional header clock, which this app never shows, so
    the indicator sits flush right and the device text keeps those columns while no
    recording is running.
    """

    DEFAULT_CSS = """
    RemoteHeader HeaderClockSpace { display: none; }
    RemoteHeader #recording-indicator {
        dock: right; width: auto; height: 1; padding: 0 1;
        color: $error; text-style: bold; display: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield from super().compose()
        yield RecordingIndicator()


class TextEntryModal(ModalScreen[str | None]):
    """On-demand text entry: type then Enter sends once and dismisses; Escape cancels.

    Owns the send path so the remote surface no longer reserves a docked field.
    Escape is bound here so it dismisses the modal rather than reaching the remote's
    Go Back (which would close the session). Transient outcomes — a failed send, or
    an ADB path that fell back — surface as app-level toasts that outlive the modal.
    Dismisses with the text that actually reached the device, or None when nothing
    did, so a recording captures only a send that landed.
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
        sent = await self._send(event.value) if event.value else False
        self.dismiss(event.value if sent else None)

    async def _send(self, text: str) -> bool:
        """Send `text`, reporting whether the device actually received it."""
        try:
            await self._session.send_text(text)
        except TextUnsupportedError:
            self.app.notify(
                "Text entry is not supported on this device", severity="warning"
            )
            return False
        except Exception:
            # A failed text send (device timeout, dropped connection) must not take
            # down the remote — report it and return, like the key-send path.
            self.app.notify(
                "Text entry failed — the device may be unreachable", severity="warning"
            )
            return False
        return True

    def action_cancel(self) -> None:
        self.dismiss(None)


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
        width: 70%; height: auto; padding: 1 2;
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
    /* min-width overrides Textual's Button default (16) so three buttons fit the row
       without the last one clipping. */
    #button-config-buttons Button { width: 14; min-width: 0; margin: 0 1; }
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
                yield Button("Reset", id="button-config-reset")

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
        elif event.button.id == "button-config-reset":
            self._reset()
        elif event.button.id == "button-config-action-type":
            # Pass the button's current action so re-editing it prefills the action's
            # config instead of opening blank.
            self.app.push_screen(ActionTypeListModal(self._action), self._action_chosen)

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
        # Keep the button in one place: drop any entry at a more-specific scope so the
        # chosen scope is what resolves, then write the title and action there.
        clear_more_specific(
            self.app.custom_buttons,
            self._index,
            scope,
            device_id=self._device.id,
            platform=self._device.platform,
        )
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

    def _reset(self) -> None:
        # Clear the button at every scope for this device, so it returns to its default
        # title and no action, then persist and close.
        clear_entry(
            self.app.custom_buttons,
            self._index,
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
    /* Edit-mode cue: the custom buttons switch to a warning-colored, bold border
       while edit-mode is armed, so it reads as "editing" rather than "run". */
    #remote Button.edit-armed { border: round $warning; text-style: bold; }
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
    /* Marks where the device keys end and the app's own Macros control begins. One row
       of the buttons' three, offset down onto their middle line, so it reads as a mark
       between the two groups rather than a border spanning them. */
    #row-top-divider { height: 1; margin: 1 1 0 1; color: $primary; }
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
        # The macro recording in progress, or None. While set, every interaction the
        # remote performs is captured as a step and the Macros button ends it.
        self._recording: Recording | None = None

    def compose(self) -> ComposeResult:
        # The device name lives in the header (see on_mount), not a separate row,
        # so the button set gets that row back.
        yield RemoteHeader()
        with Container(id="remote"):
            with Horizontal(id="row-top"):
                yield self._key_button(Key.MENU, "☰ Menu")
                yield self._key_button(Key.HOME, "⌂ Home")
                yield self._key_button(Key.BACK, "↩ Back")
                yield Rule(orientation="vertical", id="row-top-divider")
                yield self._macros_button()
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

    def _macros_button(self) -> Button:
        # The fourth top-row control, sitting past the divider because it configures
        # the app rather than sending a key: it opens the macros list, and doubles as
        # the end-recording control while a recording is in progress (see
        # `_apply_recording_ui`), which is what keeps recording free of extra rows.
        button = Button("Macros", id="macros")
        button.can_focus = False
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
        elif button_id == "macros":
            self._macros_control()

    def _activate_custom(self, index: int) -> None:
        # One dispatch shared by a click and the keyboard shortcut, so both behave
        # identically. Edit-mode armed → configure and disarm; otherwise run the
        # button's resolved action, or configure it when it has none.
        if self._edit_mode:
            self._set_edit_mode(False)
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
            self._capture_action(action)
        else:
            self._configure_custom(index)

    def _capture_action(self, action: dict) -> None:
        """Capture a dispatched custom-button action, refusing a nested macro.

        Captured when dispatched rather than when it finishes — a custom action runs
        in the background, so its outcome is not known yet. A Run Macro action is
        refused outright: the snapshot would invoke a macro from inside a macro and
        could recurse forever, so record time says no rather than leaving the user a
        step that looks valid and always fails.
        """
        if self._recording is None:
            return
        if action.get("type") == RUN_MACRO:
            self.app.notify(
                "Nested macros are not supported — that step was not recorded.",
                severity="warning",
            )
            return
        self._capture(action_step(action))

    def action_activate_custom(self, index: int) -> None:
        self._activate_custom(index)

    def action_macros(self) -> None:
        # The catalogued Macros action: identical to clicking the Macros button.
        self._macros_control()

    def _macros_control(self) -> None:
        """Open the macros list, or end the recording in progress.

        While recording, this control *is* the Stop (append) or Cancel (capture-one)
        button, so a click or the Macros shortcut ends the recording: Stop keeps what
        was captured, Cancel keeps nothing.
        """
        recording = self._recording
        if recording is None:
            self._open_macros_list()
        elif recording.mode is RecordMode.APPEND_UNTIL_STOP:
            self._finish_recording(recording.steps)
        else:
            self._finish_recording(None)

    def _open_macros_list(self, selected_id: str | None = None) -> None:
        """Show the saved macros, highlighting `selected_id` when given."""
        self.app.push_screen(
            MacrosListModal(self.app.macros, selected_id), self._macros_list_closed
        )

    def _macros_list_closed(self, outcome: tuple[str, str | None] | None) -> None:
        """Act on the macros list's choice; None means it was closed unchanged."""
        if outcome is None:
            return
        choice, macro_id = outcome
        if choice == CREATE_MACRO:
            self._begin_new_macro()
        elif choice == OPEN_MACRO and macro_id:
            macro = get(self.app.macros, macro_id)
            if macro is not None:
                self._open_macro_detail(macro)

    def _begin_new_macro(self) -> None:
        """Explain the recording state, then start recording — or start it straight away.

        The hint is pushed from here rather than from the macros list because the list
        has already dismissed itself by now, and recording needs the screen stack clear
        anyway. Gating on the saved preference is what makes "don't show this again"
        mean it.
        """
        if self.app.hide_recording_hint:
            self._start_recording(
                RecordMode.APPEND_UNTIL_STOP, self._new_macro_recorded
            )
            return
        self.app.push_screen(RecordingHintModal(), self._recording_hint_closed)

    def _recording_hint_closed(self, suppress: bool | None) -> None:
        """Start recording once the hint is acknowledged; Cancel reopens the list.

        `suppress` is the checkbox's state, so False is a real answer — only None means
        the user cancelled, and cancelling stores nothing however the box was left.
        """
        if suppress is None:
            self._open_macros_list()
            return
        if suppress:
            self.app.hide_recording_hint = True
            self.app.persist_preferences()
        self._start_recording(RecordMode.APPEND_UNTIL_STOP, self._new_macro_recorded)

    def _new_macro_recorded(self, steps: list[dict] | None) -> None:
        """Save an append-mode recording, then reopen the list on its outcome."""
        if steps is None:  # cancelled: nothing saved
            self._open_macros_list()
            return
        if not steps:
            self.app.notify("Nothing was recorded, so no macro was created.")
            self._open_macros_list()
            return
        macro = create(self.app.macros, steps)
        self.app.persist_preferences()
        self._open_macros_list(macro.id)

    def _open_macro_detail(self, draft: Macro, selected: int = 0) -> None:
        """Edit `draft` — a macro loaded from the registry, or one carried back from
        a capture-one recording with its unsaved edits still on it."""
        self.app.push_screen(
            MacroDetailModal(draft, selected), self._macro_detail_closed
        )

    def _macro_detail_closed(self, outcome: tuple[str, Macro, int] | None) -> None:
        """Persist, delete, play, or record one step, per the detail modal's choice.

        None means Close, which discards every edit the draft held — the detail modal
        never writes, so simply dropping the draft is what makes that true.
        """
        if outcome is None:
            self._open_macros_list()
            return
        choice, draft, index = outcome
        if choice == SAVE_MACRO:
            add(self.app.macros, draft)
            self.app.persist_preferences()
            self._open_macros_list(draft.id)
        elif choice == DELETE_MACRO:
            delete(self.app.macros, draft.id)
            self.app.persist_preferences()
            self._open_macros_list()
        elif choice == PLAY_MACRO:
            # Dispatched as the catalogued Run Macro action, which is what makes it play
            # exactly as a custom button plays it: the saved macro, behind the playback
            # modal, reporting its own outcome. The list is not reopened — the user asked
            # for the macro, not for more editing.
            self._run_action({"type": RUN_MACRO, "macro_id": draft.id})
        elif choice == ADD_STEP:
            self._start_recording(
                RecordMode.CAPTURE_ONE,
                lambda steps: self._step_captured(draft, index, steps),
            )

    def _step_captured(
        self, draft: Macro, index: int, steps: list[dict] | None
    ) -> None:
        """Reopen the detail modal, inserting a captured step after `index`.

        A cancelled capture returns the draft exactly as it was, so a rename or a
        reorder made before Add Step survives either outcome.
        """
        selected = index
        if steps:
            selected = insert_after(draft.steps, index, steps[0])
        self._open_macro_detail(draft, max(selected, 0))

    def _start_recording(
        self, mode: RecordMode, on_done: Callable[[list[dict] | None], None]
    ) -> None:
        """Begin capturing interactions; `on_done` receives the outcome."""
        self._recording = Recording(mode=mode, on_done=on_done)
        self._apply_recording_ui()

    def _finish_recording(self, steps: list[dict] | None) -> None:
        """End the recording and hand `steps` (or None, for cancelled) to its owner."""
        recording = self._recording
        if recording is None:
            return
        self._recording = None
        self._apply_recording_ui()
        recording.on_done(steps)

    def _capture(self, step: dict) -> None:
        """Append `step` to the recording, ending a capture-one recording with it."""
        recording = self._recording
        if recording is None:
            return
        recording.steps.append(step)
        if recording.mode is RecordMode.CAPTURE_ONE:
            self._finish_recording(recording.steps)

    def _apply_recording_ui(self) -> None:
        """Point the Macros button and the indicator at the current recording state."""
        button = self.query_one("#macros", Button)
        indicator = self.query_one("#recording-indicator", RecordingIndicator)
        recording = self._recording
        if recording is None:
            button.label = "Macros"
            indicator.stop_pulse()
        else:
            append = recording.mode is RecordMode.APPEND_UNTIL_STOP
            button.label = "■ Stop" if append else "■ Cancel"
            indicator.start_pulse()
        # `label` repaints but is layout=False, so the button would otherwise keep its
        # mount-time width and clip the longer label (see `_label_custom`).
        button.refresh(layout=True)

    def action_edit_mode(self) -> None:
        # Toggle edit-mode: `e` arms it, `e` again disarms it. While armed, the next
        # custom-button activation opens its config instead of running it, and the
        # custom buttons carry a visual cue. A toast names the new state.
        if self._edit_mode:
            self._set_edit_mode(False)
            self.app.notify("Edit mode off.")
            return
        self._set_edit_mode(True)
        self.app.notify("Edit mode: activate a custom button to configure it.")

    def _set_edit_mode(self, armed: bool) -> None:
        # One place toggles the flag and the visual cue on the custom buttons, so the
        # indicator can never outlive the armed state.
        self._edit_mode = armed
        for index in range(1, 6):
            self.query_one(f"#custom-{index}", Button).set_class(armed, "edit-armed")

    def _run_action(self, action: dict) -> None:
        # Run in a worker so a slow script never blocks the remote; the outcome is
        # surfaced per the action's Results choice when it finishes.
        self.run_worker(self._execute(action))

    async def _execute(self, action: dict) -> None:
        result = await run_action(action, self._action_context())
        entry = action_type(action.get("type"))
        if entry is not None and entry.reports_own_outcome:
            # The action already told the user how it went — macro playback names a
            # failing step in its own error, and a cancelled run is not an error at
            # all. `present_result` would toast any not-ok result as "Script failed".
            return
        present_result(self.app, result, show_results=bool(action.get("show_results")))

    def _action_context(self) -> ActionContext:
        """The execution context every catalog action is run with.

        Gathers the live session and the active device alongside the saved macros and
        custom buttons, so a runner reads what its own type needs without the remote
        knowing which type that is.
        """
        return ActionContext(
            app=self.app,
            remote_ip=self._device.ip,
            session=self._session,
            macros=self.app.macros,
            custom_buttons=self.app.custom_buttons,
            device_id=self._device.id,
            platform=self._device.platform,
        )

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
        else:
            # Captured only after a successful send, so a key the adapter does not
            # support and a send that failed both record nothing.
            self._capture(key_step(key.name))

    def action_text_mode(self) -> None:
        # Text moved off the docked field into an on-demand modal; when the adapter
        # has no text support there is nothing to open, so surface a message instead.
        if not self._capabilities.text:
            self.app.notify(
                "Text entry is not supported on this device", severity="warning"
            )
            return
        self.app.push_screen(TextEntryModal(self._session), self._text_sent)

    def _text_sent(self, text: str | None) -> None:
        """Capture a text send that reached the device; None means none did."""
        if text:
            self._capture(text_step(text))

    async def action_go_back(self) -> None:
        # While a recording is in progress, Go Back cancels it and the remote stays
        # open with its session connected. Otherwise the remote's Go Back closes the
        # live session before popping the screen; every other screen's just pops.
        if self._recording is not None:
            self._finish_recording(None)
            return
        await self._session.close()
        self.app.pop_screen()
