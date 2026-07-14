## 0. Layout groundwork

- [x] 0.1 Add a failing test in `tests/test_tui_remote_surface.py` that renders the remote against a full-capability adapter at `app.run_test(size=(80, 24))` and asserts the remote does not scroll (its content height is within the terminal). Seed it so it exercises the *full* button set as each phase adds buttons — re-assert in task 4.3 once all buttons exist.
- [x] 0.2 Add CSS scoped to `RemoteScreen` (in `app.py`'s `CSS` block or a dedicated stylesheet) making remote buttons one row tall and borderless (`RemoteScreen Button { height: 1; border: none; min-width: 0; }`), plus a `#numpad` grid rule for the 3×4 pad. Keep a clearly distinct disabled look (dimmed) since the removed border weakens Textual's default disabled affordance.
- [x] 0.3 Run 0.1 green; confirm the existing remote (current 10 buttons) still renders and its tests pass under the compact style. Visually confirm a disabled button (e.g. force one unsupported) still reads as disabled under the borderless style. _(automated tests green; disabled dimming now asserted programmatically — `text-opacity: 0.4` on a disabled vs `1.0` on an enabled button — so the cue is proven to apply. Only the aesthetic "is 40% distinct enough to the eye" and the `#remote` height:auto centered layout remain a manual glance.)_

## 1. Menu + channel keys

- [x] 1.1 Add failing tests: `test_keys.py` expects `MENU`, `CH_UP`, `CH_DOWN` in the vocabulary; `test_tui_remote_surface.py` clicks `#key-ch_up`/`#key-ch_down`/`#key-menu` and asserts the mapped key is sent (FakeAdapter supports all keys).
- [x] 1.2 Add failing per-adapter tests: LG maps `CH_UP→"CHANNELUP"`, `CH_DOWN→"CHANNELDOWN"`, `MENU→"MENU"` (`test_lg_adapter.py`); Samsung maps `KEY_CHUP`/`KEY_CHDOWN`/`KEY_MENU` (`test_samsung_adapter.py`); Apple TV maps `CH_UP→channel_up`, `CH_DOWN→channel_down` and does **not** declare `MENU` (`test_appletv_adapter.py`).
- [x] 1.3 Add `MENU`, `CH_UP`, `CH_DOWN` to the `Key` enum.
- [x] 1.4 Extend each adapter's mapping dict: LG + Samsung get all three; Apple TV gets `channel_up`/`channel_down` only (no menu). Capabilities recompute from the dict automatically.
- [x] 1.5 Render the buttons in `remote_screen.py`: add `MENU` to the top row (`☰ Menu`, before Home/Back); add a channel row with `Ch +` / `Ch −` beside the volume group. Keep them non-focusable, mouse-only.
- [x] 1.6 Update `test_keys.py`'s expected set and run tasks 1.1–1.2 green; confirm the capability-disabling test still passes (Apple TV Menu button disabled).

## 2. Media transport keys

- [x] 2.1 Add failing tests: vocabulary gains `PLAY`, `PAUSE`, `PLAY_PAUSE`, `REWIND`, `FAST_FORWARD`, `STOP`; clicking each new button sends the mapped key on a full-capability adapter.
- [x] 2.2 Add failing per-adapter tests: Apple TV declares all six (`play`, `pause`, `play_pause`, `skip_backward`, `skip_forward`, `stop`); LG declares five (no `PLAY_PAUSE`) mapping to `PLAY`/`PAUSE`/`REWIND`/`FASTFORWARD`/`STOP`; Samsung declares five (no `PLAY_PAUSE`) mapping to `KEY_PLAY`/`KEY_PAUSE`/`KEY_REWIND`/`KEY_FF`/`KEY_STOP`.
- [x] 2.3 Add the six keys to the `Key` enum.
- [x] 2.4 Extend the adapter dicts per 2.2 (Apple TV all six; LG/Samsung the five, no combined toggle).
- [x] 2.5 Render a media-transport row: `◀◀` Rewind, `▶` Play, `❚❚` Pause, `▶❚❚` Play/Pause, `■` Stop, `▶▶` Fast-forward. Scan icons for rewind/fast-forward per the design decision.
- [x] 2.6 Update `test_keys.py` and run tasks 2.1–2.2 green; confirm `PLAY_PAUSE` renders disabled on LG/Samsung.

## 3. Number pad

- [x] 3.1 Add failing tests: vocabulary gains `NUM_0`–`NUM_9`; clicking `#key-num_5` (etc.) sends the mapped key; pressing digit keys `0`–`9` sends `NUM_0`–`NUM_9`; digits typed into the focused text field fill the buffer and send nothing; on an adapter without number keys, pressing a digit sends nothing and shows no error message.
- [x] 3.2 Add failing per-adapter tests: LG maps `NUM_0→"0"`…`NUM_9→"9"`; Samsung maps `NUM_0→"KEY_0"`…`NUM_9→"KEY_9"`; Apple TV declares **no** number keys.
- [x] 3.3 Add `NUM_0`–`NUM_9` to the `Key` enum.
- [x] 3.4 Extend LG and Samsung dicts with the digit codes; leave Apple TV without any.
- [x] 3.5 Render the 3×4 number pad (`1 2 3` / `4 5 6` / `7 8 9` / `0`) inside a `#numpad` container; add `Binding("0", "send('NUM_0')")`…`Binding("9", "send('NUM_9')")` (`show=False`) to `RemoteScreen.BINDINGS`.
- [x] 3.6 Capability-gate the keyboard send: in `action_send`, no-op silently when `not self._capabilities.supports(key)`, so a bound digit on a numbers-less adapter (Apple TV) behaves like its disabled button — nothing sent, no message.
- [x] 3.7 Update `test_keys.py` and run tasks 3.1–3.2 green; confirm the whole pad renders disabled on Apple TV and that pressing a digit there is a silent no-op.

## 4. Specs, docs, and preflight

- [x] 4.1 Confirm the change's spec deltas (`specs/remote-control-core/spec.md`, `specs/tui-remote/spec.md`) match what was built; adjust wording if the implementation diverged. _(Reviewed: vocabulary, surface button set, digit bindings, scan icons, and the 80×24 fit all match the spec deltas — no spec wording changes needed. The design's "compact buttons" decision gained an "As built" note: `DEFAULT_CSS` + `height: auto` so overflow surfaces as a testable screen scroll, and the `!important` disabled dim.)_
- [x] 4.2 Update `README.md` if it documents the remote's buttons or key bindings (note the digit-key shortcuts).
- [x] 4.3 Run the formatter, linter, and full test suite; fix any failures. Confirm `test_tui_remote_surface.py::..._every_key_has_a_button` is green (all 29 keys have buttons). _(183 passed, ruff clean, `every_key_has_a_button` green, `Key` has 29 members.)_
- [ ] 4.4 **Hardware verification** — on a real Samsung TV, confirm `KEY_PLAY`, `KEY_PAUSE`, `KEY_STOP`, `KEY_REWIND`, `KEY_FF` are accepted (these codes were not found in the vendored library). Correct any that differ; the fix is a single dict entry. _(BLOCKED: requires a physical Samsung TV — cannot verify in this environment. Codes are wired per design and flagged ⚠.)_
- [ ] 4.5 Manually exercise the app against each available device: buttons enable/disable per adapter (Apple TV shows Menu + number pad disabled; LG/Samsung show `PLAY_PAUSE` disabled), and each enabled button drives the device. _(BLOCKED: requires physical devices — cannot verify in this environment. Per-adapter enable/disable is covered by automated tests; live button-drives-device is manual.)_
