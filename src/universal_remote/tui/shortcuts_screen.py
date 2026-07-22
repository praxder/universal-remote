"""The Keyboard Shortcuts screen and its key-capture modal.

The screen renders one row per catalogued action (`Action | Shortcut`) from the
app's override map; reserved entries appear as dimmed, non-activatable rows.
Activating a rebindable row opens the capture modal, which reads the next key,
validates it against the reserved-key and conflict rules, and on success updates
the overrides, persists them, and rebuilds every mounted screen's bindings.
"""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

from .shortcuts import (
    CATALOG,
    Scope,
    conflicting_label,
    display_label,
    effective_key,
    is_reserved,
    rebuild_shortcuts,
)

_BY_ID = {action.id: action for action in CATALOG}


def _shortcut_text(action, overrides: dict[str, str]) -> str:
    """The Shortcut cell text: the D-pad shows arrow / alias, others a single key."""
    if not action.editable and action.aliases:
        keys = (action.default_key, *action.aliases)
        return " / ".join(display_label(key) for key in keys)
    return display_label(effective_key(action.id, overrides))


class ShortcutsScreen(Screen[None]):
    """Lists every action and its shortcut; rebindable rows open the capture modal."""

    # Go Back (Escape by default) returns to Settings; built on mount like every
    # other non-root screen.
    SHORTCUT_SCOPES = frozenset({Scope.GLOBAL})

    DEFAULT_CSS = """
    ShortcutsScreen { align: center top; }
    #shortcuts { width: 100%; height: 1fr; }
    #shortcuts-title {
        width: 100%; text-align: center; margin: 1 0; text-style: bold; color: $accent;
    }
    #shortcuts-table { height: 1fr; width: 100%; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="shortcuts"):
            yield Static("Keyboard Shortcuts", id="shortcuts-title")
            yield DataTable(id="shortcuts-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        rebuild_shortcuts(self, self.app.shortcut_overrides, self.SHORTCUT_SCOPES)
        table = self.query_one(DataTable)
        table.add_column("Action", key="action")
        table.add_column("Shortcut", key="shortcut")
        for action in CATALOG:
            self._add_row(table, action)
        table.focus()

    def _add_row(self, table: DataTable, action) -> None:
        text = _shortcut_text(action, self.app.shortcut_overrides)
        if action.editable:
            table.add_row(action.label, text, key=action.id)
        else:
            # Reserved rows are dimmed and cannot be activated for capture.
            table.add_row(
                Text(action.label, style="dim"),
                Text(text, style="dim"),
                key=action.id,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        action = _BY_ID[event.row_key.value]
        if not action.editable:
            return  # reserved rows are display-only
        self.app.push_screen(CaptureModal(action.id), self._on_captured)

    def _on_captured(self, action_id: str | None) -> None:
        if action_id is None:
            return  # cancelled: nothing changed
        table = self.query_one(DataTable)
        table.update_cell(
            action_id,
            "shortcut",
            _shortcut_text(_BY_ID[action_id], self.app.shortcut_overrides),
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()


class CaptureModal(ModalScreen[str | None]):
    """Reads the next key press and assigns, clears, or cancels a shortcut.

    Dismisses with the action id when the shortcut changed (so the table refreshes
    that row), or None when cancelled. A refused key (reserved or already taken)
    toasts and leaves the modal open to retry.
    """

    DEFAULT_CSS = """
    CaptureModal { align: center middle; background: $background 60%; }
    #capture {
        width: auto; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #capture Label { width: 100%; text-align: center; }
    #capture-hint { color: $text-muted; margin-bottom: 1; }
    #capture Button { width: 16; margin-top: 1; }
    """

    def __init__(self, action_id: str) -> None:
        super().__init__()
        self._action = _BY_ID[action_id]

    def compose(self) -> ComposeResult:
        with Vertical(id="capture"):
            yield Label(f"Press a key for {self._action.label}…", id="capture-prompt")
            yield Label("Delete clears · Esc cancels", id="capture-hint")
            # Mouse-only: keys are captured by the modal, so the button must not
            # steal focus and swallow the next keypress.
            cancel = Button("Cancel", id="capture-cancel")
            cancel.can_focus = False
            yield cancel

    def on_key(self, event: events.Key) -> None:
        # The modal captures every key: Escape cancels, Delete clears, anything else
        # is a candidate shortcut. Stop the event so it never reaches the bindings.
        event.stop()
        event.prevent_default()
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "delete":
            self._clear()
        else:
            self._assign(event.key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)  # Cancel

    def _assign(self, key: str) -> None:
        overrides = self.app.shortcut_overrides
        if key != self._action.default_key:
            if is_reserved(key):
                self.app.notify(
                    f"{display_label(key)} is reserved and can't be assigned.",
                    severity="error",
                )
                return
            owner = conflicting_label(self._action.id, key, overrides)
            if owner is not None:
                self.app.notify(
                    f"{display_label(key)} is already taken by {owner}.",
                    severity="error",
                )
                return
        if key == self._action.default_key:
            overrides.pop(self._action.id, None)  # back to default → not stored
        else:
            overrides[self._action.id] = key
        self._commit()

    def _clear(self) -> None:
        overrides = self.app.shortcut_overrides
        if self._action.default_key == "":
            overrides.pop(self._action.id, None)  # already had no shortcut
        else:
            overrides[self._action.id] = ""  # explicitly cleared, differs from default
        self._commit()

    def _commit(self) -> None:
        self.app.persist_preferences()
        self.app.apply_shortcuts()
        self.dismiss(self._action.id)
