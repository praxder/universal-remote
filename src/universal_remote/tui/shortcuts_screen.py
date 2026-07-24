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
from textual.binding import Binding
from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

from .shortcuts import (
    CATALOG,
    Scope,
    conflicting_label,
    display_label,
    effective_key,
    is_bare_modifier,
    is_reserved,
    rebuild_shortcuts,
)

TITLE_ART = r""" ____  _                _             _
/ ___|| |__   ___  _ __| |_ ___ _   _| |_ ___
\___ \| '_ \ / _ \| '__| __/ __| | | | __/ __|
 ___) | | | | (_) | |  | || (__| |_| | |_\__ \
|____/|_| |_|\___/|_|   \__\___|\__,_|\__|___/"""

_BY_ID = {action.id: action for action in CATALOG}


def _shortcut_text(action, overrides: dict[str, str]) -> str:
    """The Shortcut cell text: the D-pad shows arrow / alias, others a single key."""
    if not action.editable and action.aliases:
        keys = (action.default_key, *action.aliases)
        return " / ".join(display_label(key) for key in keys)
    return display_label(effective_key(action.id, overrides))


# Surfaces, in display order. Every catalog action falls under exactly one, so the
# table can group its rows under a bold header per surface.
_GROUPS: tuple[tuple[Scope, str], ...] = (
    (Scope.HOME, "Home"),
    (Scope.GLOBAL, "Global"),
    (Scope.REMOTE, "Remote"),
)


def _populate_shortcuts_table(
    table: DataTable, overrides: dict[str, str]
) -> str | None:
    """Fill `table` with catalog rows grouped by surface under bold header rows.

    A blank spacer and a bold header row precede each group. Those rows carry sentinel
    keys (not action ids) so selection ignores them. Reserved rows are dimmed. Returns
    the key of the first selectable action row so the caller can place the cursor there.
    """
    table.add_column("Action", key="action")
    table.add_column("Shortcut", key="shortcut")
    first_action: str | None = None
    for index, (scope, label) in enumerate(_GROUPS):
        actions = [action for action in CATALOG if action.scope is scope]
        if not actions:
            continue
        if index:
            table.add_row("", "", key=f"__spacer__{scope.value}")
        table.add_row(
            Text(label.upper(), style="bold"), "", key=f"__group__{scope.value}"
        )
        for action in actions:
            text = _shortcut_text(action, overrides)
            if action.editable:
                table.add_row(action.label, text, key=action.id)
                first_action = first_action or action.id
            else:
                # Reserved rows are dimmed and cannot be activated for capture.
                table.add_row(
                    Text(action.label, style="dim"),
                    Text(text, style="dim"),
                    key=action.id,
                )
    return first_action


# j/k mirror Down/Up, matching the Remote surface's D-pad aliases, and stay hidden
# from the footer to keep its eight-hint fit. Declared on each screen (Textual only
# merges BINDINGS from DOMNode subclasses, not from the mixin); `rebuild_shortcuts`
# never clears them since they carry no catalog id.
_VIM_ROW_NAV_BINDINGS = [
    Binding("j", "cursor_down", "Down", show=False),
    Binding("k", "cursor_up", "Up", show=False),
]


class _VimRowNavigation:
    """Delegates the j/k Vim actions to the screen's sole DataTable cursor."""

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_cursor_up()


