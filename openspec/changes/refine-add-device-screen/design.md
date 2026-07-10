## Context

`AddDeviceScreen` (`tui/devices_screen.py`) composes, top to bottom: the ASCII banner, an IP `Input`, a Name `Input`, a platform `Select` (add mode only), and a Save `Button`. The `Select` options come from `registry.platforms()` — a list of raw platform ids — built as `[(id, id)]` tuples, so the dropdown shows kebab-case ids. The `Adapter` protocol (`adapter.py`) exposes only `platform: str`. Focus moves solely by Tab (Textual default). Save is left-aligned with the input boxes at column 0.

## Goals / Non-Goals

**Goals:**
- Field order: device type → Name → IP address.
- Human-readable platform labels in the dropdown; stored value stays the platform id.
- Edit flow shows the device type as a read-only first cell.
- Up/Down arrows move focus between the cells and Save, alongside Tab.
- Save left-aligned to the same indent as the cells above it.

**Non-Goals:**
- No change to what is persisted (`Device.platform` remains the id).
- No editable platform while editing (a stored pairing credential is platform-specific).
- No Left/Right focus movement — those stay as in-field text-cursor keys.
- No change to the device list screen, pairing, connect, or the remote surface.

## Decisions

### `display_name` on the adapter seam
Add `display_name: str` to the `Adapter` protocol; Samsung declares `"Samsung Tizen"`, LG declares `"LG WebOS"`. The brand-friendly string lives with the brand code, keeping the UI and store brand-agnostic (consistent with `platform` already living on the adapter). The screen builds `Select` options as `(adapter.display_name, adapter.platform)` so the label is shown and the id is stored. Chosen over a UI-side id→label map (would re-encode brand knowledge in the UI) and over deriving the label from the id (title-casing `lg-webos` yields "Lg Webos", not "LG WebOS").

### Registry exposes adapters, not just ids
The screen needs both the display name and the id per platform. Add `AdapterRegistry.adapters() -> list[Adapter]` returning the registered adapters in registration order; keep `platforms()` for existing callers. The screen iterates `adapters()` to build the option tuples and defaults to the first.

### Read-only device type when editing
In edit mode, render the device type as a disabled `Input` whose value is the resolved `display_name` for `self._existing.platform` (looked up via `registry.resolve(platform).display_name`). A disabled widget is non-focusable, so it is automatically skipped by both Tab and the arrow-key focus chain — Name becomes the first focusable cell, matching the "read-only" intent. Chosen over a `Static` (a disabled `Input` matches the visual box of the other cells) and over a disabled `Select` (heavier; a single fixed value needs no dropdown).

### Up/Down arrow navigation
Bind `up → focus_previous` and `down → focus_next` on `AddDeviceScreen`; the action methods delegate to `self.focus_previous()` / `self.focus_next()`. Single-line `Input` widgets do not bind Up/Down (they use Left/Right/Home/End for the cursor), so Up/Down bubble to the screen and move focus without disturbing text editing. Left/Right are deliberately left unbound so they keep moving the in-field cursor. Note: a focused `Select` consumes Up/Down to open/navigate its own overlay, which is its expected behavior; Tab still moves off the `Select`, and Up/Down navigation is seamless across the text inputs and Save.

### Save alignment
The Save button's left padding/margin is set so its left edge lines up with the cells above it, verified against the live render (the exact value is confirmed by driving the screen and inspecting the layout, not copied from a guess).

## Risks / Trade-offs

- **[Select vs. arrow nav]** A focused `Select` captures Up/Down for its dropdown, so you cannot Up/Down directly off the `Select` — Tab does that. → Accepted: this is standard Select behavior and only the add flow has an editable Select; the text inputs and Save navigate fully by arrows.
- **[Read-only cell in focus chain]** If the read-only device-type cell were focusable, arrow/Tab nav would stop on a field the user cannot change. → Mitigated by using a disabled widget, which is skipped by focus traversal.
- **[Label/id drift]** Showing a label while storing an id risks confusion if they diverge. → The mapping is owned by the adapter and covered by adapter-spec scenarios; the stored value is asserted in tests.
