## 1. Device model

- [ ] 1.1 Write a failing test: a `Device` with `text_via_adb=True` round-trips through `to_dict`/`from_dict`, and legacy JSON without the field defaults it to `False`.
- [ ] 1.2 Add `text_via_adb: bool = False` to `Device` in `devices/models.py`; confirm the round-trip test passes.

## 2. ADB text seam (`adapters/adb_text.py`)

- [ ] 2.1 Write failing tests for `escape_for_input_text`: spaces become `%s`, shell-special characters are escaped, and a plain word is unchanged.
- [ ] 2.2 Implement `escape_for_input_text` as a pure function; confirm its tests pass.
- [ ] 2.3 Define the injectable `AdbRunner` seam and a default that runs `adb` via an `asyncio` subprocess; add `find_adb()` (PATH + common macOS locations).
- [ ] 2.4 Write failing tests with a fake `AdbRunner` for `resolve_target(ip)` (parses `adb mdns services`, matches the row by IP, returns current `ip:port`; returns nothing when absent).
- [ ] 2.5 Implement `resolve_target`; confirm its tests pass.
- [ ] 2.6 Write failing tests with a fake `AdbRunner` for `send_text(target, text)` (idempotent `adb connect` then `adb -s target shell input text <escaped>`) and for `pair(ip, port, code)` (`adb pair ip:port code`), asserting the exact argv.
- [ ] 2.7 Implement `send_text` and `pair`; confirm their tests pass.

## 3. Adapter text routing

- [ ] 3.1 Write failing adapter tests: an opted-in device routes `_dispatch_text` through the ADB seam (resolve + send), and a non-opted-in device routes through Remote v2 `send_text` (assert via injected fakes/argv).
- [ ] 3.2 Wire `AndroidTvSession` to know the device IP + opt-in and route `_dispatch_text` accordingly, resolving the ADB target lazily on first send; confirm routing tests pass.
- [ ] 3.3 Write failing tests for fallback: opted-in but `adb` missing, and opted-in but device unreachable, both fall back to Remote v2 and signal ADB-text-unavailable.
- [ ] 3.4 Implement the fallback + unavailable signal; confirm fallback tests pass.

## 4. Adapter ADB pairing

- [ ] 4.1 Write failing tests: adapter ADB-pair reports success on a passing `adb pair` and reports failure on a failing one, with the device not marked opted in on failure.
- [ ] 4.2 Expose the ADB pairing operation on the adapter (delegating to the seam's `pair`); confirm tests pass.

## 5. TUI opt-in action and status

- [ ] 5.1 Add the per-device "Set up text input (ADB)" action: guidance, prompts for pairing address + code, run adapter ADB pairing, set `text_via_adb=True` and persist on success, report failure and leave the device unchanged otherwise.
- [ ] 5.2 Surface the ADB-text-unavailable signal as a one-line status on the Use Remote surface when a send falls back.
- [ ] 5.3 Add tests for the setup action (success records + persists opt-in; failure leaves device unchanged) and for the fallback status line.

## 6. Documentation and preflight

- [ ] 6.1 Update in-repo docs (README / relevant notes) to describe the opt-in ADB text path and its Developer-options / wireless-debugging prerequisites.
- [ ] 6.2 Preflight: format, lint/type-check, and run the full test suite; fix any issues.
- [ ] 6.3 Validate the change: `openspec validate add-androidtv-adb-text --strict`.
