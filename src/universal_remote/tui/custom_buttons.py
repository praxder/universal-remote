"""Resolve and store per-scope titles for the remote's custom buttons.

Titles live in a layered map keyed by scope — a specific device, a device type, or
global — mirroring how `shortcuts` keeps resolution separate from the raw
`PreferencesStore`. Resolution is most-specific-first: device, then type, then
global, then the built-in `Custom N` default. This module owns that resolution; the
store only holds the raw dict.
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

    Device, then device type, then global; a missing or blank title at one scope
    falls through to the next, and an unmatched button falls back to `Custom N`.
    """
    for scope, key in (
        (ButtonScope.DEVICE, device_id),
        (ButtonScope.TYPE, platform),
        (ButtonScope.GLOBAL, None),
    ):
        title = _stored_title(custom_buttons, scope, key, index)
        if title:
            return title
    return default_title(index)


def resolve_scope(
    custom_buttons: dict, index: int, *, device_id: str, platform: str
) -> ButtonScope | None:
    """The scope button `index`'s shown title resolves from, or None when unset.

    Mirrors `resolve_title`'s device → type → global order and its non-blank rule so
    the config modal preselects exactly the scope whose title is displayed.
    """
    for scope, key in (
        (ButtonScope.DEVICE, device_id),
        (ButtonScope.TYPE, platform),
        (ButtonScope.GLOBAL, None),
    ):
        if _stored_title(custom_buttons, scope, key, index):
            return scope
    return None


def set_title(
    custom_buttons: dict,
    index: int,
    title: str,
    scope: ButtonScope,
    *,
    device_id: str,
    platform: str,
) -> None:
    """Write `title` for button `index` at `scope`, creating slots as needed."""
    slot = _scope_slot(custom_buttons, scope, device_id, platform)
    slot[str(index)] = {"title": title}


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


def _stored_title(
    custom_buttons: dict, scope: ButtonScope, key: str | None, index: int
) -> str:
    """The stripped title stored at `scope`/`key`/`index`, or '' when absent."""
    entries = custom_buttons.get(scope.value, {})
    if key is not None:
        entries = entries.get(key, {})
    entry = entries.get(str(index), {})
    return entry.get("title", "").strip() if isinstance(entry, dict) else ""


def _scope_slot(
    custom_buttons: dict, scope: ButtonScope, device_id: str, platform: str
) -> dict:
    """The dict of button entries for `scope`/key, created if missing."""
    entries = custom_buttons.setdefault(scope.value, {})
    key = _scope_key(scope, device_id, platform)
    return entries if key is None else entries.setdefault(key, {})
