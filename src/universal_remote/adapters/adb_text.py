"""Builds the device-side `input text` command Fire TV types with.

Fire TV has no protocol-level text path, so its adapter shells `input text` over its
existing ADB connection (see `firetv.py`). That command runs in a device-side shell,
so the text has to survive both the shell's quoting and `input text`'s own `%s`
handling — which is all this module does.
"""

from __future__ import annotations

# Characters that carry meaning to the device-side shell `input text` runs in, so a
# literal one must be backslash-escaped. Space is handled separately (it becomes
# `%s`). Unicode is out of scope — this covers the common ASCII cases (see design).
_SHELL_SPECIAL = frozenset("'\"\\`$&|;<>()*?~#!%")


def _escape_char(char: str) -> str:
    if char == " ":
        return "%s"
    if char in _SHELL_SPECIAL:
        return "\\" + char
    return char


def escape_for_input_text(text: str) -> str:
    """Escape `text` so one `input text` argument reproduces it on the device."""
    return "".join(_escape_char(char) for char in text)


def _split_at_percent_s(text: str) -> list[str]:
    """Split `text` after every `%` that is immediately followed by `s`.

    Android's `input text` collapses the two-char sequence `%s` to a space, so a
    literal `%s` in the text would be corrupted. Cutting between the `%` and the `s`
    puts them in separate segments that never form `%s` within one invocation.
    """
    segments: list[str] = []
    start = 0
    for index in range(len(text) - 1):
        if text[index] == "%" and text[index + 1] == "s":
            segments.append(text[start : index + 1])
            start = index + 1
    segments.append(text[start:])
    return segments


def build_input_text_command(text: str) -> str:
    """A device-side shell command that types `text` via `input text`.

    Text with no literal `%s` stays a single `input text` call. When `text` contains
    a literal `%s`, it is split there and chained as separate `input text` calls: the
    segments concatenate on the device, but the `%s`-to-space collapse only applies
    within one invocation, so the literal survives (see `_split_at_percent_s`).
    """
    return "; ".join(
        f"input text {escape_for_input_text(segment)}"
        for segment in _split_at_percent_s(text)
    )
