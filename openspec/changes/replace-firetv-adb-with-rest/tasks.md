## 1. HTTP seam

- [ ] 1.1 Add a `RemoteApi` client module for the Fire TV REST API, taking host plus an injectable request function so tests need no network
- [ ] 1.2 Write tests covering request construction: `X-Api-Key`, `User-Agent`, `X-Client-Token` when a token is held, and self-signed TLS accepted for this host only
- [ ] 1.3 Implement request construction until 1.2 passes

## 2. Wake

- [ ] 2.1 Write tests for the DIAL wake: posts to `http://<ip>:8009/apps/FireTVRemote`, polls the control port, and returns once it accepts
- [ ] 2.2 Write a test that a wake against an already-running service succeeds
- [ ] 2.3 Write a test that a control port never accepting within the timeout raises a connection failure
- [ ] 2.4 Implement wake until 2.1–2.3 pass

## 3. Pairing

- [ ] 3.1 Write tests for `pair`: wakes, posts `pin/display`, requests the PIN through the prompt seam, posts `pin/verify`, returns the token from the `description` field
- [ ] 3.2 Write a test that a rejected PIN raises a pairing failure and returns no credential
- [ ] 3.3 Write a test that pairing without a prompt raises a pairing failure rather than supplying a value
- [ ] 3.4 Implement `pair` until 3.1–3.3 pass

## 4. Key dispatch

- [ ] 4.1 Replace `FIRETV_KEYS` and `EVDEV_KEYS` with a single map from generic key to REST action, using the verified nav vocabulary
- [ ] 4.2 Map `PLAY` and `PAUSE` to `/v1/media`, and `FAST_FORWARD`/`REWIND` to `dpad_right`/`dpad_left`
- [ ] 4.3 Write tests that keys dispatch with an **empty** request body, never `keyActionType`
- [ ] 4.4 Write a test that a 400 from the device surfaces as a failure, not a success
- [ ] 4.5 Write a test that an undeclared key is rejected without sending a substitute action
- [ ] 4.6 Implement `_dispatch_key` until 4.3–4.5 pass

## 5. Text and digits

- [ ] 5.1 Write a test that a text send reads `GET /v1/FireTV/keyboard` **before** posting, and that a `state` of `hidden` raises `TextUnsupportedError` without any POST being issued
- [ ] 5.2 Write a test that a `state` of `text` then sets the field via `POST /v1/FireTV/keyboard` with no caller escaping
- [ ] 5.3 Write a test that non-ASCII text is transmitted unchanged
- [ ] 5.4 Write a test that a digit key reads the current field and writes back the concatenation, since the endpoint replaces rather than appends
- [ ] 5.5 Implement `_dispatch_text` and digit dispatch until 5.1–5.4 pass

## 6. Capabilities and session

- [ ] 6.1 Update `_CAPABILITIES` to drop `VOL_UP`, `VOL_DOWN`, `MUTE`, `PLAY_PAUSE`, and `STOP`, keeping `text=True`
- [ ] 6.2 Write a test asserting the dropped keys are absent and the retained set is present
- [ ] 6.3 Rewrite `FireTvSession` to hold the token and API client instead of an ADB device, with `_release` closing only what it owns
- [ ] 6.4 Write a test that a connection failure mid-session triggers one re-wake and retry before surfacing an error
- [ ] 6.5 Implement the re-wake-and-retry behaviour until 6.4 passes

## 7. Reachability and connect

- [ ] 7.1 Change `reachability_port` from 5555 to 8009 and update the corresponding test
- [ ] 7.2 Write a test that `connect` wakes, verifies the stored credential, and returns a session
- [ ] 7.3 Write a test that an unreachable device or rejected credential raises `ConnectionFailedError`
- [ ] 7.4 Implement `connect` until 7.2–7.3 pass

## 8. Cleanup

- [ ] 8.1 Delete `src/universal_remote/adapters/adb_text.py` and `tests/test_adb_text.py`
- [ ] 8.2 Remove the `adb-shell[async]` dependency from `pyproject.toml` (only `firetv.py` and its test import it)
- [ ] 8.3 Update the module docstring in `firetv.py` to describe the REST transport instead of ADB
- [ ] 8.4 Update any in-repo documentation that states Fire TV requires ADB or developer mode

## 9. Verification

- [ ] 9.1 Run formatters and linters and fix all findings
- [ ] 9.2 Run the full test suite and fix all failures
- [ ] 9.3 Pair against a real Fire TV with ADB debugging **off** and confirm the PIN flow completes
- [ ] 9.4 Confirm on hardware: d-pad, OK, back, home, menu, play, pause, text entry, and a digit
- [ ] 9.5 Confirm FAST_FORWARD and REWIND scrub during playback, and note any player where they do not
