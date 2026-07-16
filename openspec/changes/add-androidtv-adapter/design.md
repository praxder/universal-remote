## Context

The remote is built on a brand-agnostic seam: a generic `Key` vocabulary, a `Capabilities` declaration, an `Adapter` protocol (`platform`, `display_name`, `capabilities()`, `pair()`, `connect()`), a `BaseSession` that gates sends against declared capabilities, and an `AdapterRegistry` mapping a device's `platform` string to an adapter. Five adapters exist. Two pairing shapes are already in use:

- **Popup** (Samsung, LG, Fire TV): `pair()` opens a connection, the TV shows an "Allow" popup, a single opaque credential returns to persist and replay. No prompt.
- **PIN** (Apple TV): the TV shows a code the user reads back. `add-appletv-adapter` wired the `Adapter.pair(prompt=…)` hook end-to-end through `PairingScreen` (a mid-pairing input state driven by an `asyncio.Future`), and added `PairingCancelledError` for "PIN adapter, no prompt".

Android TV is a **PIN** platform and reuses that flow verbatim. The two facts that shape this design:

1. **Android TV / Google TV ships the Android TV Remote protocol v2**, on by default, no developer mode — unlike Fire TV, whose only control path is ADB. The `androidtvremote2` library (the basis of Home Assistant's `androidtv_remote` integration, and what the Google TV phone app speaks) implements it: pair with a device-shown code, persist a client certificate, replay it on connect over TLS.
2. **`androidtvremote2` is file-path based.** `AndroidTVRemote(client_name, certfile, keyfile, host)` reads the client cert and key from files; `async_generate_cert_if_missing()` *writes* them to disk. Our `Device.credential` is one in-memory string, and the codebase deliberately keeps pairing keys off persistent disk (Fire TV's `_keygen` uses a throwaway temp dir). This mismatch is the design's central problem.

## Goals / Non-Goals

**Goals:**
- Implement the Android TV platform against the existing `Adapter`/`Session` seam, mirroring the Apple TV structure and testing approach (injected library factory, in-memory fake, no real hardware).
- Reuse the existing PIN-entry `PairingScreen` flow with zero TUI change.
- Bridge the file-path library to the single-string credential model without leaking keys to persistent disk.

**Non-Goals:**
- No ADB path. (That is Fire TV's adapter; using it here would force developer mode and break on Android 11+ wireless-debugging pairing, which the repo's `adb_shell` cannot perform.)
- No voice input, app-launch/deep-link, now-playing, or IME features beyond the generic key set and best-effort text.
- No changes to the generic key vocabulary, `Capabilities`, `Session` seam, registry, device model, store file format, or `PairingScreen`.

## Decisions

### Decision: Use `androidtvremote2` over the Remote v2 protocol, not ADB
Android TV's native remote protocol is enabled by default and needs no developer mode, so it works out of the box and matches what real remote apps do. `androidtvremote2` is the maintained Python implementation. ADB reuse (copying Fire TV) was rejected: it forces the user to enable developer options, produces a ~90% duplicate of `firetv.py`, and — decisively — modern Android 11+ devices gate network ADB behind "wireless debugging" pairing (6-digit code + dynamic port) that the repo's `adb_shell` library does not implement. The protocol split, not the shared kernel, is what makes this a separate adapter from Fire TV.

**Alternatives considered:**
- *ADB reuse via `firetv.py` mechanics* — rejected for developer-mode requirement, near-total duplication, and the Android 11 pairing gap.
- *Register Android TVs as Fire TV devices* — rejected: relies on ADB being enabled, wrong pairing UX, and misrepresents the platform.

### Decision: Pack cert + key into one credential string; materialize to an ephemeral temp dir
Pairing generates a client **cert** and **key** (two PEMs); the library reads them from file paths. To fit the seam's single-string credential and keep keys off persistent disk:

- **Pairing:** generate into a `TemporaryDirectory`, read both PEM files back, and return them packed into one opaque credential string (a small JSON object `{"cert": <pem>, "key": <pem>}`). The temp dir is discarded when pairing returns — nothing persists to disk except inside the encrypted device store, exactly as Fire TV's private-key PEM does.
- **Connect:** unpack the stored credential, write the two PEMs into a fresh `TemporaryDirectory`, pass those paths as `certfile`/`keyfile`, and connect. The session owns the temp dir for its lifetime and removes it on release, so no key material outlives the session on disk.

This mirrors Fire TV's "ephemeral temp dir, credential is a PEM string" intent, extended to two artifacts. The credential stays opaque to the store and UI.

**Alternatives considered:**
- *Persist stable cert/key file paths in the credential* — rejected: leaks key material to persistent disk indefinitely and couples the store to a filesystem layout.
- *Subclass the library to accept PEM strings* — rejected: fights a file-path-oriented API for no benefit over a temp-dir bridge.

### Decision: Full Android capability set, single dispatch path
`send_key_command` accepts an Android keycode by name, so every generic key maps to one `KEYCODE_*` action: directional (`DPAD_UP/DOWN/LEFT/RIGHT`), OK (`DPAD_CENTER`), `BACK`, `HOME`, `MENU`, `VOLUME_UP/DOWN`, `VOLUME_MUTE`, `MEDIA_PLAY/PAUSE/PLAY_PAUSE/STOP/REWIND/FAST_FORWARD`, `CHANNEL_UP/DOWN`, and `KEYCODE_0`–`KEYCODE_9`. Android TV declares **MUTE and channel up/down** (unlike Fire TV, which has no tuner) — the capability-driven button gating enables them with no UI change. There is **no evdev fast-path split** (Fire TV's optimization for the slow `input` binary): the v2 protocol is already a low-latency persistent connection, so one dispatch path suffices. `send_key_command` and `send_text` are synchronous library calls invoked from the async session's `_dispatch_*`.

### Decision: Identity is guaranteed by the certificate; no new model field
Connect needs only host + cert. The paired cert is whitelisted by exactly the one TV that accepted the code, so a different device at a reused IP fails the TLS/auth handshake and surfaces as `ConnectionFailedError` — no separate identifier check is needed. `Device.identifier` (added by Apple TV) is left unset, so `device-management` is unchanged.

### Decision: Map library exceptions to the seam's failure contract
`async_connect` failures (`CannotConnect`, `InvalidAuth`, `ConnectionClosed`, timeouts) are caught and re-raised as `ConnectionFailedError(f"Could not connect to {device.name}")`, matching every other adapter. `send_text` failure raises `TextUnsupportedError`. Pairing with `prompt is None` raises `PairingCancelledError`, as Apple TV does.

## Risks / Trade-offs

- **`androidtvremote2` API differs from the other clients** (file-path cert, sync send methods, its own exception set). → Isolate every library call inside `adapters/androidtv.py` behind an injected factory; tests use an in-memory fake, so the seam and TUI never depend on the library shape.
- **Cert-file lifetime during a session is library-internal.** If the library re-reads `certfile`/`keyfile` after `async_connect` (e.g. on reconnect), a too-early temp-dir cleanup would break it. → Session owns the temp dir for its whole lifetime and cleans it only on `_release`; confirm the exact read timing against the pinned version (open question).
- **Key-name vocabulary correctness is only hardware-verifiable.** → As with every adapter, tests prove the adapter emits the intended `send_key_command` argument, not that a real TV accepts it; the `KEYCODE_*` names are confirmed against the pinned library's key table during task 1, then accepted best-effort.
- **Best-effort text depends on the focused app/IME.** → Declared `text=True`, attempted, and reported `TextUnsupportedError` on failure rather than silently dropped.

## Migration Plan

Additive: a new adapter module plus one registration line and a new dependency. No data migration; existing devices and store files are untouched. Rollback is removing the registration line and the dependency.

## Open Questions (resolve during implementation)

- **Exact `androidtvremote2` entry points and key table for the pinned version**: constructor args (`client_name`, `certfile`, `keyfile`, `host`, ports), `async_generate_cert_if_missing()`, `async_start_pairing()`/`async_finish_pairing(code)`, `async_connect()`, `disconnect()`, `send_key_command(name)`, `send_text(text)`, and the precise `KEYCODE_*` names accepted. Confirm before finalizing the mapping (mirrors how the Apple TV change confirmed `pyatv` entry points in task 1).
- **Whether `certfile`/`keyfile` must persist past `async_connect`** — determines whether the temp dir is cleaned right after connect or held for the session lifetime. Default to holding it for the session and cleaning on `_release`.
- **Credential packing format** — JSON `{"cert", "key"}` is the proposed shape; confirm no PEM escaping issue and that the store round-trips it as an opaque string.
- **`client_name`** — the label the TV shows during pairing (e.g. "Universal Remote"); pick a stable constant.
