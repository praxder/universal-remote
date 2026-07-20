"""A device list with numbered rows, digit shortcuts, and Vim navigation."""

from __future__ import annotations

from textual.binding import Binding
from textual.widgets import OptionList

_DIGIT_BINDINGS = [
    Binding(str(n), f"select_index({n - 1})", show=False) for n in range(1, 10)
]


class DeviceOptionList(OptionList):
    """An OptionList where 1-9 open the Nth device and h/j/k/l move the highlight.

    Saved devices occupy indices 0..device_count-1, so digit N maps to index
    N-1 and reuses the normal select action; the screen's option-selected
    handler then fires unchanged. Digits past device_count are a no-op.
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("l", "cursor_down", "Down", show=False),
        Binding("h", "cursor_up", "Up", show=False),
        *_DIGIT_BINDINGS,
    ]

    device_count = 0

    def action_select_index(self, index: int) -> None:
        if not 0 <= index < self.device_count:
            return
        self.highlighted = index
        self.action_select()
