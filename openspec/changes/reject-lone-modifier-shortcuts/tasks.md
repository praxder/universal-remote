## 1. Reject lone modifiers in `is_bare_modifier`

- [ ] 1.1 Fix the false-green test in `tests/test_shortcuts_catalog.py`: `test_given_a_bare_modifier_when_checked` asserts `is_bare_modifier("shift")` / `is_bare_modifier("ctrl")`, strings the terminal never delivers. Retarget it to the real names — `is_bare_modifier("left_alt")`, `is_bare_modifier("left_shift")`, `is_bare_modifier("iso_level3_shift")` all True — and assert a base key (`"d"`) and a modifier combo (`is_bare_modifier("ctrl+b")`) are both False. It fails (red) because the current set holds only the short names.
- [ ] 1.2 In `src/universal_remote/tui/shortcuts.py`, replace the contents of `_MODIFIER_ONLY` with the modifier key names the protocol delivers on their own: `left_shift`, `left_control`, `left_alt`, `left_super`, `left_hyper`, `left_meta`, the six `right_*` twins, `iso_level3_shift`, `iso_level5_shift`. Add a comment citing `textual._keyboard_protocol.MODIFIER_FUNCTIONAL_KEYS`. Run 1.1 green.

## 2. Drop stale lone-modifier overrides on load

- [ ] 2.1 Add a failing test in `tests/test_shortcuts_catalog.py`: a load-time pruning helper drops overrides whose key is a lone modifier (`{"remote.vol_up": "left_alt"}` → dropped) while keeping ordinary keys and modifier combos (`{"remote.vol_up": "=", "remote.mute": "ctrl+b"}` → unchanged).
- [ ] 2.2 Add the pruning helper to `shortcuts.py` mirroring `without_reserved` — return a new map with any lone-modifier-keyed entry removed. Run 2.1 green.
- [ ] 2.3 Add a failing test for the load path (alongside the existing reserved-key pruning test) in the app/preferences tests: loading overrides that bind an action to a lone modifier drops that override, reverts the action to its default, and persists the cleaned set; a non-modifier override loads unchanged and no rewrite happens when nothing is pruned.
- [ ] 2.4 In `src/universal_remote/tui/app.py` `on_mount`, apply the lone-modifier pruning together with `without_reserved` before `self.shortcut_overrides.update(kept)`, keeping the existing "persist only when the cleaned set differs" behavior. Run 2.3 green.

## 3. Preflight

- [ ] 3.1 Format, lint, and run the full test suite; fix any fallout.
- [ ] 3.2 Confirm the modifier-plus-key path still needs no code — a `ctrl+b`-style combo assigns, conflicts, and displays as before (covered by 1.1's combo assertion; no new production code for it).
