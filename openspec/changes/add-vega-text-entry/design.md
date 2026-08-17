## Context

See proposal.md — Why for the motivation and the probe table behind it. What shapes the
design beyond that:

- Every observation here came from probing a live Vega (192.168.20.56) and an Android
  Fire OS Fire TV, with a human reading the television for each write, because the
  control API answers `200 {"description":"OK"}` to a write it discards. Statuses alone
  cannot tell the two platforms apart.
- The Vega's text route accepts exactly one character. `{"text": "q"}` is accepted;
  `{"text": "we"}` is `400 Bad arguments supplied`. Accepted characters were verified
  landing in order: letters, digits, space, and `!`. `é` and `😀` are
  `500 Error in performing the operation on the Fire TV`.
- A Vega never raises an on-screen keyboard, so `GET /v1/FireTV/keyboard` reports
  `{"mode": null, "state": "hidden", "text": null}` permanently — verified while a search
  field held focus. There is no focus oracle on the platform.
- The Android Fire OS path's confirm-read is load-bearing and its reasoning is recorded
  in `FireTvSession._confirm`: a focused field that has never been typed into reports
  `visible` rather than `text`, so the state name cannot decide writability, and the
  field's contents are the only honest signal. Nothing here may weaken that.
- `_retrying` justifies itself on requests being "individual and idempotent — each
  keyboard write sends the whole intended value, never a delta". A per-character POST to
  an appending route is a delta, so it cannot ride that seam unchanged.
- `openspec/specs/firetv-adapter/spec.md` currently requires non-ASCII support and a
  confirm-read for all Fire TV text entry. Both are false on a Vega, which is why the
  requirement becomes platform-conditional rather than gaining an exception.

## Goals / Non-Goals

**Goals:**

- One session decides its text path once, at connect, and every later keypress is a
  single request with no detection overhead.
- The Android Fire OS path is byte-for-byte unchanged in behaviour, including its
  confirm-read and its `No text field is focused` report.
- A Vega text failure never leaves a character typed twice.
- A Vega digit key stops raising `TypeError` out of the adapter.

**Non-Goals:**

- Backspace or field clearing. `POST /v1/FireTV?action=backspace` was verified working on
  a Vega (it deleted a character), but `Key` has no generic backspace member, so wiring
  one would touch every adapter. Recorded as a finding, not built on.
- Replace semantics on a Vega. Emulating the Android Fire OS replace would mean
  backspacing the field first, and a Vega reports its contents as null, so the number of
  backspaces to send is unknowable.
- Unifying the two text paths onto the single-character route. See Open Questions.
- Non-ASCII text on a Vega. The device rejects it; nothing in the adapter can carry it.

## Decisions

**Detect the platform from `properties.platformType`, gated by `info`.**
`connect()` already fetches `info()` and discards its body. It now reads
`isPropertiesApiSupported` from that body, and only then requests
`GET /v1/FireTV/properties` and compares `platformType` against `native`. One extra round
trip per connect, none per keypress.
*Alternative — `isPropertiesApiSupported` alone*, which is free since info is already
fetched, was rejected as a proxy: an Android Fire OS build that later gains the
properties API would be misread as a Vega.
*Alternative — no detection, falling back behaviourally* when a confirm-read reports
`hidden`, was rejected because it destroys the honest `No text field is focused` report:
an Android Fire OS device with nothing focused reports exactly that state, so it would
fall through and silently type into nothing.

**Detection failure degrades rather than failing the connection.**
`connect()` currently wraps `wake()` and `info()` in one `try` whose `except` closes the
transport and raises `ConnectionFailedError`. The properties read joins that same block —
placing it after, where a raise would exit `connect()` with the transport never closed and
no session returned, would leak the transport. It gets its own suppression inside the
block instead: a properties read that fails is caught there and answered with the keyboard
writer, so it never reaches the `except` that fails the connection. A properties hiccup
must not make a Vega that connects today refuse to connect at all. A device whose platform
could not be established keeps the keyboard path — text entry is then wrong on a Vega, but
every navigation and transport key still works, which is the larger share of the remote.

