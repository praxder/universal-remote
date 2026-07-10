## Context

`DeviceListScreen` (`src/universal_remote/tui/devices_screen.py`) binds deletion to the `delete` key and runs `action_delete` inline: it resolves the highlighted device and calls `store.delete(id)` immediately. Two problems: (1) Textual's `delete` key is forward-delete, which most keyboards — Mac especially — do not surface on the large ⌫ key that users press; that key is `backspace`. (2) There is no confirmation, so an accidental press permanently removes a device.

The codebase has no modal/dialog pattern yet; `AddDeviceScreen` is a full `Screen`, not a modal. This change introduces the first `ModalScreen`.

## Goals / Non-Goals

**Goals:**
- Trigger device deletion with Backspace instead of the forward-delete key.
- Require explicit confirmation before a device is removed.
- Keep the storage layer unchanged — `store.delete` stays unconditional; confirmation is UI-only.

**Non-Goals:**
- No undo/trash mechanism after confirmed deletion.
- No change to add/edit flows, the store, or the `device-management` spec.
- No bulk/multi-select deletion.

## Decisions

**Rebind `delete` → `backspace`.** Change the binding tuple at `devices_screen.py:35` from `("delete", "delete", "Delete")` to `("backspace", "delete", "Delete")`. The action name and footer label stay `delete`/`Delete`; only the trigger key changes. Alternative — binding both keys — rejected: keeping the wrong key invites the same accidental-delete surprise the confirmation is meant to prevent, and the point is to match the physical key users press.

**Confirmation via a `ModalScreen[bool]`.** Add a small `ConfirmDeleteScreen(ModalScreen[bool])` that shows the device name and Confirm/Cancel buttons (Cancel focused by default). `action_delete` resolves the selected device, returns early if none (add row highlighted), then pushes the modal with a callback that calls `store.delete(id)` + `_reload()` only when the result is `True`. Using the modal's typed dismiss result keeps the delete decision in one place. Alternative — a synchronous `push_screen_wait` — rejected: `action_delete` is a plain action method, and the callback form is the idiomatic Textual pattern and simpler to test with the pilot.

**Escape / Cancel both dismiss as "no".** The modal binds Escape to cancel so the prompt behaves like the rest of the app (Escape = back/cancel), returning `False`.

**Render as a centered pop-up over the list, not a full page.** `ConfirmDeleteScreen` stays a `ModalScreen` — the device list remains mounted beneath it. The only reason it currently reads as a whole new page is styling: with no background/box rules the container fills the opaque screen. Add app-level CSS (matching the existing `app.py` `CSS` convention) giving the modal a translucent background so the list dims through, and a fixed-width bordered `$surface` box for the dialog. Alternative — mounting the dialog as a widget inside `DeviceListScreen` — rejected: it would lose modal input capture and is a larger structural change for a purely visual ask.

**Arrow-key navigation + default focus on Cancel.** Add screen-level bindings mapping up/left → focus previous and down/right → focus next (delegating to Textual's `focus_previous`/`focus_next`), covering whichever arrow the user reaches for without changing the button layout. Focus the cancel button on mount so a destructive action never starts on Confirm. Alternative — a `Horizontal` button row + single axis — rejected as gold-plating; the vertical layout with both axes bound is simpler and matches user expectation.

## Risks / Trade-offs

- [Existing tests press `delete` and assume immediate removal] → Update `tests/test_tui_devices.py`: press `backspace`, then drive the confirmation (confirm to delete, cancel to keep). Add coverage for the cancel path and the add-row no-op.
- [First modal in the codebase — styling/focus could feel inconsistent] → Keep the modal minimal (label + two buttons), mirror existing widget usage; no new dependencies.
- [Backspace may be intercepted elsewhere when a list row is focused] → The binding lives on `DeviceListScreen` and the `OptionList` does not consume Backspace, so the screen-level binding fires; verify with a pilot test.
