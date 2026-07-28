"""The macros modals: the saved-macro list, a macro's detail editor, and the pause
prompt, plus the Vim-navigable option list they share.

Neither the list nor the detail modal drives the flow itself — each dismisses with
what the user chose and lets `RemoteScreen` act on it. That is deliberate: recording
needs every modal off the screen stack, because Textual truncates a screen's binding
chain at the topmost modal, so a modal left mounted would produce a remote that
ignores every key.

The detail modal edits an in-memory draft and never writes: the remote persists it
only when the user saves. That is what makes Close-discards-changes true, and what
lets Add Step leave for the live remote and come back with every unsaved edit intact.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList
from textual.widgets.option_list import Option

from ..macros.models import (
    Macro,
    delete_step,
    insert_after,
    move_down,
    move_up,
    pause_step,
    step_description,
)
from ..macros.registry import list_macros

# ConfirmDeleteScreen lives with the device screens that first needed it; its
# "Delete {name}?" prompt is name-agnostic, so a macro reuses it as-is.
from .devices_screen import ConfirmDeleteScreen

# What the list modal dismisses with, paired with a macro id where one applies.
CREATE_MACRO = "create"
OPEN_MACRO = "open"

# What the detail modal dismisses with, paired with its draft and selected step.
SAVE_MACRO = "save"
DELETE_MACRO = "delete"
ADD_STEP = "add_step"
# Deliberately not named RUN_MACRO: that name is already the action-type id the remote
# imports from `.actions`, and shadowing it would silence the nested-macro guard.
PLAY_MACRO = "play"


class MacroOptionList(OptionList):
    """An OptionList that also answers `j`/`k`, matching the D-pad's Vim keys."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]