**Two writers, composed into the session rather than subclassed into it.**
`FireTvSession` holds a writer; `connect()` chooses which one. This mirrors `androidtv.py`
delegating its text handling to `androidtv_text.py`, and keeps the keyboard writer's
confirm-read reasoning in one place instead of splitting it across a base class and an
override.

The writer carries two operations, not one, because a digit is not a one-character string
on the keyboard path. There, text entry *replaces* the field, so routing a digit press
through `send_text` would wipe a search box the user had already typed into; the digit has
to be appended by reading the contents back and rewriting them. On a Vega both are the
same single-character request. So the seam is:

- `send_text(text)` — keyboard writer: set the field, then confirm. Vega writer: guard the
  characters, ready the service, then one request per character.
- `type_digit(digit)` — keyboard writer: read the field, write back the contents with the
  digit appended, then confirm. Vega writer: one request for that character.

`_dispatch_key`'s digit branch calls `type_digit`, so neither the read-modify-write nor
its absence leaks into the session.

**A Vega send types each character at most once.**
The writer makes the service ready before the first character and then sends each
character with no per-character retry. `_retrying` stays exactly as it is, used by the
keyboard writer and by navigation keys, where a resent request carries the whole intended
value.
*Alternative — per-character `_retrying`* was rejected on two counts: an ambiguous
transport failure (the device applied the write, the response was lost) types the
character twice on an appending route, and the `wake()` inside a retry POSTs the DIAL app
`/apps/FireTVRemote`, which can move focus while the rest of the string is still queued.
*Alternative — retrying the whole string* is worse still: it appends the string a second
time on top of a partial one, and the field cannot be cleared first.
A mid-string failure therefore reports that part of the text may already have been typed.
That is a worse message than the Android Fire OS path gives, and it is the honest one: the
adapter cannot read the field back to find out.

**The whole send is refused up front when a character is unacceptable.**
The guard runs before the first request, so a refused send leaves the field untouched —
consistent with the atomicity the Android Fire OS path gets from a single write.
*Alternative — send until the device answers 500* leaves a half-typed field the user has
to clear by hand, and reports the error after the side effect.
*Alternative — dropping unacceptable characters* reports success for text the user did not
type, which is the one outcome worse than failing.
The guard admits printable ASCII rather than everything `str.isascii()` accepts, since
control characters are ASCII by that test and were never exercised on the device.

**An absent field value normalises to empty text at the read.**
`keyboard_state()` becomes `body.get("text") or ""`. A Vega sends `"text": null` — the key
is present, so the current `body.get("text", "")` returns `None` and the digit path's
`current + digit` raises `TypeError`. Normalising at the read fixes it for every caller
rather than at each use. This is a fix the keyboard path needs regardless of the Vega
work: any device that reports a null value would crash the same way.

## Risks / Trade-offs

- **A Vega send cannot be verified, so a send with nothing focused reports success.**
  → Unavoidable: the platform reports neither focus nor contents, and the on-screen
  keyboard that would expose a state never appears. The spec states this explicitly so it
  reads as a known platform limit rather than a bug to rediscover.
- **A long string is many requests.** → Measured at 10–30ms per character back to back
  with no rate limiting observed, so a 20-character search query costs well under a
  second. Characters are sent in order and sequentially; parallelising them would scramble
  the field.
- **`platformType` is undocumented and could change.** → Detection failure and an
  unrecognised value both degrade to the keyboard path, so an unexpected value costs
  Vega text entry rather than the whole session. `codiVersion` and `osVersion` are also
  reported and could corroborate later if the marker proves unstable.
- **The Android Fire OS path is exercised only by tests, not by the Vega on hand.** → It
  is untouched by this change, and its existing scenarios stay in the spec verbatim so a
  regression in it fails a test rather than passing quietly.

## Open Questions

- Does the single-character text route also land characters on an Android Fire OS Fire TV?
  The route exists there and answers 200 to a single character, but no one has watched
  that television during a write. If it does work, the two writers could later collapse
  into one — with the keyboard writer's confirm-read kept, since that device can still
  confirm. Answering it changes nothing here: detection-based branching leaves both paths
  independent.
- Whether any non-printable ASCII character (tab, newline) is accepted by the route. The
  guard admits printable ASCII only, so the answer can only widen what is allowed later.
