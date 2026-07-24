"""The rebindable action catalog and the resolver that drives both the screen
key bindings and the Keyboard Shortcuts table.

One catalog is the single source of truth: each entry names an action, its scope,
its default key (possibly empty), and the screen action it triggers. Reserved
entries (`editable=False`) hold keys the override map can never change; the set of
reserved keys the assignment check uses is *derived* from them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from textual.binding import Binding


class Scope(Enum):
    """Where an action can be active — used for scope-aware conflict detection."""

    HOME = "home"  # the entry menu only
    GLOBAL = "global"  # every screen except the root menu
    REMOTE = "remote"  # the remote surface only


@dataclass(frozen=True)
class Action:
    """A catalogued action, either rebindable or reserved.

    `default_key` may be empty (the action starts with no shortcut). `target` is the
    screen action string the binding fires, or None for framework entries that are
    catalogued only for visibility. `aliases` are extra fixed keys a reserved entry
    also answers to (the D-pad's Vim keys). `show` is the default footer visibility
    of the primary key. `footer_label`, when set, is a shorter label the footer shows
    in place of `label` (which stays the full Keyboard Shortcuts table text) so a
    long action name does not overflow the narrow footer.
    """

    id: str
    label: str
    scope: Scope
    default_key: str
    target: str | None
    editable: bool = True
    aliases: tuple[str, ...] = ()
    show: bool = True
    footer_label: str | None = None


def _remote_key(name: str, label: str, key: str, *, show: bool = True) -> Action:
    """A rebindable Remote action that sends the like-named `Key` to the device."""
    return Action(
        id=f"remote.{name}",
        label=label,
        scope=Scope.REMOTE,
        default_key=key,
        target=f"send('{name.upper()}')",
        show=show,
    )


def _custom_activation(index: int) -> Action:
    """A rebindable Remote action that activates custom button `index` like a click.

    Starts with no shortcut and stays out of the footer; it is not a device key, so
    firing it runs the button's own activation (Phase 1: opens the config modal).
    """
    return Action(
        id=f"remote.custom_{index}",
        label=f"Activate Custom Button {index}",
        scope=Scope.REMOTE,
        default_key="",
        target=f"activate_custom({index})",
        show=False,
    )


def _reserved_dpad(name: str, label: str, arrow: str, alias: str) -> Action:
    """A fixed D-pad direction: its arrow key plus a Vim alias, both unchangeable.

    Kept out of the footer — the on-screen D-pad already labels the directions with
    ▲▼◀▶ glyphs, so dropping their hints frees room for the edit-mode hint within the
    80-column footer fit; the table still lists them for discovery.
    """
    return Action(
        id=f"remote.{name}",
        label=label,
        scope=Scope.REMOTE,
        default_key=arrow,
        target=f"send('{name.upper()}')",
        editable=False,
        aliases=(alias,),
        show=False,
    )


CATALOG: list[Action] = [
    # Home — the entry menu.
    Action("home.manage_devices", "Manage Devices", Scope.HOME, "d", "manage_devices"),
    Action("home.use_remote", "Use Remote", Scope.HOME, "r", "use_remote"),
    Action("home.settings", "Settings", Scope.HOME, "s", "settings"),
    Action("home.quit", "Quit", Scope.HOME, "q", "app.quit"),
    # Global — every screen except the root menu.
    Action("global.go_back", "Go Back", Scope.GLOBAL, "escape", "go_back"),
    # Remote — rebindable device actions with default keys.
    _remote_key("ok", "OK", "enter"),
    _remote_key("back", "Back", "backspace"),
    _remote_key("home", "Home", "space"),
    # Remote — rebindable device actions that start with no shortcut.
    _remote_key("vol_up", "Volume Up", "", show=False),
    _remote_key("vol_down", "Volume Down", "", show=False),
    _remote_key("mute", "Mute", "", show=False),
    _remote_key("menu", "Menu", "", show=False),
    _remote_key("ch_up", "Channel Up", "", show=False),
    _remote_key("ch_down", "Channel Down", "", show=False),
    _remote_key("play", "Play", "", show=False),
    _remote_key("pause", "Pause", "", show=False),
    _remote_key("play_pause", "Play/Pause", "", show=False),
    _remote_key("rewind", "Rewind", "", show=False),
    _remote_key("fast_forward", "Fast-forward", "", show=False),
    _remote_key("stop", "Stop", "", show=False),
    # Remote — digit keys, hidden from the footer to avoid clutter.
    *(
        _remote_key(f"num_{digit}", str(digit), str(digit), show=False)
        for digit in range(10)
    ),
    # Remote — text entry.
    Action("remote.text", "Text", Scope.REMOTE, "t", "text_mode"),
    # Remote — activate a custom button (same effect as clicking it); no default key.
    *(_custom_activation(index) for index in range(1, 6)),
    # Remote — toggle edit-mode: press `e` to arm it (the next custom-button
    # activation opens its config instead of running its action) and `e` again to
    # disarm it. Reserved so `e` can't be reassigned. Shown in the footer as the short
    # "Edit" hint (the full "Configure Custom Button" label stays in the table); the
    # D-pad arrow hints are dropped to keep room within the 80-column footer fit.
    Action(
        "remote.edit_mode",
        "Configure Custom Button",
        Scope.REMOTE,
        "e",
        "edit_mode",
        editable=False,
        footer_label="Edit",
    ),
    # Remote — reserved D-pad directions (arrow + Vim alias, both fixed), kept out of
    # the footer; the "UP / K" shortcut makes the direction unambiguous in the table.
    _reserved_dpad("up", "Up", "up", "k"),
    _reserved_dpad("down", "Down", "down", "j"),
    _reserved_dpad("left", "Left", "left", "h"),
    _reserved_dpad("right", "Right", "right", "l"),
    # Reserved framework keys — catalogued for visibility only, never bound by us.
    Action(
        "framework.activate",
        "Activate Control",
        Scope.GLOBAL,
        "enter",
        None,
        editable=False,
        show=False,
    ),
    Action(
        "framework.command_palette",
        "Command Palette",
        Scope.GLOBAL,
        "ctrl+p",
        None,
        editable=False,
        show=False,
    ),
    # Reserved focus-navigation keys — handled natively by Textual, never assignable.
    Action(
        "framework.focus_next",
        "Focus Next",
        Scope.GLOBAL,
        "tab",
        None,
        editable=False,
        show=False,
    ),
    Action(
        "framework.focus_prev",
        "Focus Previous",
        Scope.GLOBAL,
        "shift+tab",
        None,
        editable=False,
        show=False,
    ),
]

_BY_ID: dict[str, Action] = {action.id: action for action in CATALOG}

# The reserved-key set is derived from the fixed entries' keys and aliases, so the
# catalog stays the single source of truth.
RESERVED_KEYS: frozenset[str] = frozenset(
    key
    for action in CATALOG
    if not action.editable
    for key in (action.default_key, *action.aliases)
    if key
)

_NAMED_DISPLAY = {"escape": "ESC", "question_mark": "?", "plus": "+", "minus": "-"}


def effective_key(action_id: str, overrides: dict[str, str]) -> str:
    """The key an action currently answers to: its override, else its default.

    Reserved entries ignore overrides — their keys are fixed.
    """
    action = _BY_ID[action_id]
    if not action.editable:
        return action.default_key
    return overrides.get(action_id, action.default_key)


def is_reserved(key: str) -> bool:
    """Whether a key is held by a fixed catalog entry and cannot be assigned."""
    return key in RESERVED_KEYS


def without_reserved(overrides: dict[str, str]) -> dict[str, str]:
    """`overrides` with any entry whose key is now reserved dropped.

    A key can become reserved after a user already bound it — for example `e` was
    assignable to a device action before it was reserved for edit-mode. Such a stale
    override would shadow the reserved binding, so it is dropped on load and the action
    reverts to its default. Returns a new map; the original is untouched.
    """
    return {aid: key for aid, key in overrides.items() if not is_reserved(key)}


def without_bare_modifiers(overrides: dict[str, str]) -> dict[str, str]:
    """`overrides` with any entry whose key is a lone modifier dropped.

    A broken guard once let a bare modifier be assigned and saved — its key names never
    matched what the terminal delivers, so `is_bare_modifier` always returned False.
    Such an override binds an action to a modifier press, so it is dropped on load and
    the action reverts to its default. Returns a new map; the original is untouched.
    """
    return {aid: key for aid, key in overrides.items() if not is_bare_modifier(key)}


# A lone modifier press is never a valid shortcut. Under the Kitty keyboard protocol
# (Ghostty, Kitty, WezTerm, modern iTerm) a modifier pressed on its own arrives as its
# own functional-key name — `left_alt`, `left_shift`, … — not the short `alt`/`shift`,
# so the capture modal receives these strings verbatim. Kept in sync with
# `textual._keyboard_protocol.MODIFIER_FUNCTIONAL_KEYS` (hardcoded to avoid importing a
# private module).
_MODIFIER_ONLY: frozenset[str] = frozenset(
    {
        "left_shift",
        "left_control",
        "left_alt",
        "left_super",
        "left_hyper",
        "left_meta",
        "right_shift",
        "right_control",
        "right_alt",
        "right_super",
        "right_hyper",
        "right_meta",
        "iso_level3_shift",
        "iso_level5_shift",
    }
)


def is_bare_modifier(key: str) -> bool:
    """Whether `key` is a lone modifier press, which can never be a shortcut."""
    return key in _MODIFIER_ONLY


def conflicting_label(
    action_id: str, key: str, overrides: dict[str, str]
) -> str | None:
    """The label of the action already holding `key` anywhere, else None.

    Shortcuts are globally unique: a key maps to at most one action across the whole
    app, so the check scans every editable action regardless of surface. An action's
    own default is exempt, so a default that coincides with another binding (or a
    reserved key) is never flagged.
    """
    action = _BY_ID[action_id]
    if key == action.default_key:
        return None
    for other in CATALOG:
        if other.id == action_id or not other.editable:
            continue
        if effective_key(other.id, overrides) == key:
            return other.label
    return None


def conflicts(action_id: str, key: str, overrides: dict[str, str]) -> bool:
    """Whether `key` is already used by any other editable action, app-wide."""
    return conflicting_label(action_id, key, overrides) is not None


def display_label(key: str) -> str:
    """A readable, uppercase label for a stored key (`ctrl+p` -> `CTRL-P`)."""
    if not key:
        return ""
    return "-".join(_NAMED_DISPLAY.get(part, part.upper()) for part in key.split("+"))


_CATALOG_IDS = frozenset(action.id for action in CATALOG)


def _bind(bindings, key: str, action: Action, show: bool) -> None:
    # The footer shows `footer_label` when set (a short hint), else the full label.
    description = action.footer_label or action.label
    bindings.key_to_bindings.setdefault(key, []).append(
        Binding(key, action.target, description=description, show=show, id=action.id)
    )


def rebuild_shortcuts(screen, overrides, scopes, *, hide=()) -> None:
    """(Re)build `screen`'s catalog bindings for `scopes` from the override map.

    Any prior catalog bindings on the instance are cleared first, then each
    catalogued action in scope whose effective key is non-empty is bound and the
    footer is refreshed. Reserved entries bind their fixed key and aliases and ignore
    overrides. Ids in `hide` stay out of the footer regardless of their `show` flag.
    """
    bindings = screen._bindings
    hidden = set(hide)
    for key in list(bindings.key_to_bindings):
        kept = [b for b in bindings.key_to_bindings[key] if b.id not in _CATALOG_IDS]
        if kept:
            bindings.key_to_bindings[key] = kept
        else:
            del bindings.key_to_bindings[key]
    for action in CATALOG:
        if action.scope not in scopes or action.target is None:
            continue
        show = action.show and action.id not in hidden
        if action.editable:
            key = effective_key(action.id, overrides)
            if key:
                _bind(bindings, key, action, show)
        else:
            _bind(bindings, action.default_key, action, show)
            for alias in action.aliases:
                _bind(bindings, alias, action, False)
    screen.refresh_bindings()
