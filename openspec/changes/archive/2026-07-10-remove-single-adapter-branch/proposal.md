## Why

The Add-Device flow and the `device-management` spec both branch on whether only one adapter is registered. But `build_app` always registers two adapters (Samsung + LG), so the single-adapter branch is unreachable in production. The dead logic and its spec wording add noise and imply a mode the app never enters.

## What Changes

- Remove the `len(platforms) <= 1` dead guard from `_platform_selector` in `src/universal_remote/tui/devices_screen.py`; the platform selector is always shown when adding a device.
- Collapse the `len(platforms) <= 1` fallback in `_selected_platform` to read the selector value directly.
- Delete the single-adapter test in `tests/test_tui_devices.py` that exercised the removed branch.
- Simplify the `device-management` "Add device with IP auto-fill" requirement wording to drop the single-adapter conditional, reword the multi-adapter scenario to drop its condition, and delete the "Platform assigned when a single adapter registered" scenario.
- Leave archived change specs frozen (historical record).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `device-management`: The "Add device with IP auto-fill" requirement no longer describes single-adapter behavior; platform selection is always offered.

## Impact

- Code: `src/universal_remote/tui/devices_screen.py`
- Tests: `tests/test_tui_devices.py`
- Spec: `openspec/specs/device-management/spec.md`
- No behavior change for real users (the removed path was unreachable). No API or dependency changes.
