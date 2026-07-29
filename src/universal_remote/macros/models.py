"""The macro model: a named, ordered list of steps with a stable identity.

A step is a small dict, persisted as-is inside the macro registry, in one of four
shapes: a device `key`, a `text` send, a snapshotted custom-button `action`, or an
explicit `pause`. Dicts rather than classes because they go straight to JSON and
mirror how a custom button's action is already stored.

A macro's `id` is stable and independent of its name and position, so an invoker
(today a custom button) refers to the macro rather than holding a copy of it. The
registry keys each macro by that id, so `to_dict` holds only the name, the steps, and
the macro's own pacing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# The gap playback leaves between one step and the next when the user has not changed
# it. Keys sent back to back outrun most TV UIs, so replaying with no gap at all lands
# presses the device never redraws for; half a second covers a typical menu transition.
DEFAULT_STEP_PAUSE_MS = 500


def key_step(key_name: str) -> dict:
    """A step that sends one device key."""
    return {"type": "key", "key": key_name}


def text_step(text: str) -> dict:
    """A step that sends one string of text."""
    return {"type": "text", "text": text}


def pause_step(ms: int) -> dict:
    """A step that waits `ms` milliseconds before the next step runs."""
    return {"type": "pause", "ms": ms}


def action_step(action: dict) -> dict:
    """A step holding a frozen copy of a custom button's resolved action.

    A copy, not a reference to the button: the step keeps doing what it did when
    recorded even if that button is later reconfigured or the macro is replayed on a
    device where the button resolves to something else.
    """
    return {"type": "action", "action": dict(action)}


def step_description(step: dict) -> str:
    """A human-readable line naming what `step` does.

    Read by the detail modal's step list and by the playback modal's progress and
    abort messages, so what the user sees named is what runs.
    """
    kind = step.get("type")
    if kind == "key":
        return f"Key: {step.get('key')}"
    if kind == "text":
        return f'Text: "{step.get("text")}"'
    if kind == "pause":
        return f"Pause: {step.get('ms')}ms"
    if kind == "action":
        return _action_description(step.get("action") or {})
    return f"Unknown step: {kind}"


def _action_description(action: dict) -> str:
    """The captured action's own catalog label, or its raw type when unknown.

    The catalog import is deferred: `tui.actions` reaches back into this module for
    macro playback, so importing it at module scope would be a cycle.
    """
    from ..tui.actions import action_type

    entry = action_type(action.get("type"))
    return entry.label if entry else f"Action: {action.get('type')}"


@dataclass
class Macro:
    """One saved macro: its name, its ordered steps, its stable id, and its pacing.

    `step_pause_ms` is this macro's own gap between steps — the right value depends on
    what the macro drives, so it belongs to the macro rather than to the application.
    """

    name: str = ""
    steps: list[dict] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    step_pause_ms: int = DEFAULT_STEP_PAUSE_MS

    def to_dict(self) -> dict[str, Any]:
        # A copy of the step list, so a draft the caller keeps editing after saving
        # cannot reach back into the stored registry.
        return {
            "name": self.name,
            "steps": list(self.steps),
            "step_pause_ms": self.step_pause_ms,
        }

    @classmethod
    def from_dict(cls, macro_id: str, data: dict[str, Any]) -> "Macro":
        """The macro stored under `macro_id`, tolerating a malformed body.

        A missing or wrongly-typed name or step list loads as empty rather than
        raising, matching how the rest of the preferences file is read.
        """
        name = data.get("name")
        steps = data.get("steps")
        return cls(
            name=name if isinstance(name, str) else "",
            steps=[step for step in steps if isinstance(step, dict)]
            if isinstance(steps, list)
            else [],
            id=macro_id,
            step_pause_ms=_step_pause(data.get("step_pause_ms")),
        )


def _step_pause(value: Any) -> int:
    """`value` as a between-step pause, or the default when it is not one.

    A macro stored before the field existed, and a hand-edited negative or fractional
    value, both read as the default: pacing is not worth raising over, and reading a
    malformed value as no gap at all would replay too fast to work.
    """
    if isinstance(value, int) and value >= 0:
        return value
    return DEFAULT_STEP_PAUSE_MS


def move_up(steps: list[dict], index: int) -> int:
    """Swap the step at `index` with the one above it; a no-op at the top.

    Returns the index the step now sits at, so a caller can keep it selected.
    """
    if index <= 0 or index >= len(steps):
        return index
    steps[index - 1], steps[index] = steps[index], steps[index - 1]
    return index - 1


def move_down(steps: list[dict], index: int) -> int:
    """Swap the step at `index` with the one below it; a no-op at the bottom."""
    if index < 0 or index >= len(steps) - 1:
        return index
    steps[index], steps[index + 1] = steps[index + 1], steps[index]
    return index + 1


def delete_step(steps: list[dict], index: int) -> None:
    """Remove the step at `index`; out-of-range is a no-op."""
    if 0 <= index < len(steps):
        del steps[index]


def insert_after(steps: list[dict], index: int, step: dict) -> int:
    """Insert `step` directly after `index`, returning where it landed.

    An `index` of -1 means nothing is selected (an empty draft), so the step goes
    first.
    """
    position = index + 1
    steps.insert(position, step)
    return position
