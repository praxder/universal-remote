"""XDG-aware JSON store for app-level user preferences (v1: the selected theme)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def default_settings_path() -> Path:
    """`$XDG_CONFIG_HOME/universal-remote/settings.json`, falling back to ~/.config."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "universal-remote" / "settings.json"


@dataclass(frozen=True)
class Preferences:
    """App-level user preferences; v1 holds only the selected theme."""

    theme: str | None = None


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
        return Preferences(theme=raw.get("theme"))

    def save(self, preferences: Preferences) -> None:
        """Best-effort write; an unwritable config dir is ignored, not raised.

        Persisting a cosmetic preference must never crash the app or interrupt a
        session — symmetric with the fault-tolerant `load` and matching how the
        error log is written best-effort.
        """
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps({"theme": preferences.theme}, indent=2))
        except OSError:
            pass
