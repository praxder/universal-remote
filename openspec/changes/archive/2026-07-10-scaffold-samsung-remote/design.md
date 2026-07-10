## Context

Greenfield project. Target: a local, terminal-based universal TV remote that is pretty, mouse-clickable, and fully keyboard-drivable. The first milestone scaffolds the app and ships one working adapter (Samsung Tizen), but the architecture must make later adapters (LG webOS, Android TV, Fire TV, Apple TV, Roku) cheap to add.

Constraints:
- Python 3 with `uv` available; `textual`, `samsungtvws`, `wakeonlan` publish support for the chosen runtime.
- Must run without a real TV in tests (CI-friendly, TDD).
- The user's environment has `uv` and Python 3.14 installed system-wide; the project pins its own interpreter.

This document holds the "how" and the protocol detail. The specs stay behavioral.

## Goals / Non-Goals

**Goals:**
- A clean adapter seam so a new TV platform is "one new module + register it," not a rewrite.
- A remote UI that treats keyboard and mouse as equal input paths and never hard-codes a brand.
- Honest handling of Samsung protocol reality (pairing popup, unreliable text entry, best-effort power-on).
- Full testability via a `FakeAdapter` and a mocked WebSocket transport.

**Non-Goals:**
- Other adapters, network discovery, media/channel keys, keychain storage (see proposal Non-goals).
- Reimplementing any TV wire protocol by hand — we wrap maintained libraries.

## Decisions

### D1. Stack: Python + Textual (over Go + charm)
The stated goal — cheap future adapters — hinges on library availability. Python has maintained libraries for every target platform (`samsungtvws`, `aiowebostv`, `androidtvremote2`, `pyatv`, plus trivial HTTP for Roku); Apple TV in particular is a large undertaking to hand-roll in Go. Textual delivers charm-level polish with native mouse support and CSS-like styling.
- **Alternative — Go + charm**: prettiest kit and the user's initial preference, but each protocol (especially Apple TV) would be built from scratch. Rejected on total-cost-to-goal.
- **Alternative — Node + Ink**: weaker TV-library coverage and aesthetics. Rejected.

### D2. Runtime pinned to Python 3.13
`textual` and `wakeonlan` publish explicit 3.13/3.14 classifiers; `samsungtvws` declares `requires_python >=3.9` with only a generic Python 3 classifier and pulls C-extension transitive deps (e.g. `aiohttp`). 3.13 is the newest interpreter all three are known-safe on. Pin via `uv` (`.python-version` / `pyproject`), not the system 3.14.
- **Assumption to verify at implementation**: `uv sync` resolves cleanly on 3.13. If `samsungtvws` forces a lower cap, drop the pin accordingly.

### D3. Adapter seam: `Adapter` builds a `Session`; explicit pair-vs-connect
Two `Protocol` types. `Adapter` declares `platform`, `capabilities()`, `pair(...)`, and `connect(...) -> Session`. `Session` exposes `send_key(Key)`, `send_text(str)`, `close()`. Pairing is separate from connecting because platforms differ: Samsung returns a token after a TV popup, LG returns a client-key, Android TV needs a PIN typed back. `pair` takes a callback/prompt hook so the TUI can collect a PIN when a future adapter needs one; Samsung ignores it (popup only).
- **Alternative — single `connect` that pairs implicitly**: hides the human-in-the-loop step and can't model PIN entry. Rejected.

### D4. Generic `Key` enum + `Capabilities`; capability-driven UI
The remote and store speak a fixed `Key` vocabulary (`UP DOWN LEFT RIGHT OK BACK HOME VOL_UP VOL_DOWN MUTE POWER`) plus `send_text`. Each adapter returns a `Capabilities` set declaring which keys and whether text/power-on are supported. The TUI renders every button but visibly disables ones the active adapter does not declare. This is the load-bearing seam: adding a platform never edits the UI.

