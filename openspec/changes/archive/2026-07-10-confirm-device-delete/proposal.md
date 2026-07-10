## Why

Deleting a device from the Manage Devices list is both hard to trigger and too easy to trigger by accident. The list binds deletion to the `delete` key, which on most keyboards (notably Mac) is the forward-delete key that users rarely press — the large ⌫ key they actually press is `backspace`, which does nothing. And when it does fire, it removes the device immediately with no chance to undo. This change fixes the key and adds a confirmation step.

## What Changes

- Rebind device deletion in the Manage Devices list from the `delete` key to the `backspace` key.
- Show a confirmation prompt before a device is deleted; the device is removed only when the user confirms and is left untouched when the user cancels.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `tui-remote`: The "Device management screens" requirement gains delete-key and confirmation behavior — deletion is triggered by Backspace and requires user confirmation before the device is removed.

## Impact

- `src/universal_remote/tui/devices_screen.py`: change the delete binding key; route `action_delete` through a new confirmation modal screen instead of deleting inline.
- `tests/test_tui_devices.py`: update tests that press `delete` to press `backspace` and drive the confirmation prompt.
- No change to the device store or the `device-management` spec — deletion at the storage layer stays unconditional; confirmation is a UI concern.
