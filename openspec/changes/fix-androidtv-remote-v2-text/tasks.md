## 1. Remote v2 IME text path

- [ ] 1.1 Write failing tests for a new `adapters/androidtv_text.py` seam that tracks the device's reported text-field state: it records the counter and the field's current value from an inbound field-state report, and starts with no field focused
- [ ] 1.2 Write failing tests that it builds an edit whose field counter is the latest reported counter and whose cursor span is current-value length plus sent-text length, and that a second send uses the counter from the report that followed the first
- [ ] 1.3 Write a failing test that sending with no field focused raises text-unsupported and sends nothing
- [ ] 1.4 Write a failing test that the seam never emits the field-state report message outbound
- [ ] 1.5 Implement the seam to pass 1.1–1.4, keeping every reference to `androidtvremote2` internals (the protocol object, inbound message observation, and the send path) inside this one module
- [ ] 1.6 Confirm the whole test file passes

## 2. Wire the adapter to the new path

- [ ] 2.1 Update `test_androidtv_adapter.py` so text dispatch expects the new seam and drop its `text_via_adb`, `pair_adb`, and `adb_text_unavailable` tests
- [ ] 2.2 Change `AndroidTvSession._dispatch_text` to send through the seam and delete the ADB routing, `_send_via_adb`, `_resolve_adb_target`, `_send_via_remote_v2`, and the `adb_text_unavailable` attribute
- [ ] 2.3 Install the seam when the session is built in `AndroidTvAdapter.connect`, and drop the `adb_text_factory`, `supports_adb_text`, and `pair_adb` members
- [ ] 2.4 Confirm `test_androidtv_adapter.py` passes

## 3. Remove the opt-in from the device model

- [ ] 3.1 Update `test_device_model.py`: drop the opt-in round-trip test and add one that a stored entry carrying the withdrawn flag loads with it ignored and does not write it back
- [ ] 3.2 Remove `Device.text_via_adb`, relying on `from_dict`'s existing unknown-field tolerance
- [ ] 3.3 Confirm `test_device_model.py` and the device-store tests pass

## 4. Remove the TUI surface

- [ ] 4.1 Delete `tests/test_tui_adb_text.py` and remove the ADB-text fakes and `supports_adb_text` from `tests/fakes.py`
- [ ] 4.2 Update `test_tui_discover.py` to expect no post-add hint for Android TV
- [ ] 4.3 Remove the text-input-mode toggle, its ADB pairing modal, and the opt-in persistence from `tui/devices_screen.py`
- [ ] 4.4 Remove the post-add ADB text hint from `tui/discover_screen.py` and any supporting wiring in `tui/app.py`
- [ ] 4.5 Remove the ADB-text-unavailable status from `tui/remote_screen.py`, leaving the generic text-failure status intact
- [ ] 4.6 Confirm the TUI test files pass

## 5. Narrow the shared ADB text helper

- [ ] 5.1 Reduce `adapters/adb_text.py` to the `input text` command building and escaping that `firetv.py` imports, deleting the `AdbText` class, `adb` binary discovery, the subprocess runner, mDNS target resolution, and ADB pairing
- [ ] 5.2 Narrow `test_adb_text.py` to the escaping and command-building tests
- [ ] 5.3 Confirm the Fire TV adapter is unchanged and `test_firetv_adapter.py` still passes

## 6. Documentation

- [ ] 6.1 Update the README: remove the Android TV ADB text path from the limitations section, revise the text-input support note, and keep the Fire TV ADB requirement as-is
- [ ] 6.2 Refresh any screenshot in `docs/screenshots` that shows the removed text-input-mode toggle

Not an implementation task: the live `androidtv-adapter` spec's Purpose line still reads "with an optional per-device ADB text path". Deltas do not carry a Purpose header and archiving rewrites the live spec, so that line must be edited **after** this change is archived, not during implementation.

## 7. Preflight and verification

- [ ] 7.1 Run `ruff format` and `ruff check`, fixing what they report
- [ ] 7.2 Run the full `pytest` suite and confirm it is green
- [ ] 7.3 Verify on real hardware that text lands in the Google TV launcher search box with the device's developer mode and wireless debugging switched **off**, and that two consecutive sends both land
- [ ] 7.4 Verify that sending text with no field focused surfaces a text-unsupported status rather than appearing to succeed
- [ ] 7.5 Verify Fire TV text still works, confirming the narrowed helper did not disturb it
- [ ] 7.6 Run `openspec validate fix-androidtv-remote-v2-text --strict` and confirm it passes
