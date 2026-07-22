## Why

The Settings screen ships a disabled "Key Bindings (coming soon)" row. Keyboard-first users want to remap the app's hotkeys — and several remote keys (Volume, Channel, Mute, Menu, media transport) have no keyboard shortcut at all today, only clickable buttons. This change makes the pending feature real: a screen where every rebindable action's shortcut can be viewed and changed.

## What Changes

- A new **Keyboard Shortcuts** screen, reached from Settings (the "coming soon" row becomes live). It lists every action in one table — `Action | Shortcut` — **grouped under bold surface headings (Home / Global / Remote)** so the user can see which actions apply where; the shortcut may be blank, and reserved actions (the D-pad, Enter, the command palette) appear as **disabled rows** so users can see the keys are in use but fixed.
- Pressing Enter on a rebindable row opens a **capture modal** ("press a key"); the next keypress — **including Escape** — becomes that action's shortcut. The modal dismisses only three ways: pressing a key (assign), clicking a **Cancel** button (no change), or clicking a **DEL** button (clear the shortcut). Both buttons are mouse-only (they never take keyboard focus), so every keypress is captured as a shortcut — there is no keyboard cancel/clear path.
- Shortcuts are shown in a **readable form** (e.g. `CTRL-P`, `SPACE`, `ESC`) rather than raw internal key names.
- An **action catalog** of every rebindable action, grouped by the surface each is active on (this grouping only decides which screen binds which action — it does **not** scope conflicts):
  - **Home menu**: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`) — all rebindable.
  - **Everywhere**: Go Back (`escape`) — the app-wide back-a-page action, unified across every screen (on the remote it also closes the session), rebindable.
  - **Remote**: 26 rebindable actions — OK, Back, Home, digits 0–9, Text entry (`t`), and the 12 click-only keys (Vol±, Ch±, Mute, Menu, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) which start with **no** shortcut and become assignable — **plus** the four D-pad directional keys (Up/Down/Left/Right), which are **reserved** (fixed to the arrows with `h`/`j`/`k`/`l` aliases) and cannot be rebound.
- **Global conflict rejection**: every shortcut is unique across the whole app. Assigning a key already used by **any** other action is refused — the shortcut is **not** set and a toast reports "`<key>` is already taken by `<Action>`". A key maps to at most one action anywhere; there is no per-scope reuse.
- **Reserved keys**: the D-pad directional keys (arrows and `h`/`j`/`k`/`l`), Enter (activate the focused control), **Tab and Shift+Tab** (focus navigation), and the command palette (`ctrl+p`) cannot be assigned to any action, and they are **shown in the table as disabled rows** so users can see the keys are in use but fixed. A rebindable action's existing default is exempt (e.g. OK legitimately defaults to Enter).
- Changes take effect **immediately**: on save, the bindings of every mounted screen are rebuilt so the new shortcut works without a restart.
- Custom shortcuts **persist** in the existing preferences file (`settings.json`) as a `shortcuts` map of action id → key, loaded and applied at startup.
- The Keyboard Shortcuts screen gains an **ASCII-art banner header** matching the other screens' `TITLE_ART` banners, replacing the plain "Keyboard Shortcuts" text.
- The **command palette** (`ctrl+p`) gains a single "Keyboard Shortcuts" entry; selecting it closes the palette and opens a **read-only modal** listing every action and its current shortcut (no editing), so the user can check bindings from any screen.

## Capabilities

### New Capabilities

- `keyboard-shortcuts`: the rebindable action catalog (ids, labels, scopes, default keys), the Keyboard Shortcuts screen and key-capture modal, key normalization, scope-aware conflict and reserved-key rejection with a toast, and live application of custom shortcuts to the running screens.

### Modified Capabilities

- `tui-settings`: the "Key Bindings" placeholder row becomes a working "Keyboard Shortcuts" row that opens the new screen.
- `app-preferences`: the preferences file gains a persisted `shortcuts` map (action id → key) alongside the theme, loaded at startup and applied to the app's bindings.
- `tui-remote`: the documented home, remote, and back key mappings become **defaults** that the user may rebind via `keyboard-shortcuts` (except the D-pad directional keys, which stay **reserved** and fixed); the click-only remote keys become assignable; and the app-wide Escape "back a page" is exposed as the customizable Go Back action.

## Impact

- New `src/universal_remote/tui/shortcuts.py` (or a `shortcuts/` package) — action catalog + effective-binding resolution; **global** conflict detection (no `_OVERLAP`); Tab/Shift+Tab reserved entries.
- New `src/universal_remote/tui/shortcuts_screen.py` — the table screen (ASCII banner header) and the key-capture modal (Escape assignable; mouse-only Cancel and DEL buttons; more padding); plus a read-only shortcuts modal for the command palette.
- `src/universal_remote/tui/settings_screen.py` — enable the row; push the new screen.
- `src/universal_remote/tui/menu.py` — home action bindings (d/r/s/q) built from the catalog.
- `src/universal_remote/tui/remote_screen.py` — remote key + text bindings built from the catalog; the 12 empty keys become assignable.
- `src/universal_remote/tui/devices_screen.py`, `discover_screen.py`, `remote_flow.py`, `remote_screen.py` — unify the per-screen `escape`/`exit_remote` back handlers under the single Go Back action.
- `src/universal_remote/preferences/store.py` — add a `shortcuts` field to `Preferences` and the JSON read/write.
- `src/universal_remote/tui/app.py` — load and apply saved shortcuts on mount; live-rebuild bindings across the screen stack on save; register a command-palette `Provider` (`COMMANDS`) for the read-only shortcuts view.
- No new dependencies; no device-adapter or `Key` vocabulary changes.
