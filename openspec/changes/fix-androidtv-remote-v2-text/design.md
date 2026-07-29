## Context

`AndroidTvSession._dispatch_text` currently calls `androidtvremote2`'s `AndroidTVRemote.send_text`, which builds a Remote v2 `RemoteImeBatchEdit`. On the Google TV launcher search box ("Search for apps and games") the TV silently discarded those edits, which is why the opt-in ADB text path was built.

Protocol tracing against a Chromecast/Google TV (remote service 6.9.906821247, Android 14) established what the TV actually requires. Confirmed by four accepted sends on that surface, including three consecutive sends in one session at roughly 40–90 ms each.

| Batch-edit field | Value the TV accepts | What `send_text` sends |
| --- | --- | --- |
| `ime_counter` | the counter from the inbound batch edit | same — correct |
| `field_counter` | the **live** counter from the TV's text-field status | the inbound batch edit's field counter — wrong |
| `edit_info.text_field_status.start` / `.end` | current field length + inserted length | `len(text) - 1`, ignoring current contents — wrong |
| `edit_info.insert` | `1` | same — correct |

The inbound batch edit's own field counter stayed at `1` permanently and is not the per-edit counter. The counter the TV wants arrives on its text-field status, which reaches the client two ways: on the IME key-inject message when a field gains focus, and on the **IME show-request message after every edit from any source** — including edits made with the physical remote. `androidtvremote2` logs that show-request as `Unhandled:` and drops it.

So the two wrong values cannot be corrected by patching the outgoing message alone. The client must first consume a message the library ignores. That is the whole shape of this change.

Evidence, probe, and full trace set: session scratchpad `FINDINGS.md` and `ime_probe.py` with `run_A`…`run_L`.

## Goals / Non-Goals

**Goals:**

- Android TV text lands over Remote v2 with no ADB, no developer mode, and no wireless debugging.
- Repeated sends in one session work, not just the first.
- All contact with `androidtvremote2` internals is confined to one module with its own tests.
- The ADB text workaround and its user-facing surface area are removed rather than left as dead configuration.

**Non-Goals:**

- Making text work in third-party app text fields. YouTube's search field cannot be focused at all while a Remote v2 client is connected — the TV reports the foreground app but never a text-field status — so no client-side change reaches it, and the ADB path did not reach it either.
- Fixing `androidtvremote2` upstream. Worth doing with the traces as evidence, but this change must not wait on a release.
- Surfacing the field read-back described below.
- Any Fire TV behaviour change.

## Decisions

### Build the batch edit locally instead of calling `send_text`

`send_text` takes no parameters that would let a caller supply the right counter or span, so there is no way to reuse it. The adapter builds the `RemoteMessage` itself from the protobuf types the library already exposes and hands it to the protocol's send path.

*Alternative — vendor a patched `androidtvremote2`:* rejected. The library is otherwise correct and carries pairing, TLS, certificate handling, and the key path; forking all of that to change one message is disproportionate, and it would strand the app on a stale copy.

*Alternative — monkeypatch `RemoteProtocol.send_text` at import time:* rejected. Process-global mutation of a dependency, invisible at the call site.

### Confine private-API contact to one new module

The implementation needs the protocol object hanging off `AndroidTVRemote`, a way to observe inbound messages, and a way to send one. All three are private. A single module owns that coupling: it installs the inbound observer, tracks the field state, and exposes a text-sending operation plus whether a field is currently focused. `AndroidTvSession` talks only to that module.

Rationale: the coupling is real and cannot be avoided, so the useful move is to make it one small, obvious, tested surface that breaks loudly in one place on a library upgrade — rather than spreading private attribute access through the adapter and session.

*Alternative — put it inline in `androidtv.py`:* rejected. Mixes protocol archaeology with adapter wiring and makes the private-API surface hard to see when upgrading the dependency.

### Re-read the field counter on every send; never increment it

The observed counter advanced by 3 on the first accepted edit of a session and by 1 on later ones. The step is not predictable, so the only correct source is the most recent inbound text-field status. This is called out explicitly because a local `+= 1` looks like an obvious simplification and would break the second send in every session.

