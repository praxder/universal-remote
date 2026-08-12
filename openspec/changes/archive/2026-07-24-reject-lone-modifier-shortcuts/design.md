## Context

The capture modal already gates assignment with `is_bare_modifier(key)`, but the guard has never fired. This design records the one non-obvious fact the fix depends on — the exact key string a bare modifier produces — so the implementer does not re-derive it and does not reintroduce the same name mismatch.

## The name mismatch (root cause)

`shortcuts.py` defines:

```python
_MODIFIER_ONLY = frozenset({"shift", "ctrl", "alt", "super", "meta", "hyper"})
```

These strings are never delivered. Tracing Textual 8.2.8:

- `textual/_keyboard_protocol.py` maps the Kitty functional codepoints to modifier names: `left_shift`, `left_control`, `left_alt`, `left_super`, `left_hyper`, `left_meta`, the six `right_*` twins, and `iso_level3_shift` / `iso_level5_shift`. That exact set is exported as `MODIFIER_FUNCTIONAL_KEYS`.
- `textual/_xterm_parser.py` (~line 383) builds the event key. For a modifier-only press the resolved `key` is in `MODIFIER_FUNCTIONAL_KEYS`, so the block that would prefix `alt+`/`ctrl+` tokens is **skipped** (`key not in MODIFIER_FUNCTIONAL_KEYS` is false). The emitted `event.key` is therefore the bare name unchanged — e.g. pressing left Alt yields `event.key == "left_alt"`.

So `_assign(event.key)` receives `"left_alt"`, not `"alt"`, and `is_bare_modifier("left_alt")` returns `False`. The guard is dead code and the modifier is assigned.

This only surfaces where the terminal reports modifier presses — the Kitty keyboard protocol, which Textual auto-enables on Ghostty, Kitty, WezTerm, and modern iTerm. On terminals without it, a bare modifier never reaches the app, so the bug is dormable there but the fix is harmless.

## Decision

- Replace `_MODIFIER_ONLY`'s contents with the twelve `left_*`/`right_*` names plus `iso_level3_shift` and `iso_level5_shift`. **Hardcode** them with a comment citing `textual._keyboard_protocol.MODIFIER_FUNCTIONAL_KEYS`, rather than importing that private module — boring and stable, no internal-API coupling. Keeping the old short names in the set as well is harmless, but the delivered long names are the ones that matter.
- Modifier-plus-key combos need **no** code: `ctrl+b`-style keys are not modifier-only, so they flow through `display_label` / `is_reserved` / `conflicting_label` exactly as today.
- Prune persisted lone-modifier overrides at load, mirroring `without_reserved` and its call site in `app.py:on_mount` (drop → revert to default → persist the cleaned set only when something changed).

## Ignore, don't toast (press-only terminals)

The obvious guard — toast "can't assign a modifier alone" on the bare-modifier event — fires at the wrong time. The terminal reports key **presses only, never releases**: Textual enables Kitty flags `disambiguate | report-all-keys | associated-text` (`drivers/linux_driver.py:287`), not `report-event-types`, and `_xterm_parser.py` does `int(modifiers_str)` which would `ValueError` on the `modifiers:event_type` sub-field a release carries. So a modifier that starts a combo (Alt, then A) arrives as its own `left_alt` press event *before* the `alt+a` event, and a toast on that first event spuriously rejects a valid combo mid-keystroke.

There is no release signal to wait for, so "error only if released alone" is not achievable. Decision: the capture modal's `on_key` **silently ignores** a bare-modifier press (swallow the event, keep the modal open, assign nothing). `Alt+A` still assigns via the following event; a lone modifier just leaves the modal waiting. The bare-modifier branch (and its toast) is removed from `_assign` since `on_key` now filters before it. `is_bare_modifier` and the corrected `_MODIFIER_ONLY` set are still the single source of truth for what counts as a lone modifier, used by both `on_key` and the load-time pruning.

## Out of scope

- **`alt+a` vs `å`.** Whether an Alt+letter combo arrives as `alt+a` or as a composed character is a protocol/terminal detail (the parser drops the `alt` token when the press carries text). Same enablement surface as this bug; a UX note, not a code task here.
- **Modifier-only combinations** such as `ctrl+shift` with no base key. Not known to be delivered as a single assignable key; not gold-plating a guard for it. YAGNI.
