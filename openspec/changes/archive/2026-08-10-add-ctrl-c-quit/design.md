## Context

`UniversalRemoteApp` declares no `BINDINGS`, so it inherits Textual 8.2.8's App defaults:

```python
Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
Binding("ctrl+c", "help_quit", show=False, system=True),
```

`action_help_quit` only toasts "Press Ctrl+Q to quit the app". Two further framework details explain why the current behavior is worse than a mere toast:

- `App.on_event` runs the priority binding pass (`_check_bindings(key, priority=True)`) **before** forwarding the key to the focused widget, and that pass walks the full, untruncated binding chain including the App. The non-priority pass instead walks `Screen._modal_binding_chain`, which truncates at the first modal and therefore excludes the App. Textual's `ctrl+c` is not priority, so inside any modal it matches nothing at all — not even the toast.
- With an `Input` or `TextArea` focused, that widget's own `ctrl+c`→`copy` binding sits earlier in the chain and wins.

So the fix has to sit at the App level *and* be a priority binding; anything else leaves modals and text fields uncovered.

## Goals / Non-Goals

**Goals:**

- One Ctrl+C press exits, from any screen, inside any modal, and while a text field has focus.
- Ctrl+Q keeps working.
- Ctrl+C and Ctrl+Q cannot be silently shadowed by a user-assigned device shortcut.

**Non-Goals:**

- No double-tap / confirm-to-quit flow. Immediate quit is achievable, so building both would be waste.
- No `KeyboardInterrupt` handling in the CLI entry point. While the TUI runs, the terminal is in raw mode and Ctrl+C arrives as a key event, never as a signal.
- No footer hint for either quit key — the supported 80-column footer is already full.
- No confirmation prompt before exiting; the app persists preferences and device data as it goes.

## Decisions

**Bind `ctrl+c` → `quit` with `priority=True` on `UniversalRemoteApp.BINDINGS`.** This is the same mechanism Textual already uses for its own `ctrl+q`, with the key and action swapped, so it inherits behavior that is known to work inside modals. `DOMNode._merge_bindings` assigns per key while walking the MRO (`keys[key] = key_bindings`), so a subclass entry for `ctrl+c` *replaces* Textual's `help_quit` binding rather than stacking with it — the toast is gone, not merely outranked.

The chain filter that strips keys a focused widget would consume (`Screen._binding_chain`) only removes keys for which `check_consume_key` is true; `Input` and `TextArea` return true only for printable characters, so `ctrl+c` survives the filter and the priority pass reaches the App.

*Alternative rejected:* override `action_help_quit` to call `self.exit()`. Smaller, but it keeps Textual's non-priority `ctrl+c` binding, so it still never fires inside a modal and still loses to `Input`'s copy binding — it would fix only the case that already half-works.

**Catalog quit as one reserved framework entry** — `ctrl+c` with `ctrl+q` as a fixed alias (`target=None`, `editable=False`, `show=False`), alongside the existing `framework.command_palette` and focus-navigation entries. `RESERVED_KEYS` is derived from the fixed entries' keys *and* aliases, so one entry reserves both keys. That is what makes the capture modal refuse them and what makes `without_reserved` drop a stale saved override on load. Without it, a user can bind Ctrl+C to a device action, have it saved, and watch the priority binding silently shadow it — the same failure the `e` edit-mode key already caused once. `rebuild_shortcuts` skips entries whose `target` is `None`, so the entry is display-only and is never bound by us; the live Ctrl+C binding stays in `app.py`, and Ctrl+Q stays Textual's.

Both keys sit on one entry rather than two because the reserved D-pad rows already establish the primary-plus-alias shape, and `_shortcut_text` already renders it — the table shows a single "Quit (Any Screen)" row reading `CTRL-C / CTRL-Q`, instead of two identically labelled rows. Ctrl+Q is included at all because it is the identical case — a live framework quit key that is assignable to a device action today — so reserving one and not the other would make the reserved set look arbitrary.

## Risks / Trade-offs

- **Ctrl+C no longer copies in a text input or text area** → Accepted; it is the direct cost of quitting from anywhere. Copying falls back to the terminal emulator's own copy (mouse-select, then Cmd+C). The widgets' `super+c` binding is not a dependable substitute: macOS terminals bind Cmd+C themselves and generally do not forward it, so a keyboard-only selection cannot be copied from inside the app. Felt mainly in the inline-script text area and the device name/host, PIN, macro-name, and custom-label inputs.
- **A user who had assigned Ctrl+C or Ctrl+Q to a device action loses that shortcut** → The existing drop-on-load path handles it: the override is pruned, the action reverts to its default, and the cleaned set is persisted.
- **Textual could change its priority-pass ordering in a future release** → The tests press `ctrl+c` through `pilot.press`, which routes through `driver.send_message` → `App.on_event`, so an ordering regression fails the suite rather than shipping.
- **Tests alone cannot prove the tty path** → A prior change claimed Ctrl-C worked "verified by code reading" and was wrong. Verification therefore includes a real pty run that writes `\x03` and asserts the process exits.
