## Context

The Add/Edit Device screen (`tui/devices_screen.py`) collects IP, Name, Model, MAC, and a Probe button that auto-fills Name/Model/MAC from a TV's info endpoint (`devices/probe.py`). `Device` (`devices/models.py`) carries `mac` and `model`. The only functional consumer of `mac` is Wake-on-LAN power-on (`SamsungTizenAdapter.power_on` / `LgWebOsAdapter.power_on`); `model` is never read by any adapter.

Power in the app has two distinct paths:
- **Live power-off** — user-facing: the on-screen Power button sends `Key.POWER`, which LG maps to `client.power_off()` and Samsung maps to `KEY_POWER`.
- **Wake-on-LAN power-on** — the `power_on()` methods. A grep confirms these are called only by tests; no TUI flow invokes them. So the WoL plumbing is already dead code.

This change removes both power paths, the probe, and the model/MAC fields, restyles the add/edit title as ASCII art, and adjusts Save-button spacing.

## Goals / Non-Goals

**Goals:**
- Add/Edit Device screen reduced to manual IP + Name entry.
- Power removed everywhere: `Key.POWER`, `Capabilities.power_on`, both `power_on()`/`PowerOnResult`, LG power-off handling, the on-screen Power button, and the `wakeonlan` dependency.
- `mac`/`model` gone from `Device`; legacy saved files still load.
- Add/Edit title rendered as ASCII-art banners with Devices-page spacing; Save button aligned with the inputs.

**Non-Goals:**
- No replacement for power control (physical remote handles on/off).
- No migration script for `devices.json` — tolerant load is sufficient.
- No change to pairing, connect, key-send, text entry, or the device list screen behavior.

## Decisions

### Tolerant `Device.from_dict`
`from_dict` is currently `cls(**data)`. With `mac`/`model` removed from the dataclass, a legacy entry containing those keys raises `TypeError`. Decision: filter `data` to the dataclass's known field names before constructing. This drops unknown keys silently on load; they disappear from disk on the next `save_all` (which re-serializes via `to_dict`). Chosen over a one-shot migration (no separate migration surface to maintain) and over keeping the fields (defeats the removal).

### Remove `Key.POWER` from the enum, not just the UI
`Key.POWER` is removed from `keys.py`. Both adapters drop it from their key maps/supported sets; LG drops the `if key is Key.POWER: power_off()` branch in `_dispatch_key`; the remote surface drops the Power button. `RemoteScreen.on_mount` iterates `for key in Key` to disable unsupported buttons, so removing the enum member removes it from that loop automatically. Chosen over hiding only the button so no dead brand code (`KEY_POWER`, `power_off`) lingers.

### Remove the `power_on` capability flag
`Capabilities.power_on` is read only by tests; no runtime code branches on it. It is removed from the dataclass and from both adapters' `_CAPABILITIES`. This keeps `Capabilities` to exactly what the app uses (`keys`, `text`).

### ASCII banners for Add/Edit titles
Follow the existing `TITLE_ART` pattern in `devices_screen.py` (a raw-string figlet "Standard"-style banner rendered in a `Static`). Add two banners — "Add Device" and "Edit Device" — and select which to show by `self._existing`. Match the Devices banner's spacing mechanism: the `#devices-title` rule uses `margin: 1 0 2 0` (margin, not padding). The new title needs its own `width:` set wide enough for the longest banner line so it does not wrap — "Add Device"/"Edit Device" are wider than "Devices", so the width will differ from `#devices-title`'s `36`; set it to fit the generated art.

### Save-button and title CSS are new rules
`app.py`'s `CSS` block has no `#add-device` rules today, so title and Save styling are added, not edited. "Same left padding as the inputs" and "top padding to separate from inputs" are visual-alignment targets: the exact values are chosen to match the input fields' effective left edge and verified against the live layout at implementation time rather than copied from an existing number.

## Risks / Trade-offs

- **[LG loses in-app power-off]** Removing the Power button removes LG's working `power_off()` path (not just best-effort WoL). → Accepted and intended by the maintainer; the physical remote handles power. Called out explicitly here so it is a conscious behavior change, not an accident.
- **[Legacy files silently drop fields]** A tolerant `from_dict` hides genuinely malformed entries too. → Acceptable: the store is app-owned and the only "unknown" keys in the wild are the removed `mac`/`model`. Covered by a spec scenario and a store test.
- **[Banner wrapping]** If the new title `width:` is too narrow, the multi-line ASCII art wraps and garbles. → Set width to the widest banner line and verify by running the screen.
- **[Test breadth]** Power/probe/mac/model touch ~11 test files plus `fakes.py`. → Enumerated in tasks.md so none are missed; the full suite must pass at preflight.

## Migration Plan

No deployment or data migration. Legacy `devices.json` files load unchanged and are rewritten without the removed keys on the next save. Removing `wakeonlan` from `pyproject.toml` requires a dependency re-sync (`uv sync` / equivalent) in dev environments.
