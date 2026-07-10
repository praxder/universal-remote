## Context

`DeviceListScreen` (`src/universal_remote/tui/devices_screen.py`) currently composes a `Label("Manage Devices")`, an `OptionList` of device rows, and a `Label` empty-state hint. Add is reachable only via the `a` binding; edit via `e` and delete via `delete`, both keyed off `OptionList.highlighted`. There is no `OptionSelected` handler, so pressing Enter or clicking a row does nothing today.

## Goals

- Banner reads "Devices" in ASCII art, matching `MenuScreen.TITLE_ART`.
- Add is always the last row of the list, discoverable on first run.
- Selecting the add row opens add; selecting a device row edits it.

## Decisions

### Add is an `OptionList` row, not a separate `Button`

Making add a row in the same `OptionList` unifies the empty and populated states (one widget, one selection model) and matches the requested "always the last row" / "cell" framing. A separate `Button` would need a `Rule` between it and the list and a second focus target. Rejected for extra surface with no benefit.

### List composition in `_reload()`

Rebuild on every reload (mount + `on_screen_resume`), same as today:

```
devices = store.list()
for d in devices: add_option(Option(d.name, id=d.id))
if devices: add_option(Separator())        # separator only when devices exist
add_option(Option("+ add", id=ADD_ID))     # ADD_ID = "__add__" sentinel
highlighted = 0
```

- **First run** → list is `[add]`, no separator.
- **≥1 device** → `[dev…, Separator, add]`.
- `highlighted = 0` always (was gated on `devices` before; now there is always at least the add row).

Sentinel id `"__add__"` cannot collide with a `Device.id` (store ids are generated tokens). `Separator` is non-selectable and skipped by keyboard navigation, so it never becomes `highlighted`.

### Selection handler

```
def on_option_list_option_selected(self, event):
    if event.option.id == ADD_ID:
        self.action_add()
        return
    device = next((d for d in store.list() if d.id == event.option.id), None)
    if device is not None:
        self.app.push_screen(AddDeviceScreen(existing=device))
```

`OptionList` emits `OptionSelected` on both Enter and mouse click, so both interactions are covered by one handler. The `e` binding stays; `action_edit()` keys off `highlighted`, which selection also sets, so both paths agree.

### Edit/delete safety on the add row

`_selected()` returns `next(d for d in store.list() if d.id == option.id)`. For the add row (`__add__`) that yields `None`, and `action_edit`/`action_delete` already guard with `if device is not None`. No extra guard needed; confirm with a test rather than adding code.

### Banner

Replace the `Label` with a `Static` (multiline art must not be a single-line `Label`), id `#devices-title`, pinned in `app.py` CSS to a fixed width so it never wraps — mirroring `#title { width: 42 }`. Art (figlet, standard font):

```
 ____             _
|  _ \  _____   _(_) ___ ___  ___
| | | |/ _ \ \ / / |/ __/ _ \/ __|
| |_| |  __/\ V /| | (_|  __/\__ \
|____/ \___| \_/ |_|\___\___||___/
```

Widest line is 34 columns → `#devices-title { width: 36; text-align: center; }`.

## Risks

- Low. Single screen, no store/adapter changes. Existing `test_tui_devices.py` asserts device prompts are present in `#device-list`; the add row and separator are additive and don't break those assertions.
