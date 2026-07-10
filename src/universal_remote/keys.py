"""The platform-agnostic remote key vocabulary."""

from __future__ import annotations

from enum import Enum


class Key(Enum):
    """A generic remote key, independent of any TV brand."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    OK = "ok"
    BACK = "back"
    HOME = "home"
    VOL_UP = "vol_up"
    VOL_DOWN = "vol_down"
    MUTE = "mute"
    POWER = "power"
