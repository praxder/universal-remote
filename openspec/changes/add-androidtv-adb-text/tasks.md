## 1. Device model

- [x] 1.1 Write a failing test: a `Device` with `text_via_adb=True` round-trips through `to_dict`/`from_dict`, and legacy JSON without the field defaults it to `False`.
- [x] 1.2 Add `text_via_adb: bool = False` to `Device` in `devices/models.py`; confirm the round-trip test passes.

## 2. ADB text seam (`adapters/adb_text.py`)

- [x] 2.1 Write failing tests for `escape_for_input_text`: spaces become `%s`, shell-special characters are escaped, and a plain word is unchanged.
- [x] 2.2 Implement `escape_for_input_text` as a pure function; confirm its tests pass.
- [x] 2.3 Define the injectable `AdbRunner` seam and a default that runs `adb` via an `asyncio` subprocess; add `find_adb()` (PATH + common macOS locations).
- [x] 2.4 Write failing tests with a fake `AdbRunner` for `resolve_target(ip)` (parses `adb mdns services`, matches the row by IP, returns current `ip:port`; returns nothing when absent).
- [x] 2.5 Implement `resolve_target`; confirm its tests pass.
- [x] 2.6 Write failing tests with a fake `AdbRunner` for `send_text(target, text)` (idempotent `adb connect` then `adb -s target shell input text <escaped>`) and for `pair(ip, port, code)` (`adb pair ip:port code`), asserting the exact argv.
- [x] 2.7 Implement `send_text` and `pair`; confirm their tests pass.

## 3. Adapter text routing

- [x] 3.1 Write failing adapter tests: an opted-in device routes `_dispatch_text` through the ADB seam (resolve + send), and a non-opted-in device routes through Remote v2 `send_text` (assert via injected fakes/argv).
- [x] 3.2 Wire `AndroidTvSession` to know the device IP + opt-in and route `_dispatch_text` accordingly, resolving the ADB target lazily on first send; confirm routing tests pass.
- [x] 3.3 Write failing tests for fallback: opted-in but `adb` missing, and opted-in but device unreachable, both fall back to Remote v2 and signal ADB-text-unavailable.
- [x] 3.4 Implement the fallback + unavailable signal; confirm fallback tests pass.

## 4. Adapter ADB pairing

- [x] 4.1 Write failing tests: adapter ADB-pair reports success on a passing `adb pair` and reports failure on a failing one, with the device not marked opted in on failure.
- [x] 4.2 Expose the ADB pairing operation on the adapter (delegating to the seam's `pair`); confirm tests pass.

## 5. TUI opt-in toggle and status

- [x] 5.1 Add an Android-TV-only text-input-mode toggle to the Add/Edit screen (gated on an adapter `supports_adb_text` flag): switching to ADB launches the pairing modal (address + code); success holds the opt-in as form intent, cancel/failure reverts the toggle; the opt-in is written to `text_via_adb` on Save. Remove the device-list "Set up text input (ADB)" action.
- [x] 5.2 Surface the ADB-text-unavailable signal as a one-line status on the Use Remote surface when a send falls back.
- [x] 5.3 Add tests: toggle visible only for Android TV; switching to ADB launches pairing and opts in on Save; cancel/failure reverts the toggle and leaves the device unchanged; editing flips an existing device's mode; and the fallback status line.

## 6. Documentation and preflight

- [x] 6.1 Update in-repo docs (README / relevant notes) to describe the opt-in ADB text path and its Developer-options / wireless-debugging prerequisites.
- [x] 6.2 Preflight: format, lint/type-check, and run the full test suite; fix any issues.
- [x] 6.3 Validate the change: `openspec validate add-androidtv-adb-text --strict`.
