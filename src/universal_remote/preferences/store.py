"""XDG-aware JSON store for app-level user preferences (v1: the selected theme)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def default_settings_path() -> Path:
    """`$XDG_CONFIG_HOME/universal-remote/settings.json`, falling back to ~/.config."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "universal-remote" / "settings.json"


@dataclass(frozen=True)
class Preferences:
    """App preferences: theme, custom shortcuts, custom-button titles, and macros."""

    theme: str | None = None
    # Action id -> key; only shortcuts that differ from a catalog default are stored.
    shortcuts: dict[str, str] = field(default_factory=dict)
    # Layered custom-button titles keyed by scope (device / type / global); empty when
    # the user has configured none. Resolution lives in `tui.custom_buttons`.
    custom_buttons: dict = field(default_factory=dict)
    # The saved macro registry: `next_number` (the default-name counter) plus `items`
    # keyed by macro id. Empty when the user has recorded none; the registry
    # operations live in `macros.registry`.
    macros: dict = field(default_factory=dict)
    # True once the user has asked not to see the pre-recording hint again. Stored as
    # suppression rather than as "show" so a missing or malformed value defaults to
    # showing it — a fresh install must meet the hint.
    hide_recording_hint: bool = False


class PreferencesStore:
    """Reads and writes preferences as indented JSON; reads never raise."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_settings_path()

    def load(self) -> Preferences:
        """The saved preferences, or defaults when the file is missing or unreadable."""
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, ValueError):
            return Preferences()
        if not isinstance(raw, dict):
            return Preferences()
        shortcuts = raw.get("shortcuts")
        if not isinstance(shortcuts, dict):
            shortcuts = {}
        custom_buttons = raw.get("custom_buttons")
        if not isinstance(custom_buttons, dict):
            custom_buttons = {}
        macros = raw.get("macros")
        if not isinstance(macros, dict):
            macros = {}
        return Preferences(
            theme=raw.get("theme"),
            shortcuts=shortcuts,
            custom_buttons=custom_buttons,
            macros=macros,
            # `is True` is the type guard: anything else — missing, a string, a number —
            # loads as not suppressed rather than hiding a hint the user never dismissed.
            hide_recording_hint=raw.get("hide_recording_hint") is True,
        )

    def save(self, preferences: Preferences) -> None:
        """Best-effort write; an unwritable config dir is ignored, not raised.

        Persisting a cosmetic preference must never crash the app or interrupt a
        session — symmetric with the fault-tolerant `load` and matching how the
        error log is written best-effort.
        """
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(
                    {
                        "theme": preferences.theme,
                        "shortcuts": preferences.shortcuts,
                        "custom_buttons": preferences.custom_buttons,
                        "macros": preferences.macros,
                        "hide_recording_hint": preferences.hide_recording_hint,
                    },
                    indent=2,
                )
            )
        except OSError:
            pass