class ShortcutsScreen(_VimRowNavigation, Screen[None]):
    """Lists every action and its shortcut; rebindable rows open the capture modal."""

    BINDINGS = _VIM_ROW_NAV_BINDINGS

    # Go Back (Escape by default) returns to Settings; built on mount like every
    # other non-root screen.
    SHORTCUT_SCOPES = frozenset({Scope.GLOBAL})

    DEFAULT_CSS = """
    ShortcutsScreen { align: center top; }
    #shortcuts { width: 100%; height: 1fr; }
    /* width matches the TITLE_ART banner so it never wraps; Center handles alignment */
    #shortcuts-title { width: 46; text-align: left; margin: 1 0; color: $accent; }
    #shortcuts-table { height: 1fr; width: 100%; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="shortcuts"):
            with Center():
                yield Static(TITLE_ART, id="shortcuts-title")
            yield DataTable(id="shortcuts-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        rebuild_shortcuts(self, self.app.shortcut_overrides, self.SHORTCUT_SCOPES)
        table = self.query_one(DataTable)
        first = _populate_shortcuts_table(table, self.app.shortcut_overrides)
        if first is not None:
            table.move_cursor(row=table.get_row_index(first))
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        action = _BY_ID.get(event.row_key.value)
        if action is None or not action.editable:
            return  # group headers, spacers, and reserved rows are display-only
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
        width: auto; height: auto; padding: 2 4; align-horizontal: center;
        border: thick $primary; background: $surface;
    }
    #capture Label { width: 100%; text-align: center; }
    #capture-prompt { margin-bottom: 1; }
    #capture-buttons { width: auto; height: auto; }
    #capture-buttons Button { width: 12; margin: 0 1; }
    """

    def __init__(self, action_id: str) -> None:
        super().__init__()
        self._action = _BY_ID[action_id]

    def compose(self) -> ComposeResult:
        with Vertical(id="capture"):
            yield Label(f"Press any key for {self._action.label}…", id="capture-prompt")
            # Mouse-only: every keypress is captured as a shortcut, so the buttons
            # must not take focus and swallow it. Cancel/clear are therefore click-only.
            with Horizontal(id="capture-buttons"):
                for button_id, text in (
                    ("capture-del", "Delete"),
                    ("capture-cancel", "Cancel"),
                ):
                    button = Button(text, id=button_id)
                    button.can_focus = False
                    yield button

    def on_key(self, event: events.Key) -> None:
        # Every key is a candidate shortcut, including Escape and Delete. Cancel and
        # clear are the mouse-only buttons. Stop the event so it never reaches the
        # bindings.
        event.stop()
        event.prevent_default()
        # A modifier pressed on its own arrives as its own press event (`left_alt`, …)
        # before any combination — the terminal reports presses only, never releases,
        # so we cannot wait to see if a base key follows. Swallow it silently: Alt+A
        # still assigns via the following `alt+a` event, and a lone modifier simply
        # leaves the modal waiting rather than firing a spurious error mid-combo.
        if is_bare_modifier(event.key):
            return
        self._assign(event.key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "capture-del":
            self._clear()
        else:
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


class ShortcutsViewModal(_VimRowNavigation, ModalScreen[None]):
    """A read-only list of every action and its current shortcut.

    Opened from the command palette so the user can check bindings from any screen.
    Unlike `ShortcutsScreen`, rows cannot be activated and there is no capture — the
    view offers no way to change a shortcut.
    """

    BINDINGS = [Binding("escape", "close", "Close"), *_VIM_ROW_NAV_BINDINGS]

    DEFAULT_CSS = """
    ShortcutsViewModal { align: center middle; background: $background 60%; }
    #shortcuts-view {
        width: 70%; height: 80%; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #shortcuts-view-title {
        width: 100%; text-align: center; text-style: bold; margin-bottom: 1;
    }
    #shortcuts-view-table { width: 100%; height: 1fr; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="shortcuts-view"):
            yield Label("Keyboard Shortcuts", id="shortcuts-view-title")
            yield DataTable(id="shortcuts-view-table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        first = _populate_shortcuts_table(table, self.app.shortcut_overrides)
        if first is not None:
            table.move_cursor(row=table.get_row_index(first))
        table.focus()

    def action_close(self) -> None:
        self.dismiss()


class ShortcutsCommandProvider(Provider):
    """Adds one 'Keyboard Shortcuts' entry to the command palette that opens the
    read-only `ShortcutsViewModal`."""

    _DISPLAY = "Keyboard Shortcuts"
    _HELP = "View current shortcuts (read-only)"

    async def discover(self) -> Hits:
        yield DiscoveryHit(self._DISPLAY, self._show, help=self._HELP)

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        score = matcher.match(self._DISPLAY)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(self._DISPLAY),
                self._show,
                help=self._HELP,
            )

    def _show(self) -> None:
        self.app.push_screen(ShortcutsViewModal())
