## Why

When choosing a device in the Use Remote flow, the user gets no signal about which TVs are actually on the network — they pick one, wait through the connect spinner, and only then discover it is off or unreachable. A live at-a-glance status next to each device turns that guess into an informed choice.

## What Changes

- Add a **reachability status** for a saved device: reachable, unreachable, or unknown.
- Determine reachability with a lightweight, non-invasive **TCP connect probe** to the platform's control port, bounded by a short timeout — no pairing, no credential, no session, no side effects.
- Each platform adapter **declares the TCP port** used for its reachability probe; an adapter that declares none yields an unknown status.
- The Use Remote device picker shows a **colored status bubble** next to each device name: green (reachable), yellow (unknown / still checking), red (unreachable).
- The picker **polls reachability on an interval** while open, updating each bubble in place; it stops probing when the screen is left.
- The bubble is a **hint only** — connecting to any device, including a red one, remains allowed.

## Capabilities

### New Capabilities
- `device-reachability`: determining whether a saved device is reachable on the network without connecting to it — the reachable/unreachable/unknown status model, the bounded TCP-port probe, and the per-adapter reachability-port declaration.

### Modified Capabilities
- `tui-remote`: the Use Remote device picker gains a per-device reachability indicator that refreshes on an interval and never blocks device selection.

## Impact

- New module `src/universal_remote/reachability.py` (status enum + async probe).
- `src/universal_remote/tui/remote_flow.py` (`UseRemoteScreen`): render bubbles, run the polling cycle, update rows in place, cancel on leave.
- Each adapter (`samsung`, `lg`, `roku`, `firetv`, `androidtv`, `appletv`) gains a `reachability_port` attribute.
- TUI stylesheet: color classes for the three bubble states.
- No new third-party dependencies (uses `asyncio.open_connection`).
