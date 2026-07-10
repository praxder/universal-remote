## Why

There is no unified, local, keyboard-and-mouse-driven way to control the many TV platforms on a home network (Samsung Tizen, LG webOS, Android TV, Fire TV, Apple TV, Roku), each of which speaks a different control protocol. This change lays the foundation: a pretty terminal remote whose UI and device management are fully platform-agnostic, with the first concrete adapter (Samsung Tizen) proving the seam. Doing the abstraction now — before a second protocol exists — is what keeps every future adapter cheap.

## What Changes

- New Python CLI application (`universal-remote`) built on Textual, launched into a **menu-driven TUI** with two modes: Manage Devices and Use Remote.
- **Device management**: list, add, edit, delete saved devices. Add flow accepts an IP and auto-fills name/model/MAC by probing the TV's info endpoint; user confirms.
- **Platform-agnostic remote core**: a generic `Key` model, a `Capabilities` declaration, and an `Adapter`/`Session` seam with an explicit pair-vs-connect lifecycle and an adapter registry. The TUI and device store never reference a specific TV brand.
- **Samsung Tizen adapter**: the first adapter, wrapping the `samsungtvws` library — token-based pairing (TV popup), key sends, best-effort text input, and best-effort Wake-on-LAN power-on.
- **Remote TUI**: an on-screen remote (D-pad, OK, Back, Home, Volume, Power, text field) that is both clickable and driven by the keyboard (arrows→D-pad, Enter→OK, Esc→Back, etc.). Buttons the active adapter does not support are visibly disabled.
- **Local persistence**: devices and pairing credentials stored in a JSON file with `0600` permissions.
- Project scaffolding: `uv` + `pyproject.toml` pinned to Python 3.13, `pytest` test suite, a `FakeAdapter` and mocked transport so the app is fully testable without a real TV.

## Capabilities

### New Capabilities
- `device-management`: CRUD over saved devices, local persistent store, and IP-probe auto-fill on add.
- `remote-control-core`: the platform-agnostic seam — generic key model, capability declaration, adapter registry, and pair/connect/send/close session lifecycle.
- `samsung-tizen-adapter`: a concrete adapter implementing `remote-control-core` for Samsung Tizen TVs.
- `tui-remote`: the menu-driven Textual UI — device screens plus the clickable, keyboard-driven remote surface.

### Modified Capabilities
<!-- None. Greenfield project; no existing specs. -->

## Non-goals

Deferred to keep the first change minimal (YAGNI):
- Adapters for any platform other than Samsung Tizen (LG, Android TV, Fire TV, Apple TV, Roku). The seam must accommodate them; this change does not build them.
- Automatic network discovery (SSDP/mDNS scanning). Devices are added manually with IP auto-fill only.
- Media transport (play/pause/seek) and channel up/down keys. The button set is limited to D-pad, OK, Back, Home, Volume up/down/mute, and Power.
- OS keychain credential storage (a `0600` JSON file is the v1 store).
- Guaranteed text entry and guaranteed remote power-**on**; both are best-effort on Samsung hardware (see design.md risks).

## Impact

- New codebase; no existing code affected.
- New runtime dependencies: `textual`, `samsungtvws`, `wakeonlan`. Dev: `pytest`.
- Toolchain: `uv`, Python pinned to 3.13.
- Writes a credential-bearing config file under the user's config directory (`~/.config/universal-remote/`, mode `0600`).
- Opens outbound LAN connections to user-configured TV IPs (HTTP info probe, secure WebSocket, UDP WOL magic packet).
