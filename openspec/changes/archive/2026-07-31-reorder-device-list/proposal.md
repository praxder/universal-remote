## Why

The saved-device list is stuck in the order devices happened to be added, and that order drives both the Manage Devices list and the Use Remote picker — including the `1`–`9` digit shortcuts. A user with several devices cannot put the one they reach for daily at position `1`, so the most-used device can sit behind a digit that is awkward to press or off the numbered range entirely.

## What Changes

- Manage Devices gains a **Move Up** / **Move Down** button row below the device list, acting on the highlighted device row.
- `shift+up` and `shift+down` on the Manage Devices list do the same thing, with `K` and `J` as hidden Vim aliases, so a keyboard user never leaves the list.
- A move swaps the device with its neighbour in the stored order and persists immediately; the order survives restarts.
- The list highlight follows the moved device to its new position, so repeated presses walk a device several places.
- A move that cannot happen — the first device moved up, the last moved down, or the highlight on the `+ Add` row — does nothing, silently, and leaves the store untouched.
- The Use Remote device picker lists devices in the same reordered order, and its digit shortcuts follow. Reordering is possible **only** on Manage Devices; the picker is read-only with respect to order.
- Row numbering (`1. Apple TV`) is unchanged in form, but now reflects a user-controlled order rather than insertion order.

No new stored field: the device list order *is* the order of the `devices` array in `devices.json`, which nothing sorts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `device-management`: adds a reorder requirement (move a saved device up or down, persisted, boundary moves are no-ops) and states that listing returns devices in their stored order.
- `tui-remote`: the Manage Devices screen requirement gains the Move Up / Move Down buttons, their key bindings, the no-op boundaries, and the highlight-follows-the-device rule; the numbered-list requirement is restated so numbering and digit selection reflect the user-controlled persisted order on both lists.

## Impact

- `src/universal_remote/devices/store.py` — new `move_up` / `move_down` over a private swap; reuses `save_all` (which already preserves the `0600` mode).
- `src/universal_remote/tui/devices_screen.py` — button row in `compose`, two actions, two bindings, and `_reload` gains an optional "keep this device highlighted" argument. Existing `_reload` callers (`action_delete`, `on_screen_resume`) keep today's snap-to-top behaviour.
- `src/universal_remote/tui/app.py` — CSS for the new button row.
- `src/universal_remote/tui/device_option_list.py` — **unchanged**. The widget is shared with the Use Remote picker, so the reorder bindings must live on `DeviceListScreen`, not on the widget.
- No change to `Device`, to the on-disk schema, or to the `keyboard-shortcuts` action catalog (the Manage Devices keys `a`/`e`/`backspace` are already screen-local rather than catalogued; the new keys follow that precedent).
- Layout risk: the button row costs vertical space on the supported 80×24 terminal, under a 5-line banner plus Header and Footer. Needs a visual check, not just a passing test.
