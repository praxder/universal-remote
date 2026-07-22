## Why

The Settings screen ships a disabled "Key Bindings (coming soon)" row. Keyboard-first users want to remap the app's hotkeys — and several remote keys (Volume, Channel, Mute, Menu, media transport) have no keyboard shortcut at all today, only clickable buttons. This change makes the pending feature real: a screen where every rebindable action's shortcut can be viewed and changed.

## What Changes

- A new **Keyboard Shortcuts** screen, reached from Settings (the "coming soon" row becomes live). It lists every rebindable action in one table — `Action | Shortcut` — where the shortcut may be blank.
- Pressing Enter on a row opens a **capture modal** ("press a key"); the next keypress becomes that action's shortcut. Delete or Escape in the modal **clears** the shortcut (back to none).
- A rebindable **action catalog** across three scopes:
  - **Home**: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`).
  - **Global**: Go Back (`escape`) — the app-wide back-a-page action, unified across every screen (on the remote it also closes the session).
  - **Remote**: all 29 remote keys plus Text entry (`t`). The 12 click-only keys (Vol±, Ch±, Mute, Menu, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) start with **no** shortcut and become assignable.
- **Scope-aware conflict rejection**: assigning a key already taken by another action that can be active on the same screen is refused — the shortcut is **not** set and a toast reports "`<key>` is already taken by `<Action>`". Home and Remote actions never share a screen, so they may reuse a key; Go Back (active everywhere) must not collide with a Remote key.
- **Reserved keys**: a new assignment to a key owned by non-rebindable machinery — focus navigation (arrow keys and `h`/`j`/`k`/`l`), Enter (activate the focused control), and the command palette (`ctrl+p`) — is refused with a toast. Existing default bindings are exempt (e.g. Remote Up legitimately defaults to the Up arrow).
- Changes take effect **immediately**: on save, the bindings of every mounted screen are rebuilt so the new shortcut works without a restart.
- Custom shortcuts **persist** in the existing preferences file (`settings.json`) as a `shortcuts` map of action id → key, loaded and applied at startup.

## Capabilities

### New Capabilities

- `keyboard-shortcuts`: the rebindable action catalog (ids, labels, scopes, default keys), the Keyboard Shortcuts screen and key-capture modal, key normalization, scope-aware conflict and reserved-key rejection with a toast, and live application of custom shortcuts to the running screens.

### Modified Capabilities

- `tui-settings`: the "Key Bindings" placeholder row becomes a working "Keyboard Shortcuts" row that opens the new screen.
- `app-preferences`: the preferences file gains a persisted `shortcuts` map (action id → key) alongside the theme, loaded at startup and applied to the app's bindings.
- `tui-remote`: the documented home, remote, and back key mappings become **defaults** that the user may rebind via `keyboard-shortcuts`; the click-only remote keys become assignable; and the app-wide Escape "back a page" is exposed as the customizable Go Back action.

## Impact

- New `src/universal_remote/tui/shortcuts.py` (or a `shortcuts/` package) — action catalog + effective-binding resolution.
- New `src/universal_remote/tui/shortcuts_screen.py` — the table screen and the key-capture modal.
- `src/universal_remote/tui/settings_screen.py` — enable the row; push the new screen.
- `src/universal_remote/tui/menu.py` — home action bindings (d/r/s/q) built from the catalog.
- `src/universal_remote/tui/remote_screen.py` — remote key + text bindings built from the catalog; the 12 empty keys become assignable.
- `src/universal_remote/tui/devices_screen.py`, `discover_screen.py`, `remote_flow.py`, `remote_screen.py` — unify the per-screen `escape`/`exit_remote` back handlers under the single Go Back action.
- `src/universal_remote/preferences/store.py` — add a `shortcuts` field to `Preferences` and the JSON read/write.
- `src/universal_remote/tui/app.py` — load and apply saved shortcuts on mount; live-rebuild bindings across the screen stack on save.
- No new dependencies; no device-adapter or `Key` vocabulary changes.
