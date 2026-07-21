## Why

Deleting a saved device is only discoverable through the Backspace key on the device list — invisible to anyone editing a device who wants to remove it. The edit screen is the natural place to expect a delete action, so it should offer one.

## What Changes

- Add a Delete button to the edit device screen, shown below Save and only when editing an existing device (never when adding).
- Activating Delete reuses the existing delete-confirmation prompt; confirming removes the device and returns to the saved-device list, cancelling leaves the store unchanged.
- The Delete button joins the edit screen's Tab / Up / Down focus order.
- The existing Backspace-on-a-row delete on the device list is unchanged (this is an additional entry point).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `tui-remote`: The "Manage saved devices" requirement gains a second delete trigger — a Delete button on the edit screen — and extends the edit screen's keyboard-navigable set to include it.

## Impact

- `src/universal_remote/tui/devices_screen.py` — `AddDeviceScreen` (Delete button + confirm/delete/pop handler, edit-only).
- `src/universal_remote/tui/app.py` — CSS for the Delete button (error variant, left-aligned like Save).
- `tests/test_tui_devices.py` — coverage for the new button.
- Reuses existing `ConfirmDeleteScreen` and `store.delete`; no new store or dialog code.