### D5. Async everywhere
Textual runs on asyncio; `samsungtvws` offers `SamsungTVWSAsyncRemote`. Adapter `Session` methods are async and run inside Textual workers so key sends never block the UI thread.

### D6. Local store: JSON file, mode 0600
Devices + credentials persist to `~/.config/universal-remote/devices.json` (XDG-aware), written with `0600` since it holds pairing tokens. CRUD goes through a small store module; the TUI and adapters never touch the file directly.
- **Alternative — OS keychain**: better secret hygiene but more platform code; deferred.

### D7. Add flow: manual entry + IP auto-fill probe
On add, the user enters an IP; the app issues `GET http://<ip>:8001/api/v2/` (Samsung's unauthenticated info endpoint) to prefill name, model, and MAC (`device.wifiMac`), then the user confirms/edits. Probe failure degrades to a fully manual form — it never blocks adding a device.

### D8. Keyboard/mouse mapping and text-field focus model
Remote screen bindings: arrows→D-pad, Enter→OK, Esc→Back, `h`→Home, `q`/Ctrl-C→exit remote. Mouse clicks hit the same actions via Textual button widgets (native hit-testing — no manual zone math). A text field toggles a **text-entry mode**: while focused, typed characters fill a local buffer and Enter sends the buffered string; Esc exits the field (does *not* fire Back) to avoid ambiguity. Outside the field, keys act as remote buttons.

### Samsung Tizen protocol reference (implementation detail, owned by `samsungtvws`)
- Info probe: `GET http://<ip>:8001/api/v2/` → JSON with `device.name`, `device.modelName`, `device.wifiMac`.
- Control channel: `wss://<ip>:8002/api/v2/channels/samsung.remote.control` (self-signed cert → TLS verify disabled by the library).
- Pairing: first connect triggers an on-TV "Allow" popup; on accept the TV returns a token that must be persisted and replayed on later connects.
- Keys: `KEY_UP/DOWN/LEFT/RIGHT`, `KEY_ENTER`, `KEY_RETURN` (Back), `KEY_HOME`, `KEY_VOLUP/VOLDOWN/MUTE`, `KEY_POWER`. Our `Key` enum maps to these in the adapter.
- Power-on: WebSocket is dead while the TV is off, so power-on is a Wake-on-LAN magic packet to the stored MAC; power-off is `KEY_POWER`.

## Risks / Trade-offs

- **[Text input unreliable on 2021+ Tizen]** `SendInputString` is widely reported broken/removed on newer firmware — and text entry is a feature the user explicitly asked for. → The `Capabilities.text` flag is authoritative: the adapter attempts text via the library and, on failure or unsupported firmware, the Session reports text-unsupported so the TUI disables/greys the field and shows a clear "text not supported on this TV" message rather than silently dropping input. Decide the concrete fallback (per-key sends vs. hard-disable) during implementation against a real device; do not spec text delivery as guaranteed.
- **[Wake-on-LAN power-on is best-effort]** Requires both a stored MAC and the TV's "Network Standby / Wake on LAN" setting, which ships **off** on many Samsungs. → Power-*off* (`KEY_POWER`) is reliable and specced as such; power-*on* is specced as best-effort and surfaces a hint if it fails. Never promise out-of-the-box power-on.
- **[`samsungtvws` on Python 3.14]** Transitive C-extension deps may lag the newest interpreter. → Pinning 3.13 (D2) sidesteps it; verify `uv sync` at implementation.
- **[Pairing needs a human at the TV]** First connect blocks on someone tapping "Allow." → Model pairing as an explicit, cancellable step with on-screen guidance and a timeout, not a silent connect.
- **[WebSocket idle drops]** Long-idle control sockets close. → Adapter reconnects (replaying the token) on the next send; surface transient errors without crashing the TUI.

## Open Questions

- Exact text-input fallback (per-key synthesis vs. hard-disable) — resolve against real 2021+ Tizen hardware.
- Whether to keep a live connection warm or connect lazily per action — start lazy; revisit if latency is poor.
