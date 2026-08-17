## Why

Amazon's Vega-based Fire TV devices answer the same remote-control API as an Android
Fire OS Fire TV for every navigation and transport key, so they pair and drive
correctly today. Text entry is the one action that does not work: sending text to a
Vega reports `No text field is focused on this Fire TV` even while a search field holds
focus, and pressing a digit key raises an unhandled `TypeError` out of the adapter.

Probing a Vega (`platformType: "native"`, `codiVersion: "1"`, deviceType
`A1TGF7GBNNZ9EE`) against an Android Fire OS Fire TV established why:

| Request | Android Fire OS | Vega |
| --- | --- | --- |
| `POST /v1/FireTV/keyboard {"text": "abc"}` | 200, the field holds `abc` | 200, and the field stays empty |
| `GET /v1/FireTV/keyboard` | `{"state": "hidden"}`, becoming `visible`/`text` when a field is focused | `{"mode": null, "state": "hidden", "text": null}`, unchanged even while a field is focused |
| `POST /v1/FireTV/text {"text": "q"}` | 200 | 200, and `q` is appended to the field |
| `POST /v1/FireTV/text {"text": "we"}` | 400 | 400 — the route takes exactly one character |
| `GET /v1/FireTV/properties` | 405 | 200, reporting `platformType` |

So a Vega breaks the current text path twice over. The keyboard route accepts a write
and discards it, and the state the adapter confirms against never changes — a Vega
never shows an on-screen keyboard, so `hidden` is permanent and no focus signal exists
at all. Text has to travel one character at a time over `/v1/FireTV/text`, which the
adapter does not use, and a Vega send cannot be confirmed the way the Android Fire OS
send is.

## What Changes

- Detect at connect whether a Fire TV is the Vega platform, by reading the properties
  route when the device's own info reports that route exists. The result is settled
  once per session, never per keypress.
- Enter text on a Vega by typing it one character at a time over the single-character
  text route, appending to the focused field — the same append behaviour the Roku and
  Android TV adapters already present.
- Refuse a Vega send outright, before typing any character, when the text holds a
  character the route rejects. A Vega answers non-ASCII with
  `500 Error in performing the operation on the Fire TV`.
- Type each character at most once. The route appends, so a retried character would be
  typed twice, and the re-wake a retry performs launches a DIAL app that can move focus
  mid-string. A Vega send wakes the service once up front instead, and a mid-string
  failure reports that part of the text may already have been typed.
- Report a Vega send as successful without a read-back, since the platform reports
  neither focus nor contents. The Android Fire OS confirm-read is unchanged and stays
  load-bearing there.
- Type digits on a Vega through the same single-character route, replacing the
  read-modify-write of the field's contents that currently crashes: a Vega reports
  `"text": null`, so the adapter's `body.get("text", "")` yields `None` and
  `current + digit` raises `TypeError: unsupported operand type(s) for +: 'NoneType'
  and 'str'`. An absent field value is normalised to empty text for every caller.

## Capabilities

### Modified Capabilities

- `firetv-adapter`: text entry becomes platform-conditional. The existing keyboard-route
  requirement is scoped to devices that report their focused field's contents, and new
  requirements cover Vega platform detection, Vega text entry, and Vega digit keys.

## Impact

- `src/universal_remote/adapters/firetv_api.py` — the properties route, the
  single-character text route, and normalising an absent field value.
- `src/universal_remote/adapters/firetv.py` — platform detection at connect, and the
  two text paths a session can hold.
- `tests/test_firetv_adapter.py` — the Vega text and digit paths, and detection.
- No new dependency, no credential or storage change: a paired Vega keeps working with
  the token it already holds.
