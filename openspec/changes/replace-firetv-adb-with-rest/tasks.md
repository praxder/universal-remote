## 1. HTTP seam

- [x] 1.1 Add a `RemoteApi` client module for the Fire TV REST API, taking host plus an injectable request function so tests need no network
- [x] 1.2 Write tests covering request construction: `X-Api-Key`, `User-Agent`, `X-Client-Token` when a token is held, and self-signed TLS accepted for this host only
- [x] 1.3 Implement request construction until 1.2 passes

## 2. Wake

- [x] 2.1 Write tests for the DIAL wake: posts to `http://<ip>:8009/apps/FireTVRemote`, polls the control port, and returns once it accepts
- [x] 2.2 Write a test that a wake against an already-running service succeeds
- [x] 2.3 Write a test that a control port never accepting within the timeout raises a connection failure
- [x] 2.4 Implement wake until 2.1–2.3 pass

## 3. Pairing

- [x] 3.1 Write tests for `pair`: wakes, posts `pin/display`, requests the PIN through the prompt seam, posts `pin/verify`, returns the token from the `description` field
- [x] 3.2 Write a test that a rejected PIN raises a pairing failure and returns no credential
- [x] 3.3 Write a test that pairing without a prompt raises a pairing failure rather than supplying a value
- [x] 3.4 Implement `pair` until 3.1–3.3 pass

## 4. Key dispatch

- [x] 4.1 Replace `FIRETV_KEYS` and `EVDEV_KEYS` with a single map from generic key to REST action, using the verified nav vocabulary
- [x] 4.2 Map `PLAY` and `PAUSE` to `/v1/media`, and `FAST_FORWARD`/`REWIND` to `dpad_right`/`dpad_left`
- [x] 4.3 Write tests that keys dispatch with an **empty** request body, never `keyActionType`
- [x] 4.4 Write a test that a 400 from the device surfaces as a failure, not a success
- [x] 4.5 Write a test that an undeclared key is rejected without sending a substitute action
- [x] 4.6 Implement `_dispatch_key` until 4.3–4.5 pass

## 5. Text and digits

- [x] 5.1 Write a test that a text send reads `GET /v1/FireTV/keyboard` **before** posting, and that a `state` of `hidden` raises `TextUnsupportedError` without any POST being issued
- [x] 5.2 Write a test that a `state` of `text` then sets the field via `POST /v1/FireTV/keyboard` with no caller escaping
- [x] 5.3 Write a test that non-ASCII text is transmitted unchanged
- [x] 5.4 Write a test that a digit key reads the current field and writes back the concatenation, since the endpoint replaces rather than appends
- [x] 5.5 Implement `_dispatch_text` and digit dispatch until 5.1–5.4 pass

## 6. Capabilities and session

- [x] 6.1 Update `_CAPABILITIES` to drop `VOL_UP`, `VOL_DOWN`, `MUTE`, `PLAY_PAUSE`, and `STOP`, keeping `text=True`
- [x] 6.2 Write a test asserting the dropped keys are absent and the retained set is present
- [x] 6.3 Rewrite `FireTvSession` to hold the token and API client instead of an ADB device, with `_release` closing only what it owns
- [x] 6.4 Write a test that a connection failure mid-session triggers one re-wake and retry before surfacing an error
- [x] 6.5 Implement the re-wake-and-retry behaviour until 6.4 passes

## 7. Reachability and connect

- [x] 7.1 Change `reachability_port` from 5555 to 8009 and update the corresponding test
- [x] 7.2 Write a test that `connect` wakes, verifies the stored credential, and returns a session
- [x] 7.3 Write a test that an unreachable device or rejected credential raises `ConnectionFailedError`
- [x] 7.4 Implement `connect` until 7.2–7.3 pass

## 8. Cleanup

- [x] 8.1 Delete `src/universal_remote/adapters/adb_text.py` and `tests/test_adb_text.py`, along with the ADB test doubles in `tests/fakes.py` that only they and the Fire TV tests used
- [x] 8.2 Remove the `adb-shell[async]` dependency from `pyproject.toml` (only `firetv.py` and its test import it) and relock
- [x] 8.3 Remove the `collect_all('adb_shell')` step from `universal-remote.spec`, which would fail the frozen build once the dependency is gone, and regenerate `THIRD_PARTY_LICENSES.md` from the new lock
- [x] 8.4 Update the module docstring in `firetv.py` to describe the REST transport instead of ADB
- [x] 8.5 Update any in-repo documentation that states Fire TV requires ADB or developer mode
- [x] 8.6 Add a `homebrew-distribution` spec delta dropping `adb-shell` from the dynamic-import dependencies the frozen bundle must carry
- [x] 8.7 Report the digit/text failure reason on a key press (`tui/remote_screen.py`, `tui/actions.py`): a Fire TV digit is typed rather than sent as a keycode, so "may be unreachable" would misstate an unfocused field
- [ ] 8.8 At archive time, hand-edit the `## Purpose` line of `openspec/specs/firetv-adapter/spec.md`, which still describes popup pairing and a low-latency path with a fallback — no delta block can express a Purpose change, so archive would leave it asserting the opposite of the shipped behaviour

## 9. Verification

- [x] 9.1 Run formatters and linters and fix all findings
- [x] 9.2 Run the full test suite and fix all failures
- [ ] 9.3 Pair against a real Fire TV with ADB debugging **off** and confirm the PIN flow completes
- [ ] 9.4 Confirm on hardware: d-pad, OK, back, home, menu, play, pause, text entry, and a digit
- [ ] 9.5 Confirm FAST_FORWARD and REWIND scrub during playback, and note any player where they do not
