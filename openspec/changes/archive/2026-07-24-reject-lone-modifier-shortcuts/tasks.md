## 1. Reject lone modifiers in `is_bare_modifier`

- [x] 1.1 Fix the false-green test in `tests/test_shortcuts_catalog.py`: `test_given_a_bare_modifier_when_checked` asserts `is_bare_modifier("shift")` / `is_bare_modifier("ctrl")`, strings the terminal never delivers. Retarget it to the real names — `is_bare_modifier("left_alt")`, `is_bare_modifier("left_shift")`, `is_bare_modifier("iso_level3_shift")` all True — and assert a base key (`"d"`) and a modifier combo (`is_bare_modifier("ctrl+b")`) are both False. It fails (red) because the current set holds only the short names.
- [x] 1.2 In `src/universal_remote/tui/shortcuts.py`, replace the contents of `_MODIFIER_ONLY` with the modifier key names the protocol delivers on their own: `left_shift`, `left_control`, `left_alt`, `left_super`, `left_hyper`, `left_meta`, the six `right_*` twins, `iso_level3_shift`, `iso_level5_shift`. Add a comment citing `textual._keyboard_protocol.MODIFIER_FUNCTIONAL_KEYS`. Run 1.1 green.

## 2. Drop stale lone-modifier overrides on load

- [x] 2.1 Add a failing test in `tests/test_shortcuts_catalog.py`: a load-time pruning helper drops overrides whose key is a lone modifier (`{"remote.vol_up": "left_alt"}` → dropped) while keeping ordinary keys and modifier combos (`{"remote.vol_up": "=", "remote.mute": "ctrl+b"}` → unchanged).
- [x] 2.2 Add the pruning helper to `shortcuts.py` mirroring `without_reserved` — return a new map with any lone-modifier-keyed entry removed. Run 2.1 green.
- [x] 2.3 Add a failing test for the load path (alongside the existing reserved-key pruning test) in the app/preferences tests: loading overrides that bind an action to a lone modifier drops that override, reverts the action to its default, and persists the cleaned set; a non-modifier override loads unchanged and no rewrite happens when nothing is pruned.
- [x] 2.4 In `src/universal_remote/tui/app.py` `on_mount`, apply the lone-modifier pruning together with `without_reserved` before `self.shortcut_overrides.update(kept)`, keeping the existing "persist only when the cleaned set differs" behavior. Run 2.3 green.

## 3. Preflight

- [x] 3.1 Format, lint, and run the full test suite; fix any fallout. `ruff format`/`ruff check` clean; 612 passed. One failure — `test_tui_menu.py::...use_remote_is_clicked...` — is **pre-existing and unrelated** (fails identically on the clean baseline with these changes stashed; "Use Remote" clicked with an empty device store never reaches `UseRemoteScreen`). Left untouched: out of scope for lone-modifier shortcuts.
- [x] 3.2 Confirm the modifier-plus-key path still needs no code — a `ctrl+b`-style combo assigns, conflicts, and displays as before (covered by 1.1's combo assertion; no new production code for it).
- [x] 3.3 End-to-end coverage for the spec's two capture scenarios (the `_assign` wiring was never exercised while the guard was dead): in `tests/test_tui_shortcuts.py`, `pilot.press("left_alt")` in the capture modal leaves the action unchanged; `pilot.press("ctrl+b")` is accepted and the row shows `CTRL-B`. Proves a modifier-only event actually reaches the modal handler.

## 4. Ignore lone modifiers instead of toasting (press-only terminals)

- [x] 4.1 Update the e2e test `test_given_a_lone_modifier_when_pressed_then_it_is_ignored`: `pilot.press("left_alt")` in the capture modal assigns nothing, leaves the modal open (`isinstance(app.screen, CaptureModal)`), and fires **no** error notification. Fails (red) because the modal currently toasts on the modifier's press event, which would also spuriously interrupt a real Alt+A.
- [x] 4.2 In `shortcuts_screen.py`, make `CaptureModal.on_key` return early (swallowing the event) when `is_bare_modifier(event.key)`, before `_assign`; remove the now-dead bare-modifier toast branch from `_assign`. Run 4.1 green. (Rationale: the terminal reports presses only — no release signal — so a deferred/release-based error is infeasible; ignoring is the robust behavior. See design.md.)
