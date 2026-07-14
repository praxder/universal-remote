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
    MENU = "menu"
    CH_UP = "ch_up"
    CH_DOWN = "ch_down"
    PLAY = "play"
    PAUSE = "pause"
    PLAY_PAUSE = "play_pause"
    REWIND = "rewind"
    FAST_FORWARD = "fast_forward"
    STOP = "stop"
    NUM_0 = "num_0"
    NUM_1 = "num_1"
    NUM_2 = "num_2"
    NUM_3 = "num_3"
    NUM_4 = "num_4"
    NUM_5 = "num_5"
    NUM_6 = "num_6"
    NUM_7 = "num_7"
    NUM_8 = "num_8"
    NUM_9 = "num_9"
