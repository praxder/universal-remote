"""Resolve and store per-scope entries for the remote's custom buttons.

Each button's entry — its title and its optional assigned action — lives in a
layered map keyed by scope: a specific device, a device type, or global, mirroring
how `shortcuts` keeps resolution separate from the raw `PreferencesStore`.
Resolution is most-specific-first (device, then type, then global) and treats the
entry as a single unit: the most-specific scope that holds anything for the button
wins whole, so its title and action are always taken together and never split
across scopes. A button with no matching entry falls back to the `Custom N`
default title and no action. This module owns that resolution; the store only holds
the raw dict.
"""

from __future__ import annotations

from enum import Enum


class ButtonScope(Enum):
    """Where a custom-button title applies, listed most specific first."""

    DEVICE = "device"
    TYPE = "type"
    GLOBAL = "global"


def default_title(index: int) -> str:
    """The built-in label for button `index` when no title is configured."""
    return f"Custom {index}"


def resolve_title(
    custom_buttons: dict, index: int, *, device_id: str, platform: str
) -> str:
    """The title shown for button `index`, resolved most-specific-first.

    The button's stored entry resolves as a unit (see `_resolving_entry`); the shown
    title is that entry's title, falling back to `Custom N` when it is blank or the
    button has no matching entry.
    """
    _, entry = _resolving_entry(
        custom_buttons, index, device_id=device_id, platform=platform
    )
    return _entry_title(entry) or default_title(index)


def resolve_scope(
    custom_buttons: dict, index: int, *, device_id: str, platform: str
) -> ButtonScope | None:
    """The scope button `index`'s entry resolves from, or None when it has none.

    The config modal preselects this scope so reopening reflects where the button is
    actually stored.
    """
    scope, _ = _resolving_entry(
        custom_buttons, index, device_id=device_id, platform=platform
    )
    return scope


def resolve_action(
    custom_buttons: dict, index: int, *, device_id: str, platform: str
) -> dict | None:
    """The action assigned to button `index`, or None when it has none.

    Taken from the same entry as the title (see `_resolving_entry`), so a button's
    title and action always come from one scope and are never split.
    """
    _, entry = _resolving_entry(
        custom_buttons, index, device_id=device_id, platform=platform
    )
    action = entry.get("action")
    return action if isinstance(action, dict) else None


def set_title(
    custom_buttons: dict,
    index: int,
    title: str,
    scope: ButtonScope,
    *,
    device_id: str,
    platform: str,
) -> None:
    """Write `title` into button `index`'s entry at `scope`, keeping any action."""
    entry = _entry_slot(custom_buttons, scope, index, device_id, platform)
    entry["title"] = title


def set_action(
    custom_buttons: dict,
    index: int,
    action: dict | None,
    scope: ButtonScope,
    *,
    device_id: str,
    platform: str,
) -> None:
    """Write `action` into button `index`'s entry at `scope`, keeping its title.

    A falsy `action` clears the entry's action, leaving the title in place.
    """
    entry = _entry_slot(custom_buttons, scope, index, device_id, platform)
    if action:
        entry["action"] = action
    else:
        entry.pop("action", None)


def forget_device(custom_buttons: dict, device_id: str) -> None:
    """Drop every device-scoped custom-button entry for `device_id`.

    Device-type and global entries are left intact; a no-op when the device has none.
    """
    custom_buttons.get(ButtonScope.DEVICE.value, {}).pop(device_id, None)


def _scope_key(scope: ButtonScope, device_id: str, platform: str) -> str | None:
    """The map key within a scope: device id, platform, or None for global."""
    if scope is ButtonScope.DEVICE:
        return device_id
    if scope is ButtonScope.TYPE:
        return platform
    return None


def _resolving_entry(
    custom_buttons: dict, index: int, *, device_id: str, platform: str
) -> tuple[ButtonScope | None, dict]:
    """The scope and entry button `index` resolves from, most-specific-first.

    Returns the most-specific scope whose stored entry holds anything for the button
    — a non-blank title or an action — paired with that entry, so the caller reads
    title and action from one place. Returns (None, {}) when no scope has an entry.
    """
    for scope, key in (
        (ButtonScope.DEVICE, device_id),
        (ButtonScope.TYPE, platform),
        (ButtonScope.GLOBAL, None),
    ):
        entry = _stored_entry(custom_buttons, scope, key, index)
        if _entry_title(entry) or entry.get("action"):
            return scope, entry
    return None, {}


def _stored_entry(
    custom_buttons: dict, scope: ButtonScope, key: str | None, index: int
) -> dict:
    """The entry dict stored at `scope`/`key`/`index`, or {} when absent."""
    entries = custom_buttons.get(scope.value, {})
    if key is not None:
        entries = entries.get(key, {})
    entry = entries.get(str(index), {})
    return entry if isinstance(entry, dict) else {}


def _entry_title(entry: dict) -> str:
    """The stripped title held in `entry`, or '' when it has none."""
    title = entry.get("title", "")
    return title.strip() if isinstance(title, str) else ""


def _entry_slot(
    custom_buttons: dict,
    scope: ButtonScope,
    index: int,
    device_id: str,
    platform: str,
) -> dict:
    """Button `index`'s entry dict at `scope`, creating slots as needed."""
    slot = _scope_slot(custom_buttons, scope, device_id, platform)
    return slot.setdefault(str(index), {})


def _scope_slot(
    custom_buttons: dict, scope: ButtonScope, device_id: str, platform: str
) -> dict:
    """The dict of button entries for `scope`/key, created if missing."""
    entries = custom_buttons.setdefault(scope.value, {})
    key = _scope_key(scope, device_id, platform)
    return entries if key is None else entries.setdefault(key, {})
