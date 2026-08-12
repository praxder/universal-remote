## Why

The Add/Edit Device screen presents its fields bottom-up relative to how a user thinks about a device (they pick the brand first, then name it, then give its address), shows raw kebab-case platform ids in the type dropdown, and can only be traversed with Tab. This change reorders the form, humanizes the platform labels, keeps the device type visible (read-only) while editing, and lets the arrow keys move between fields — small refinements that make adding a device feel natural.

## What Changes

- Reverse the on-screen field order to **device type first, then Name, then IP address**.
- The device-type dropdown SHALL display **user-friendly labels** ("Samsung Tizen", "LG WebOS") while still storing the platform id ("samsung-tizen", "lg-webos"). Each adapter declares a human-readable `display_name` on the adapter seam.
- In the **edit** flow, show the device type as a **read-only** first cell (the platform is fixed once paired); Name and IP stay editable.
- The device-type cell, Name, IP, and the Save button SHALL be navigable with **Up/Down arrow keys** in addition to Tab (Up = previous, Down = next). Left/Right remain in-field text-cursor movement inside the inputs.
- The **Save** button gains left padding so its left edge matches the indent of the cells above it.
- Restore the delete-confirmation requirement text and scenarios to the `tui-remote` "Device management screens" requirement (dropped by a prior change's archive though the behavior still exists in code). Spec-only; no code change.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `tui-remote`: the Add/Edit Device screen orders its cells device-type → Name → IP; the device type is a read-only cell when editing; the device-type dropdown shows human-readable labels; the cells and Save button are reachable with the Up/Down arrow keys as well as Tab; Save is left-aligned with the cells above it. Also restores the delete-confirmation requirement text and scenarios that a prior archive dropped.
- `device-management`: when adding a device, the platform choices are offered as human-readable labels while the stored value remains the platform id.
- `samsung-tizen-adapter`: the adapter declares a human-readable display name ("Samsung Tizen").
- `lg-webos-adapter`: the adapter declares a human-readable display name ("LG WebOS").

## Impact

- **Source**: `adapter.py` (add `display_name` to the `Adapter` protocol), `adapters/samsung.py`, `adapters/lg.py` (declare `display_name`), `registry.py` (expose registered adapters for label/value pairing), `tui/devices_screen.py` (field order, read-only edit cell, friendly dropdown options, arrow-key bindings), `tui/app.py` (Save-button CSS).
- **Tests**: `tests/fakes.py` (`FakeAdapter.display_name`), `test_tui_devices.py` (field order, read-only edit cell, friendly labels, arrow navigation), `test_registry.py` (adapter exposure) if applicable.
- **Data**: none. The stored `Device.platform` value is unchanged (still the id).
- **Dependencies**: none.
