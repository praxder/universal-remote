## 1. Normalise an absent field value

- [x] 1.1 Add a failing test: a keyboard-state read whose body reports `"text": null` yields empty text rather than `None`
- [x] 1.2 Add a failing test: a digit key sent to a device reporting `"text": null` does not raise `TypeError` out of the session
- [x] 1.3 Change `keyboard_state()` to `body.get("text") or ""` so both pass

## 2. The properties and single-character text routes

- [x] 2.1 Add a failing test: `RemoteApi.properties()` GETs `/v1/FireTV/properties` with the client token and returns the reported body
- [x] 2.2 Add a failing test: `RemoteApi.type_character()` POSTs `/v1/FireTV/text` with `{"text": <char>}`
- [x] 2.3 Add `PROPERTIES_PATH`, `TEXT_PATH`, and `PLATFORM_TYPE_NATIVE` alongside the existing route constants, and implement both methods

## 3. Platform detection at connect

- [x] 3.1 Add a failing test: a device whose info reports `isPropertiesApiSupported` has its properties read, and a `native` platform type yields a session on the Vega text path
- [x] 3.2 Add a failing test: a device whose info omits `isPropertiesApiSupported` is never asked for properties and keeps the keyboard text path
- [x] 3.3 Add a failing test: a properties read that raises still yields a session, on the keyboard text path
- [x] 3.4 Add a failing test: an unrecognised platform type keeps the keyboard text path
- [x] 3.5 Read `isPropertiesApiSupported` from the info body `connect()` already fetches, and request properties outside the try that raises `ConnectionFailedError`
- [x] 3.6 Confirm by test that detection happens once per connect and no keypress triggers a properties read

## 4. The two text writers

- [x] 4.1 Extract the current set-field-and-confirm and read-modify-write behaviours into a keyboard writer exposing `send_text` and `type_digit`, with the existing Fire TV text and digit tests passing unchanged against it
- [x] 4.2 Add a failing test: the Vega writer sends one single-character request per character, in order, for a multi-character string
- [x] 4.3 Add a failing test: a string holding a non-printable or non-ASCII character is refused with `TextUnsupportedError` naming the limitation, and no request is sent
- [x] 4.4 Add a failing test: the Vega writer makes the service ready before the first character
- [x] 4.5 Add a failing test: a transport failure part-way through a string fails the send, says part of the text may already have been typed, and re-sends no character
- [x] 4.6 Add a failing test: the Vega writer neither reads the keyboard state before sending nor reports text-unsupported because of it
- [x] 4.7 Implement the Vega writer's `send_text` and `type_digit`, and compose the chosen writer into `FireTvSession`

## 5. Digit keys on a Vega

- [x] 5.1 Add a failing test: a digit key on a Vega session issues one single-character request and no keyboard-state read
- [x] 5.2 Add a failing test: a digit key on a keyboard-path session still reads the field and writes the contents back with the digit appended, rather than replacing the field with the digit — covered by the pre-existing `test_given_a_digit_key_when_sent_then_the_field_is_read_and_written_back`, which asserts the GET/POST/GET sequence and a field of `53` rather than `3`, and which passed unchanged through the 4.1 extraction; a second test asserting the same thing was not added
- [x] 5.3 Route `_dispatch_key`'s digit branch through the writer's `type_digit`

## 6. Documentation and preflight

- [x] 6.1 Update the module docstrings in `firetv.py` and `firetv_api.py` to record the two platforms, the single-character route, and why a Vega send cannot be confirmed
- [x] 6.2 Note the Vega text-entry limits (append-only, printable ASCII, unconfirmable) wherever README documents Fire TV support
- [x] 6.3 Run the formatter, the linter, and the full test suite, and fix what they report
- [x] 6.4 Verify against the live devices: type a multi-character string into a focused Vega search field, press a digit key, and confirm the Android Fire OS Fire TV still reports `No text field is focused` with nothing focused
