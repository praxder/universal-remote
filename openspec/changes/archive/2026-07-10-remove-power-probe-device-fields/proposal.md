## Why

The Add/Edit Device screen carries fields and a Probe button that add friction without earning their keep: `model` is display-only and never read by any adapter, `mac` fed only Wake-on-LAN power-on, and the network probe is an extra step users can skip. We are also dropping the power feature entirely — its power-on (WoL) plumbing is already dead (called only by tests), and the maintainer has decided the physical remote will handle turning TVs on and off. Removing all of this shrinks the surface area to exactly what a connection needs: IP and name.

## What Changes

- **BREAKING** Remove the power feature from the whole app: the on-screen Power button, the generic `Key.POWER`, the `Capabilities.power_on` flag, both adapters' `power_on()`/`PowerOnResult` (Wake-on-LAN), and LG's live power-off handling. TVs are powered on/off with the physical remote.
- **BREAKING** Remove `mac` and `model` from the `Device` model. `Device.from_dict` tolerates legacy `devices.json` entries that still carry those keys (they are dropped on next save).
- Remove the **Model** and **MAC** inputs from the Add/Edit Device screen.
- Remove the **Probe** button and all probe functionality; delete `devices/probe.py` and its wiring in `tui/app.py`. Adding a device is now manual IP + Name entry only.
- Render both the **Add Device** and **Edit Device** screen titles as ASCII-art banners, styled with the same top/bottom margin as the Devices page banner.
- Give the **Save** button the same left padding as the input fields, plus top padding to separate it from the inputs.
- Drop the `wakeonlan` dependency from `pyproject.toml`.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `remote-control-core`: drop `power` from the generic key vocabulary and drop the power-on capability flag.
- `tui-remote`: remove the power button from the on-screen remote surface; the Add/Edit Device screen presents an ASCII-art banner and a manual IP + Name form.
- `device-management`: adding a device is manual IP + Name entry (no probe auto-fill, no model/MAC); listing no longer exposes MAC; the store tolerates loading legacy files that still contain `mac`/`model`.
- `samsung-tizen-adapter`: remove the power capability and the power-handling requirement (power-off key and Wake-on-LAN power-on).
- `lg-webos-adapter`: remove the power capability, the power-key mapping (power-off), and the power-handling requirement.

## Impact

- **Source**: `keys.py`, `capabilities.py`, `adapters/samsung.py`, `adapters/lg.py`, `devices/models.py`, `devices/store.py`, `devices/probe.py` (deleted), `tui/app.py`, `tui/devices_screen.py`, `tui/remote_screen.py`.
- **Dependencies**: removes `wakeonlan`.
- **Data**: legacy `devices.json` files with `mac`/`model` keys load cleanly; those keys are dropped on the next save. No migration step required.
- **Tests**: `test_probe.py` (deleted); updates to `test_keys.py`, `test_capabilities.py`, `test_tui_capabilities.py`, `test_samsung_adapter.py`, `test_lg_adapter.py`, `test_store.py`, `test_device_crud.py`, `test_tui_devices.py`, `test_tui_remote_surface.py`, `test_cli_integration.py`, and `tests/fakes.py`.
