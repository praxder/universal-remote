## 1. Remote v2 IME text path

- [x] 1.1 Write failing tests for a new `adapters/androidtv_text.py` seam that tracks the device's reported text-field state: it records the counter and the field's current value from an inbound field-state report, and starts with no field focused
- [x] 1.2 Write failing tests that it builds an edit whose field counter is the latest reported counter and whose cursor span is current-value length plus sent-text length, and that a second send uses the counter from the report that followed the first
- [x] 1.3 Write a failing test that sending with no field focused raises text-unsupported and sends nothing
- [x] 1.4 Write a failing test that the seam never emits the field-state report message outbound
- [x] 1.5 Implement the seam to pass 1.1–1.4, keeping every reference to `androidtvremote2` internals (the protocol object, inbound message observation, and the send path) inside this one module
- [x] 1.6 Confirm the whole test file passes

## 2. Wire the adapter to the new path

- [x] 2.1 Update `test_androidtv_adapter.py` so text dispatch expects the new seam and drop its `text_via_adb`, `pair_adb`, and `adb_text_unavailable` tests
- [x] 2.2 Change `AndroidTvSession._dispatch_text` to send through the seam and delete the ADB routing, `_send_via_adb`, `_resolve_adb_target`, `_send_via_remote_v2`, and the `adb_text_unavailable` attribute
- [x] 2.3 Install the seam when the session is built in `AndroidTvAdapter.connect`, and drop the `adb_text_factory`, `supports_adb_text`, and `pair_adb` members
- [x] 2.4 Confirm `test_androidtv_adapter.py` passes

## 3. Remove the opt-in from the device model

- [x] 3.1 Update `test_device_model.py`: drop the opt-in round-trip test and add one that a stored entry carrying the withdrawn flag loads with it ignored and does not write it back
- [x] 3.2 Remove `Device.text_via_adb`, relying on `from_dict`'s existing unknown-field tolerance
- [x] 3.3 Confirm `test_device_model.py` and the device-store tests pass

## 4. Remove the TUI surface

- [x] 4.1 Delete `tests/test_tui_adb_text.py` and remove the ADB-text fakes and `supports_adb_text` from `tests/fakes.py`
- [x] 4.2 Update `test_tui_discover.py` to expect no post-add hint for Android TV
- [x] 4.3 Remove the text-input-mode toggle, its ADB pairing modal, and the opt-in persistence from `tui/devices_screen.py`
- [x] 4.4 Remove the post-add ADB text hint from `tui/discover_screen.py` and any supporting wiring in `tui/app.py`
- [x] 4.5 Remove the ADB-text-unavailable status from `tui/remote_screen.py`, leaving the generic text-failure status intact
- [x] 4.6 Confirm the TUI test files pass

## 5. Narrow the shared ADB text helper

- [x] 5.1 Reduce `adapters/adb_text.py` to the `input text` command building and escaping that `firetv.py` imports, deleting the `AdbText` class, `adb` binary discovery, the subprocess runner, mDNS target resolution, and ADB pairing
- [x] 5.2 Narrow `test_adb_text.py` to the escaping and command-building tests
- [x] 5.3 Confirm the Fire TV adapter is unchanged and `test_firetv_adapter.py` still passes

## 6. Documentation

- [x] 6.1 Update the README: remove the Android TV ADB text path from the limitations section, revise the text-input support note, and keep the Fire TV ADB requirement as-is
- [x] 6.2 Refresh any screenshot in `docs/screenshots` that shows the removed text-input-mode toggle

Not an implementation task: the live `androidtv-adapter` spec's Purpose line still reads "with an optional per-device ADB text path". Deltas do not carry a Purpose header and archiving rewrites the live spec, so that line must be edited **after** this change is archived, not during implementation.

## 7. Preflight and verification

- [x] 7.1 Run `ruff format` and `ruff check`, fixing what they report
- [x] 7.2 Run the full `pytest` suite and confirm it is green
- [x] 7.3 Verify on real hardware that text lands in the Google TV launcher search box with the device's developer mode and wireless debugging switched **off**, and that two consecutive sends both land
- [x] 7.4 Verify that sending text with no field focused surfaces a text-unsupported status rather than appearing to succeed
- [x] 7.5 Verify Fire TV text still works, confirming the narrowed helper did not disturb it
- [x] 7.6 Run `openspec validate fix-androidtv-remote-v2-text --strict` and confirm it passes

## 8. IME counter correction (found during 7.3 verification)

Hardware verification found text landing on the launcher search box but silently dropped in an app's own text field. Isolated trials showed the edit's `ime_counter` must be the focused editor's `app_info.counter`, not the inbound batch edit's counter — which is a fixed greeting that only coincidentally matches on the launcher.

- [x] 8.1 Write failing tests that the edit's IME counter is the reported editor counter, that a newer report replaces it, and that the library's tracked value is used when no editor counter has been reported
- [x] 8.2 Read `app_info.counter` off the key-inject report in the seam and build the edit from it
- [x] 8.3 Correct the design's field table, its app-text-field non-goal, and the spec delta, which all recorded the inbound counter as correct
- [x] 8.4 Verify on real hardware that text lands in an app's own text field, and that consecutive sends append
- [x] 8.5 Re-verify the launcher search box for regression

## 9. Confirm sends with the device's echo (found during 7.4 verification)

Verifying 7.4 exposed a second silent-success path: the device never reports a field losing focus, so text sent after the user navigates away carried a stale counter, was discarded without response, and was reported as delivered. The device's field-state report after an accepted edit is used as an acknowledgement instead.

- [x] 9.1 Write failing tests that a send the device does not report raises text-unsupported, that the edit was still put on the wire, and that a reported send succeeds
- [x] 9.2 Make the seam's send await the device's report, with an injectable timeout so tests do not sit out the real one
- [x] 9.3 Add the confirmation requirement and its scenario to the spec delta, and the decision and its cost to the design
- [x] 9.4 Verify on hardware that a send lands while a field is focused and reports text-unsupported after navigating away from it
