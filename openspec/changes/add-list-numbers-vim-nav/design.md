## Context

The TUI is built on Textual. Two screens list saved devices in a `OptionList`: `DeviceListScreen` (Manage Devices) and `UseRemoteScreen` (the Use Remote picker). Menu/list navigation today is arrow-key driven — `MenuScreen` and the dialogs bind Up/Down (and Left/Right) to focus movement, while the `OptionList` widget supplies its own Up/Down cursor movement. `RemoteScreen` is different: its buttons are `can_focus=False`, arrows are bound to *send D-pad keys to the device* rather than to move focus, and `h` is currently bound to send HOME.

This change is additive on the menus and lists (numbers and `hjkl` layered on top of existing behavior) and mildly breaking on the remote (the HOME hotkey moves from `h` to Space so `h` can drive the D-pad).

## Goals / Non-Goals

**Goals:**

- Number device rows `1.`, `2.`, `3.`… on both device lists and let digits `1`–`9` open the device at that position.
- Add `hjkl` navigation wherever the arrow keys already move through menu items or list rows.
- Make `hjkl` drive the remote D-pad, moving the HOME hotkey to Space.

**Non-Goals:**

- No multi-digit selection (10+ devices remain reachable by arrows only).
- No `hjkl` navigation on the add/edit form — typing must keep working there.
- No change to the device store, adapters, or any non-TUI code.

## Decisions

### Digit maps to option index N-1, not a store lookup

On both screens the saved devices occupy `OptionList` indices `0..n-1` at the top; any separator and the `+ Add` row come *after* them. So pressing digit `N` maps directly to option index `N-1` on both screens, with no dependence on the store or on how the trailing rows are laid out. The handler guards with `idx < device_count and option is not None and option.id != ADD_ID`, so an out-of-range or non-device digit is a silent no-op.

**Selection reuse:** rather than duplicate the open/connect logic, the digit handler sets `highlighted = N-1` and invokes the `OptionList` select action so the existing `on_option_list_option_selected` handler fires unchanged. This keeps a single selection path per screen.

**Alternative considered:** mapping the digit to `store.list()[N-1]` and calling the open/connect method directly. Rejected — it forks the selection logic into a second path and risks drifting from the Enter/click behavior.

### Number prefix is display-only; option `id` is untouched

Rows are built as `Option(f"{i + 1}. {device.name}", id=device.id)`. Both screens resolve the selected device by `option.id`, so prefixing the label leaves `_selected()` and both selected-handlers working without change. The stored device name is never altered.

### `hjkl` mirrors existing arrow semantics

Where focus navigation already exists (MenuScreen, ConfirmDeleteScreen), `k`/`h` alias the existing "previous" action and `j`/`l` alias "next" — the same mapping the Up/Left and Down/Right arrows already use, so no new movement logic is introduced. On the `OptionList` lists, `j`/`k` invoke the widget's built-in `cursor_down`/`cursor_up`. All aliases are declared `show=False` so the footer does not double up, mirroring the already-hidden Up/Down bindings on MenuScreen.

**Shared widget:** the numbering + digit-select + `j`/`k` behavior is identical on both lists, so it is factored into one `OptionList` subclass reused by both screens, keeping the two screens thin.

### Remote D-pad and the HOME move to Space

On `RemoteScreen`, `h`/`j`/`k`/`l` are bound alongside the arrows to `send('LEFT'|'DOWN'|'UP'|'RIGHT')`. The former `h`→HOME binding is replaced by `space`→`send('HOME')`. Space is safe here because the remote's buttons are non-focusable, so nothing consumes Space at the screen level; and while the text field is focused it consumes Space as typed input, exactly as it consumes letters — so HOME never fires mid-typing.

## Risks / Trade-offs

- **Textual key dispatch while a widget is focused** → The screen/subclass bindings for `j`/`k`/digits must fire while the `OptionList` holds focus. This already works today: `DeviceListScreen` binds `a`/`e`/`backspace` at screen level and they fire with the list focused. Low risk; confirmed by exercising the app.
- **Letters vs. text inputs** → On the add/edit form and the remote's text field, a focused `Input` consumes `h`/`j`/`k`/`l` and Space as typed characters, so those bindings never steal keystrokes mid-typing. This is the same mechanism that lets the form's Up/Down navigate while Left/Right edit the cursor.
- **10+ devices** → digits only reach the first nine; arrows still reach the rest. Acceptable for a personal device list.
- **HOME hotkey relearn** → users who pressed `h` for Home must relearn Space. Mitigated by the unchanged on-screen Home button and the footer hint.
