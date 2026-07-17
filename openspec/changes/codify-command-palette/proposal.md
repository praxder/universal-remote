## Why

Textual gives every app a built-in command palette (Ctrl+P). The app currently inherits it untouched, so it exposes commands the app does not want — "Maximize" (there is no keybinding to maximize any widget, so it is a dead end) and "Screenshot" (an SVG export irrelevant to end users). The palette's contents are also undocumented, so they can drift silently on a Textual upgrade. This change removes the two unwanted commands and pins the palette's exact contents in the spec.

## What Changes

- Remove the **Maximize** command from the command palette.
- Remove the **Screenshot** command from the command palette.
- Keep the remaining built-in commands: **Theme**, **Quit**, and **Keys**.
- Codify the exact set of command-palette entries as a spec requirement, so future changes to the palette are deliberate and any upstream drift is caught by a test.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `tui-remote`: Add a requirement fixing the command palette's contents to Theme, Quit, and Keys — explicitly excluding Maximize and Screenshot.

## Impact

- **Code**: `src/universal_remote/tui/app.py` — `UniversalRemoteApp` gains a `get_system_commands` override that filters the inherited commands. No other source touches the palette.
- **Tests**: A new test asserting the palette's command titles equal the expected set (and exclude Maximize/Screenshot), guarding against Textual upgrades reintroducing them.
- **Dependencies**: None. Behavior derives from Textual 8.2.8's `App.get_system_commands`.
- **User-facing**: The Ctrl+P palette no longer lists Maximize or Screenshot; the Minimize command (shown only while a widget is maximized) becomes unreachable in practice since nothing can maximize.
