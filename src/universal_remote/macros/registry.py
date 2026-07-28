"""Read and write the saved macro registry, keeping resolution out of the store.

The registry is the raw dict persisted under the preferences file's `macros` key:

    {"next_number": 4,
     "items": {"<id>": {"name": …, "steps": [ … ], "step_pause_ms": 500}}}

`next_number` is a monotonic counter, not a count of the items, so deleting a macro
never lets a later one reuse its default name. Reads tolerate a malformed registry —
the same fault tolerance the rest of the preferences file has.
"""

from __future__ import annotations

from .models import Macro


def add(macros: dict, macro: Macro) -> None:
    """Store `macro` under its id, replacing any macro already held there."""
    _items(macros, create_missing=True)[macro.id] = macro.to_dict()


def get(macros: dict, macro_id: str) -> Macro | None:
    """The macro stored under `macro_id`, or None when there is none."""
    body = _items(macros).get(macro_id)
    return Macro.from_dict(macro_id, body) if isinstance(body, dict) else None


def delete(macros: dict, macro_id: str) -> None:
    """Remove the macro stored under `macro_id`; an unknown id is a no-op."""
    _items(macros).pop(macro_id, None)


def list_macros(macros: dict) -> list[Macro]:
    """Every saved macro in saved order (the order they were added)."""
    return [
        Macro.from_dict(macro_id, body)
        for macro_id, body in _items(macros).items()
        if isinstance(body, dict)
    ]


def create(macros: dict, steps: list[dict]) -> Macro:
    """Store a new macro holding `steps`, named from the counter, and return it."""
    number = _next_number(macros)
    macros["next_number"] = number + 1
    macro = Macro(name=f"Macro {number}", steps=steps)
    add(macros, macro)
    return macro


def _next_number(macros: dict) -> int:
    """The counter's current value, defaulting to 1 for a new or malformed registry."""
    number = macros.get("next_number")
    return number if isinstance(number, int) and number > 0 else 1


def _items(macros: dict, *, create_missing: bool = False) -> dict:
    """The registry's item map, or an empty one when missing or malformed."""
    items = macros.get("items")
    if isinstance(items, dict):
        return items
    if not create_missing:
        return {}
    fresh: dict = {}
    macros["items"] = fresh
    return fresh
