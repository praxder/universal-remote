## Why

Ctrl+C — the reflex every terminal user has for "get me out of here" — does not quit this app. Textual binds it to a `help_quit` action that only shows a "Press Ctrl+Q to quit the app" toast, and because that binding is not a priority binding it does not even reach the user inside a modal, while a text field consumes it as Copy. The user has to learn a second key to leave an app that already looks like it should answer to the first one.

## What Changes

- Ctrl+C SHALL quit the application immediately on a single press, from any screen, while any modal is open, and while a text input or text area has focus. The "Press Ctrl+Q to quit" toast is gone.
- Ctrl+Q keeps working as it does today; it is now documented as the alternate quit key rather than the only one.
- Ctrl+C and Ctrl+Q become **reserved** keys in the shortcut catalog: they appear as one fixed "Quit (Any Screen)" row in the Keyboard Shortcuts table reading `CTRL-C / CTRL-Q`, cannot be assigned to a device action, and any previously saved override that used one of them is dropped on load (the action reverts to its default).
- Quitting while the remote is open now closes the live device session. Previously only Go Back closed it, so leaving by any other route left the adapter's HTTP client session open and aiohttp printed `Unclosed client session` to the terminal after the app exited. (Pre-existing with Ctrl+Q; binding Ctrl+C makes it easy to hit.)
- **BREAKING** (minor, deliberate): Ctrl+C no longer copies inside a text input or text area. Copying there falls back to the terminal emulator's own copy (select with the mouse, then Cmd+C) — the widget's `super+c` binding is not a reliable substitute, because macOS terminals bind Cmd+C themselves and do not forward it to the application.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keyboard-shortcuts`: a new requirement that Ctrl+C exits immediately from anywhere; the catalog, table, and reserved-key requirements grow to cover the quit entry; and the readable-form requirement generalizes its "primary key / alias" rule from the D-pad rows to any reserved row with aliases.
- `tui-remote`: a new requirement that the remote releases its device session whenever it is torn down, quitting included.
- `app-error-handling`: the "Ctrl-C still quits" scenario under the interrupt-passthrough requirement asserts something that was never true — Textual consumes Ctrl+C as a key event, so no `KeyboardInterrupt` is ever raised. The requirement is corrected to be about exception passthrough only, and the quit claim moves to the keyboard-shortcuts capability where the binding lives.

## Impact

- `src/universal_remote/tui/app.py` — `UniversalRemoteApp` gains a `BINDINGS` entry for `ctrl+c`.
- `src/universal_remote/tui/remote_screen.py` — `RemoteScreen.on_unmount` closes the live session, so every teardown route releases it; the close is bounded by `CLOSE_TIMEOUT` and logged rather than raised, because it runs during shutdown outside the app's error net.
- `src/universal_remote/tui/shortcuts.py` — one reserved framework entry in `CATALOG` covering both quit keys, which feeds `RESERVED_KEYS`, the capture-modal refusal path, `without_reserved`, and the Keyboard Shortcuts table.
- Text entry surfaces lose Ctrl+C-to-copy: the inline-script text area and the device name/host, PIN, macro name, and custom-label inputs. Terminal-level copy is unaffected.
- No dependency, storage-format, or adapter changes.
