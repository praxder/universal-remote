## Why

The keyboard-shortcuts feature already *intends* to reject a lone modifier key as a shortcut: `shortcuts.py` has an `is_bare_modifier` guard and the capture modal calls it before assigning. But the guard's `_MODIFIER_ONLY` set uses short names (`"shift"`, `"ctrl"`, `"alt"`, `"super"`, `"meta"`, `"hyper"`) that the terminal never delivers. A bare modifier press actually arrives as `left_alt`, `left_shift`, `left_control`, `left_super`, `left_hyper`, `left_meta`, the six `right_*` twins, or `iso_level3_shift` / `iso_level5_shift` (confirmed in `textual/_keyboard_protocol.py` and `textual/_xterm_parser.py` — the name reaches `event.key` unchanged for a modifier-only press). None of those match the set, so the guard is dead code: on any terminal that reports modifier key presses (the Kitty keyboard protocol — Ghostty, Kitty, WezTerm, modern iTerm) the user can bind an action to a lone modifier.

The spec has **no requirement** covering this behavior at all — the guard was never specified. This change makes the intended behavior real and pins it down: a modifier is a valid shortcut only when combined with a base key.

## What Changes

- A **lone modifier press** (left/right Shift, Control, Alt, Super/Command, Hyper, Meta, plus ISO level-3/level-5 shift) is **silently ignored** in the capture modal — no shortcut assigned, modal stays open, no error. The terminal reports key presses only (never releases), so a modifier that starts a combo (Alt, then A) arrives as its own event first; toasting on it would spuriously reject a valid `Alt+A`, so the modal swallows the modifier and waits for the base key.
- A **modifier combined with a base key** (for example `ctrl+b`) stays a normal candidate shortcut, assignable subject to the conflict and reserved-key rules. This half already works — no code change — the spec just records it.
- Fix `is_bare_modifier`: `_MODIFIER_ONLY` becomes the key names the keyboard protocol actually delivers for a modifier pressed on its own, with a comment citing `textual._keyboard_protocol.MODIFIER_FUNCTIONAL_KEYS` (hardcoded, no private-module import).
- On load, **drop any persisted override whose key is a lone modifier**, mirroring the existing reserved-key pruning (`without_reserved`): the action reverts to its default and the cleaned set is persisted. This self-heals anyone who already saved a bare-modifier binding while the guard was broken.
- Fix the **false-green test**: `test_given_a_bare_modifier_when_checked` asserts `is_bare_modifier("shift") is True` against strings the terminal never sends; retarget it to the real delivered names and add a modifier-plus-key assertion.

## Capabilities

### Modified Capabilities

- `keyboard-shortcuts`: adds the lone-modifier rejection rule enforced by the capture flow, and drops stale lone-modifier overrides when saved shortcuts are loaded.

## Impact

- `src/universal_remote/tui/shortcuts.py` — correct `_MODIFIER_ONLY` to the modifier key names the protocol delivers; add a load-time pruning helper for lone-modifier overrides mirroring `without_reserved`.
- `src/universal_remote/tui/app.py` — apply lone-modifier pruning alongside `without_reserved` in `on_mount`, persisting the cleaned overrides when anything is dropped.
- `src/universal_remote/tui/shortcuts_screen.py` — the capture modal's `on_key` swallows a bare-modifier press (using the corrected `is_bare_modifier`) instead of assigning; the now-dead bare-modifier toast branch is removed from `_assign`.
- `tests/test_shortcuts_catalog.py` — fix the false-green bare-modifier test; add a modifier-plus-key-allowed assertion and a lone-modifier pruning test.
- No new dependencies; no device-adapter or `Key` vocabulary changes; no user-visible change to combos, which already worked.
