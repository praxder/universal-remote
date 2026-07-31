## Context

Device order is already implicit in `devices.json`: `DeviceStore.list()` returns `Device.from_dict` over the `devices` array in file order, and nothing in `src/` sorts devices — there is no `sorted(` call anywhere in the package. Both consumers enumerate that list and number the rows from the enumeration index:

- `tui/devices_screen.py:73` — the Manage Devices list
- `tui/remote_flow.py:144` — the Use Remote picker

Every writer preserves order: `add` appends, `update` maps in place, `delete` filters, and discovery saves through `store.add` (`tui/discover_screen.py:117`). Both screens are pushed fresh on each visit (`tui/menu.py:80,83`), so neither can show a stale order.

So the change is small: swap two array slots, `save_all`, and rebuild the list. The interesting constraints are in the TUI.

## Goals / Non-Goals

**Goals:**

- Reorder the saved-device list from Manage Devices, by button and by key, and persist it.
- Highlight follows the moved device so repeated moves walk it several places.
- The Use Remote picker and the `1`–`9` digit shortcuts pick up the new order with no work of their own.

**Non-Goals:**

- No drag-and-drop, no "move to top", no numeric jump-to-position.
- No sorting modes (alphabetical, by reachability, most-recently-used).
- No reordering from the Use Remote picker — it stays read-only with respect to order.
- No new field on `Device` and no on-disk schema change.
- The new keys are not added to the rebindable action catalog.

## Decisions

### Order stays implicit in the array; no `position` field

A `position: int` on `Device` would need normalising on load, gap handling on delete, and a sort on every read — and would let the file order and the field disagree. The array is already the single source of truth, and the migration story is "none": existing files load unchanged and are already in *some* order.

*Alternative considered:* explicit `position`. Rejected as YAGNI, and as a second source of truth for the same fact.

### `move_up` / `move_down` on `DeviceStore`, over a private swap

Mutation belongs in the store, matching `add`/`update`/`delete`, so the reorder can be tested without a TUI harness. Two named methods read better at the call site than `move(id, delta)`; both delegate to one private swap that finds the index, returns early when the target index is out of range or the id is unknown, and otherwise swaps and calls `save_all`.

Returning early *before* `save_all` skips a pointless rewrite of the file, but that is an implementation choice, not a requirement: the spec only asserts that the stored order is unchanged, which is what a caller can actually observe. Do not write a test that spies on `save_all` to prove the file was left alone — a swap-with-itself would produce byte-identical output anyway, so there is no user-visible difference to assert on.

`save_all` already re-`chmod`s to `0600`, so the secret-bearing file keeps its permissions with no extra care here.

*Alternative considered:* a `reorder(ids: list[str])` that takes the whole order. More general, more ways to be wrong (missing or unknown ids), and nothing needs it.

### Bindings live on `DeviceListScreen`, never on `DeviceOptionList`

`DeviceOptionList` is shared with the Use Remote picker (`remote_flow.py:138`). Putting `shift+up`/`shift+down` on the widget would silently make the picker reorderable, contradicting the spec. `OptionList` binds `up`/`down` but not the shifted variants, so the key event bubbles from the focused list up to the screen and the screen's binding fires. The widget file is untouched.

`shift+up` / `shift+down` were chosen over `[`/`]` because "shift-arrow moves the thing" is the editor convention, and because the list already spends `up`/`down`/`h`/`j`/`k`/`l`/`1`–`9` on navigation and selection.

`K` and `J` are bound as aliases, hidden from the footer with `show=False`. The tui-remote capability already requires Vim parity for arrow-key navigation on both device lists (`tui-remote` spec.md:334), and every arrow affordance in this application has a Vim counterpart; an arrow-only reorder would be the one exception. Uppercase letters arrive as their own key names in Textual, so they do not collide with the widget's lowercase `j`/`k` cursor movement.

### `_reload` gains an optional keep-highlighted id

`_reload()` ends with `option_list.highlighted = 0` (`devices_screen.py:80`), so calling it after a move would snap the highlight to the top and make a second move impossible. It becomes `_reload(select_id: str | None = None)`: when an id is given, highlight the index of the device with that id after rebuilding; otherwise keep today's snap-to-0. `action_delete` and `on_screen_resume` pass nothing and behave exactly as before.

The highlight follows the *device*, not the position — that is what makes "press Move Down twice" work.

### The move actions guard through `_selected()`

`_selected()` (`devices_screen.py:82`) already returns `None` when the highlight is on the `+ Add` row, because it looks the option id up against the store. The move actions return early on `None`, which covers the add row and the empty-list case in one check without a new predicate. The remaining boundary (first/last) is the store's early return. So "silent no-op" needs no dedicated boundary code in the screen.

The separator needs no handling at all: Textual 8.2.8 keeps `OptionList._options` as a `list[Option]` and `validate_highlighted` clamps against `len(self.options)`, so `add_option(None)` does not occupy an index and `highlighted` can never land on it. This is why the existing "Backspace on the add entry does nothing" scenario names only the add entry — and why the new move scenarios do the same.

### Buttons stay enabled; no toast

Disabling per-highlight would need `on_option_list_option_highlighted` wiring, re-evaluation on every cursor move, and its own tests, to prevent a press that already does nothing. And no confirmation toast: the row visibly moves and the numbers change, which is the feedback.

## Risks / Trade-offs

- **Vertical space on 80×24** → The button row sits under a 5-line banner, Header, and Footer. Two known Textual traps apply: a `1fr` `OptionList` renders blank on a short terminal unless `border: none` is set, and `Button` clamps to `min-width: 16` unless `min-width: 0` is also set. Verify with a real screenshot at 80×24, not only a test with an oversized viewport.
- **Footer hint count** → The screen shows Add, Edit, Delete plus the global Go Back; two more hints makes six, under the ~8 that fit at 80 columns. If the footer clips, hide the two new hints with `show=False` and rely on the buttons for discoverability.
- **`shift+up` / `shift+down` terminal support** → Both are standard CSI sequences that Textual decodes, but a terminal that swallows them would leave the keys dead. The buttons are the primary affordance and remain fully functional, so the failure mode is degraded, not broken.
- **Uncatalogued keys are invisible to conflict detection** → A user could rebind a catalogued action onto `shift+up`. This is already true of this screen's `a`, `e`, and Backspace, so the change adds no new class of problem; catalogueing the moves would mean a new surface in the keyboard-shortcuts capability for two keys.
- **Highlight after a `+ Add`-row press** → With the highlight on the add row a move does nothing, including not moving the highlight, so a user pressing `shift+down` there sees no response at all. Accepted: it matches Backspace's existing behaviour on that row.

## Migration Plan

None. Existing `devices.json` files load unchanged in whatever order they already hold, which becomes the initial user-visible order. Rollback is a code revert; a file written after a reorder is schema-identical to one written before it.

## Open Questions

None outstanding.
