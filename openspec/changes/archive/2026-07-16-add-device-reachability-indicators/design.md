## Context

The Use Remote flow (`src/universal_remote/tui/remote_flow.py`) lists saved devices in a `DeviceOptionList` and, on selection, runs pairing/connect. There is no pre-connect signal of whether a device is on the network. The only existing "is it there" path is `Adapter.connect()`, which is heavyweight: it performs an authenticated handshake, needs a stored credential, may trigger a pairing popup, and opens a live session — all unsuitable for a passive, repeated status check on a list of devices.

Adapters already know their control ports implicitly (Samsung `8002`, Fire TV ADB `5555`), though for some platforms the port lives inside a third-party library (LG `aiowebostv`, Android TV `androidtvremote2`, Apple TV `pyatv`). The app is a Textual TUI, so all probing must run off the input handler as async work and update the UI reactively.

## Goals / Non-Goals

**Goals:**
- Show a green/yellow/red reachability bubble next to each device in the Use Remote picker.
- Determine reachability cheaply and safely — no pairing, no credential, no session, no side effects.
- Keep the list usable immediately; resolve and refresh bubbles asynchronously.
- Add the capability with minimal surface: one small module plus a per-adapter port constant.

**Non-Goals:**
- Proving a device is truly *connect-ready* (that requires the full authenticated connect). Green means network-reachable.
- Adding reachability to the Manage Devices list (only the Use Remote picker is in scope).
- Gating or blocking connection based on the indicator — it is advisory only.
- Wake-on-LAN or any action taken from the indicator.

## Decisions

### Decision: TCP connect probe over ICMP or full connect
Reachability is a bounded `asyncio.open_connection(ip, port)` wrapped in `asyncio.wait_for(timeout)`. Success → reachable; `ConnectionRefusedError`/`TimeoutError`/`OSError` → unreachable.

- **Why not ICMP ping?** TVs frequently drop ICMP or sleep the NIC, producing false reds; raw sockets need privileges and a subprocess. A TCP check against the actual control port is both privilege-free and more meaningful.
- **Why not reuse `connect()`?** Side effects (auth popup), credential requirement, and session teardown make it wrong for a passive, polled check.
- **Why not a per-adapter `reachable()` protocol method?** More accurate but adds a method to every adapter for marginal gain. A single shared probe + one declared port per adapter is the YAGNI choice; the door stays open to upgrade later.

### Decision: Adapters declare `reachability_port: int | None`
Each adapter exposes the TCP port to probe. Read via `getattr(adapter, "reachability_port", None)` so adapters that omit it — and any future platform — degrade to unknown (yellow) rather than erroring.

| Platform | Port | Basis |
| --- | --- | --- |
| Samsung | 8002 | wss control channel (`CONTROL_PORT`) |
| Roku | 8060 | ECP HTTP port |
| Fire TV | 5555 | ADB (`ADB_PORT`) |
| LG WebOS | 3000 | `aiowebostv` tries `ws://:3000` first (falls back to `wss://:3001`) |
| Android TV | 6466 | `androidtvremote2` api/command port |
| Apple TV | 7000 | AirPlay — a proxy for "awake"; Companion control port is mDNS-dynamic |

Apple TV has no fixed control port (pyatv discovers Companion via mDNS), so `7000` is a deliberate approximation: green means the Apple TV is awake and on the network, not that the control channel was verified.

### Decision: New `reachability.py` module
A `Reachability` (or `Status`) enum with `REACHABLE`, `UNREACHABLE`, `UNKNOWN`, and `async def probe(ip, port, timeout) -> Reachability`. Keeping the probe out of the TUI keeps it unit-testable without a running app and free of adapter imports.

### Decision: Progressive render + interval polling in `UseRemoteScreen`
- On mount, render all rows immediately with a yellow bubble, then run one probe cycle right away and start `set_interval(5.0, ...)`.
- Each cycle resolves the adapter per device; a device whose adapter has no port stays yellow. Devices with a port are probed **concurrently** (timeout `2.0s`, strictly below the interval so cycles cannot stack).
- As each probe resolves, the corresponding row's prompt is replaced **in place** (`replace_option_prompt_at_index`) so the highlight/cursor position is preserved and there is no full-list rebuild.
- A per-device in-flight guard skips a device whose previous probe has not yet resolved.
- Probing follows picker visibility: the interval is **paused on `ScreenSuspend`** (a modal or the remote is pushed on top) and **resumed on `ScreenResume`**, which also runs one immediate refresh so bubbles are current on return. On unmount / leaving the screen entirely, the interval is stopped and in-flight work is cancelled.

The bubble is a Rich-markup colored `●` prepended to the existing `"{n}. {name}"` prompt.

## Risks / Trade-offs

- **Green ≠ guaranteed connect** (port open but auth could still fail; Apple TV green is only "awake") → framed as advisory; the existing Retry/Back failure dialog still handles real connect failures.
- **Powered-off TV shows red** (its network stack is down) → this is intended and useful; red explains why a connect would fail.
- **Hardcoded ports can drift** from the libraries that own them (LG/Android TV/Apple TV) → ports are stable in practice; a wrong port only degrades the hint (false red/yellow), never breaks connect.
- **LAN chatter from polling** → bounded by a 5s interval and a 2s timeout; probing stops when the screen is left.
- **Firewall/NAT could refuse a reachable device** → shows red; acceptable for a local-network tool where devices are on the same LAN.

## Open Questions

None — semantics (TCP port open), timing (5s / 2s), and Apple TV handling (AirPlay 7000) were settled during exploration.