### Track the field's current contents, not just the counter

The cursor span is current length plus inserted length, so appending correctly requires knowing what is already in the field. The inbound show-request carries that value, so the same observer that keeps the counter fresh keeps the contents fresh, and repeated sends append rather than fight over position.

### Never send the show-request message outbound

Sending it produced an empty inbound batch edit that reset both counters to zero and tore down the IME session. It is a TV-to-client message. Recorded here because it reads like a reasonable way to ask the TV to open its keyboard, and it is actively destructive.

### Report text as unsupported when no field is focused

With nothing focused the TV reports no text-field status, so there is no counter to send and any edit is discarded silently. The session raises the existing text-unsupported error instead, which the remote surface already presents. This replaces the old "ADB text unavailable" status with a condition that is both accurate and actionable.

### Do not spoof the client identity

Claiming the TV's own remote-service package and version was tested and made no difference — the same message shape was accepted without it. Pretending to be Google's client for no functional gain is not worth it.

### Keep the `input text` helpers for Fire TV

`adb_text.py` holds both Android-TV-only machinery (the `adb` client, binary discovery, mDNS target resolution, pairing) and pure `input text` command building and escaping that `firetv.py` imports. The Android TV machinery is deleted; the pure helpers and their tests stay where they are so Fire TV is untouched. Renaming or relocating them would churn Fire TV's imports for no benefit in this change.

### Drop the opt-in flag rather than deprecate it

`Device.from_dict` already ignores unknown fields, so stored entries carrying the old flag load cleanly with no migration step. Keeping a flag that no longer selects anything would be dead configuration that still has to be rendered, persisted, and explained.

## Risks / Trade-offs

- **Depends on `androidtvremote2` private members, so a library upgrade can break text silently** → confine the coupling to one module whose tests fail loudly if the internals move, and pin the dependency version. Keys, pairing, and transport continue to use only public API, so a break degrades text rather than the whole adapter.
- **Verified on one device model and one Fire OS-free Google TV build; other Android TV vendors may order or gate IME messages differently** → the no-field-focused path already yields a clean text-unsupported error rather than a silent drop, so an unverified device degrades honestly instead of appearing to work. Worth re-running the probe against a second vendor before assuming universality.
- **Removing the ADB path is hard to walk back if a surface turns up that only ADB reaches** → the change is revertible from git history, and the ADB path's own prerequisites (developer mode plus wireless debugging) meant it was never available by default anyway. The one surface known to defeat Remote v2 text also defeats ADB text.
- **Devices previously opted into ADB text change behaviour without being asked** → they move to a path that is now verified to work on the surface they were opted in for, with no setup, so the change is a strict improvement and needs no user action.
- **Upstream may fix `send_text` later, leaving the local implementation redundant** → acceptable; the local module can then shrink to a call into the library, and the traces make the upstream report cheap to file.

## Migration Plan

No data migration. Stored devices carrying `text_via_adb` load with it ignored, exactly as existing legacy fields (`mac`, `model`) already are. No user action is required, and the ADB wireless-debugging pairing the user previously performed simply stops being used — the app never removes trust it did not create, so nothing is revoked on the device.

## Open Questions

- Does the corrected recipe hold on non-Google-branded Android TV hardware (Sony, TCL, Hisense, NVIDIA Shield)? Only a Chromecast/Google TV was available. The failure mode is a clean text-unsupported error, so this is a confidence question rather than a correctness risk.
- Should the field read-back the show-request provides — live contents of the focused text field, with no ADB — be surfaced anywhere in the UI? Deliberately out of scope here; captured as a follow-on opportunity.
- The modified `Persistent device store` requirement drops its "ADB text opt-in round-trips" scenario and adds a differently named one covering the withdrawn field's tolerance on load. `validate --strict` accepts this, and expressing it as a removal plus an addition of the same requirement name is rejected outright, so MODIFIED is the only available form. If the archive step's scenario drop-guard objects, resolve it there rather than with `--no-validate`.
