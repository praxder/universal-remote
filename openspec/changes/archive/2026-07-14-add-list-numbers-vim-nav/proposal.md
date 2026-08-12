## Why

Selecting a device today means arrowing through a list and pressing Enter. On the device lists a quick numeric shortcut is faster, and keyboard-first users expect Vim-style `hjkl` movement everywhere the arrow keys already work.

## What Changes

- Device lists (Manage Devices and the Use Remote picker) prefix each saved device with a `1.`, `2.`, `3.`… number.
- Pressing a digit `1`–`9` on those screens immediately opens the device at that position — editing it on Manage Devices, connecting/pairing on Use Remote. Out-of-range digits do nothing.
- The `+ Add` row stays unnumbered and keeps its Enter/click behavior.
- `hjkl` navigates menus and lists alongside the arrow keys: MenuScreen, both device lists, and the delete-confirmation dialog. Mapping mirrors the existing arrows (`k`/`h` = previous, `j`/`l` = next).
- On the remote surface, `hjkl` drives the D-pad (`h`=LEFT, `j`=DOWN, `k`=UP, `l`=RIGHT) in addition to the arrow keys. **BREAKING** the keyboard HOME shortcut moves off `h` onto the Space bar; the on-screen Home button is unchanged.
- The add/edit device form is left as-is — arrow keys move between fields so typed letters (including `h`/`j`/`k`/`l`) still fill the inputs.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `tui-remote`: device-management and Use-Remote lists gain numbered rows and digit selection; menu/list navigation gains `hjkl`; the remote's keyboard control changes so `hjkl` drives the D-pad and Space (not `h`) sends HOME.

## Impact

- `src/universal_remote/tui/devices_screen.py` — numbered rows + digit select + `hjkl` on the device list; delete-confirm dialog gains `hjkl`.
- `src/universal_remote/tui/remote_flow.py` — numbered rows + digit select on the Use Remote picker.
- `src/universal_remote/tui/menu.py` — MenuScreen gains `hjkl`.
- `src/universal_remote/tui/remote_screen.py` — `hjkl` D-pad bindings; HOME rebound from `h` to Space.
- Possible shared OptionList subclass for the numbering/digit-select/`j`k` behavior common to the two lists.
- No API, dependency, or store changes.