class MacrosListModal(ModalScreen[tuple[str, str | None] | None]):
    """Lists every saved macro by name; dismisses with what to do next.

    Dismisses None on Close, `(CREATE_MACRO, None)` to record a new macro, or
    `(OPEN_MACRO, macro_id)` to edit one.
    """

    BINDINGS = [Binding("escape", "close", "Close")]

    DEFAULT_CSS = """
    MacrosListModal { align: center middle; background: $background 60%; }
    /* A bounded height with a 1fr list is what makes the list scroll while the
       buttons stay reachable on a short terminal. */
    #macros-list {
        width: 70%; height: 80%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #macros-list-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #macros-list-options { width: 100%; height: 1fr; }
    #macros-list-buttons {
        width: 100%; height: auto; align-horizontal: center; margin-top: 1;
    }
    /* min-width overrides Textual's Button default (16) so both buttons fit. */
    #macros-list-buttons Button { width: 16; min-width: 0; margin: 0 1; }
    """

    def __init__(self, macros: dict, selected_id: str | None = None) -> None:
        super().__init__()
        self._macros = macros
        # The macro to highlight on open — a macro just recorded, saved, or edited.
        self._selected_id = selected_id

    def compose(self) -> ComposeResult:
        with Vertical(id="macros-list"):
            yield Label("Macros", id="macros-list-title")
            yield MacroOptionList(*self._rows(), id="macros-list-options")
            with Horizontal(id="macros-list-buttons"):
                yield Button("Create Macro", id="macros-create", variant="primary")
                yield Button("Close", id="macros-close")

    def _rows(self) -> list[Option]:
        """One row per saved macro, or a single unselectable placeholder when none."""
        saved = list_macros(self._macros)
        if not saved:
            # Disabled so Enter on it cannot open anything: there is nothing to open.
            return [Option("No macros yet", disabled=True)]
        return [Option(macro.name, id=macro.id) for macro in saved]

    def on_mount(self) -> None:
        options = self.query_one(MacroOptionList)
        options.focus()
        ids = [macro.id for macro in list_macros(self._macros)]
        if self._selected_id in ids:
            options.highlighted = ids.index(self._selected_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss((OPEN_MACRO, event.option.id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "macros-create":
            self.dismiss((CREATE_MACRO, None))
        elif event.button.id == "macros-close":
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


class PauseDurationModal(ModalScreen[int | None]):
    """Prompts for a pause duration in milliseconds; OK returns it, Cancel None.

    Anything that is not a non-negative whole number returns None, so an invalid
    entry inserts or changes nothing rather than storing a nonsense duration.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    PauseDurationModal { align: center middle; background: $background 60%; }
    #pause-duration {
        width: 60%; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #pause-duration-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #pause-duration-ms { width: 100%; margin-bottom: 1; }
    #pause-duration-buttons { width: 100%; height: auto; align-horizontal: center; }
    #pause-duration-buttons Button { width: 14; min-width: 0; margin: 0 1; }
    """

    def __init__(self, ms: int | None = None) -> None:
        super().__init__()
        # The step's current duration when editing an existing pause, so the prompt
        # opens prefilled and the value can be changed rather than retyped.
        self._ms = ms

    def compose(self) -> ComposeResult:
        with Vertical(id="pause-duration"):
            yield Label("Pause for how many milliseconds?", id="pause-duration-title")
            yield Input(
                value="" if self._ms is None else str(self._ms),
                placeholder="e.g. 500",
                id="pause-duration-ms",
            )
            with Horizontal(id="pause-duration-buttons"):
                yield Button("OK", id="pause-duration-ok", variant="primary")
                yield Button("Cancel", id="pause-duration-cancel")

    def on_mount(self) -> None:
        self.query_one("#pause-duration-ms", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(_milliseconds(event.value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pause-duration-ok":
            self.dismiss(
                _milliseconds(self.query_one("#pause-duration-ms", Input).value)
            )
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


def _milliseconds(text: str) -> int | None:
    """`text` as a non-negative whole number of milliseconds, or None if it is not.

    `isdigit` is the whole check: it rejects a negative, a fraction, and anything
    non-numeric in one go.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else None


class MacroDetailModal(ModalScreen[tuple[str, Macro, int] | None]):
    """Edits one macro as a draft: its name, its step order, and its step list.

    Renders from the draft it is given and mutates only that draft, so Close discards
    everything. Dismisses None on Close, or `(choice, draft, selected_index)` where
    choice is Save, Delete, Add Step, or Run — the remote persists, deletes, starts a
    capture-one recording, or plays the saved macro accordingly.
    """

    BINDINGS = [Binding("escape", "close", "Close")]

    DEFAULT_CSS = """
    MacroDetailModal { align: center middle; background: $background 60%; }
    /* A bounded height with a 1fr step list is what keeps both button rows reachable
       on a short terminal: the list scrolls instead of the buttons clipping. */
    #macro-detail {
        width: 90%; height: 90%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    /* No vertical margins anywhere in here: the default-pause row costs three rows the
       shortest supported terminal does not have spare, and the three margins that used
       to sit under the title, under the name, and above the buttons pay for it. */
    #macro-detail-title {
        width: 100%; text-align: center; text-style: bold;
    }
    #macro-detail-name { width: 100%; }
    #macro-detail-steps-label { width: 100%; color: $text-muted; }
    /* No border, unlike OptionList's default: its `tall` border costs the list two
       rows, which on the shortest supported terminal (80x24) is the whole height the
       1fr list gets — it rendered empty. The modal's own border already frames it. */
    #macro-detail-steps { width: 100%; height: 1fr; border: none; }
    #macro-detail-step-buttons {
        width: 100%; height: auto; align-horizontal: center;
    }
    /* The label shares the input's three rows rather than taking one of its own. */
    #macro-detail-pause-row { width: 100%; height: 3; }
    #macro-detail-pause-label {
        width: auto; height: 3; content-align: left middle; margin-right: 1;
    }
    #macro-detail-pause { width: 12; }
    #macro-detail-buttons {
        width: 100%; height: auto; align-horizontal: center;
    }
    /* Five step controls share the row (1fr) and four macro controls take a fixed
       width; min-width overrides Textual's Button default of 16, which would
       overflow the supported 80 columns on either row. */
    #macro-detail-step-buttons Button { width: 1fr; min-width: 0; margin: 0 1; }
    /* 14, not 16: four buttons plus their side margins are 64 columns, and the modal's
       content is only 66 wide at the supported 80 — a fourth 16 would overflow. */
    #macro-detail-buttons Button { width: 14; min-width: 0; margin: 0 1; }
    """

    def __init__(self, draft: Macro, selected: int = 0) -> None:
        super().__init__()
        self._draft = draft
        self._selected = selected

    def compose(self) -> ComposeResult:
        with Vertical(id="macro-detail"):
            yield Label("Edit Macro", id="macro-detail-title")
            yield Input(
                value=self._draft.name, placeholder="Macro name", id="macro-detail-name"
            )
            yield Label("Steps", id="macro-detail-steps-label")
            yield MacroOptionList(*self._rows(), id="macro-detail-steps")
            with Horizontal(id="macro-detail-step-buttons"):
                yield Button("Up", id="step-up")
                yield Button("Down", id="step-down")
                yield Button("Remove", id="step-remove")
                yield Button("+ Step", id="step-add")
                yield Button("+ Pause", id="step-pause")
            with Horizontal(id="macro-detail-pause-row"):
                yield Label(
                    "Default pause between steps (ms)", id="macro-detail-pause-label"
                )
                yield Input(
                    value=str(self._draft.step_pause_ms),
                    placeholder="500",
                    id="macro-detail-pause",
                )
            with Horizontal(id="macro-detail-buttons"):
                yield Button("Save", id="macro-save", variant="primary")
                yield Button("Run", id="macro-run")
                yield Button("Close", id="macro-close")
                yield Button("Delete", id="macro-delete", variant="error")

    def _rows(self) -> list[Option]:
        """One numbered, described row per step, or an unselectable empty placeholder."""
        if not self._draft.steps:
            return [Option("No steps", disabled=True)]
        return [
            Option(f"{number}. {step_description(step)}")
            for number, step in enumerate(self._draft.steps, start=1)
        ]

    def on_mount(self) -> None:
        steps = self.query_one("#macro-detail-steps", MacroOptionList)
        steps.focus()
        if self._draft.steps:
            steps.highlighted = min(self._selected, len(self._draft.steps) - 1)

    def _selected_index(self) -> int:
        """The highlighted step's index, or -1 when the draft holds no steps."""
        if not self._draft.steps:
            return -1
        highlighted = self.query_one("#macro-detail-steps", MacroOptionList).highlighted
        return -1 if highlighted is None else highlighted

    def _refresh_steps(self, selected: int) -> None:
        """Rebuild the step list from the draft, keeping `selected` highlighted."""
        steps = self.query_one("#macro-detail-steps", MacroOptionList)
        steps.clear_options()
        steps.add_options(self._rows())
        if self._draft.steps:
            steps.highlighted = max(0, min(selected, len(self._draft.steps) - 1))

    def _sync_inputs(self) -> None:
        """Take the edited name and default pause into the draft before it leaves.

        An invalid pause leaves the draft's own value alone, matching the pause prompt:
        a value that is not a non-negative whole number of milliseconds changes nothing
        rather than storing a nonsense pace.
        """
        self._draft.name = self.query_one("#macro-detail-name", Input).value
        ms = _milliseconds(self.query_one("#macro-detail-pause", Input).value)
        if ms is not None:
            self._draft.step_pause_ms = ms

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        index = self._selected_index()
        if button_id == "step-up":
            self._refresh_steps(move_up(self._draft.steps, index))
        elif button_id == "step-down":
            self._refresh_steps(move_down(self._draft.steps, index))
        elif button_id == "step-remove":
            delete_step(self._draft.steps, index)
            self._refresh_steps(index)
        elif button_id == "step-add":
            self._sync_inputs()
            self.dismiss((ADD_STEP, self._draft, index))
        elif button_id == "step-pause":
            self._prompt_pause(index)
        elif button_id == "macro-save":
            self._sync_inputs()
            self.dismiss((SAVE_MACRO, self._draft, index))
        elif button_id == "macro-run":
            # No `_sync_inputs`: Run leaves the draft behind like Close does, so what
            # plays is the macro as saved.
            self.dismiss((PLAY_MACRO, self._draft, index))
        elif button_id == "macro-close":
            self.dismiss(None)
        elif button_id == "macro-delete":
            self._confirm_delete(index)

    def _confirm_delete(self, index: int) -> None:
        """Ask before deleting, dismissing only once the user confirms.

        Cancelling leaves this modal mounted with its draft untouched, which is why the
        prompt is pushed from here rather than after a dismiss: there is nothing to
        restore. The name is synced first so the prompt names the macro as the user has
        just renamed it, not as it was saved.
        """
        self._sync_inputs()

        def _confirmed(confirmed: bool | None) -> None:
            if confirmed:
                self.dismiss((DELETE_MACRO, self._draft, index))

        self.app.push_screen(ConfirmDeleteScreen(self._draft.name), _confirmed)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        # Opening an existing pause step reopens the duration prompt on it, so the
        # value can be changed; other step types have nothing to open.
        index = self._selected_index()
        if 0 <= index < len(self._draft.steps):
            step = self._draft.steps[index]
            if step.get("type") == "pause":
                self._prompt_pause(index, editing=True)

    def _prompt_pause(self, index: int, *, editing: bool = False) -> None:
        """Ask for a duration, then insert a pause after `index` or replace it."""
        current = self._draft.steps[index].get("ms") if editing else None

        def _entered(ms: int | None) -> None:
            if ms is None:  # cancelled or invalid: change nothing
                return
            if editing:
                # Replaced, never mutated in place: the step dict may still be the one
                # the saved registry holds, and an unsaved edit must not reach it.
                self._draft.steps[index] = pause_step(ms)
                self._refresh_steps(index)
            else:
                self._refresh_steps(
                    insert_after(self._draft.steps, index, pause_step(ms))
                )

        self.app.push_screen(PauseDurationModal(current), _entered)

    def action_close(self) -> None:
        self.dismiss(None)
