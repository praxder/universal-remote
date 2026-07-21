## Context

`AddDeviceScreen` in `src/universal_remote/tui/devices_screen.py` serves both Add and Edit (distinguished by `self._existing`). Delete already exists: `DeviceListScreen.action_delete` (Backspace) pushes `ConfirmDeleteScreen`, and on confirm calls `self.app.store.delete(device.id)` then `_reload()`. This change adds a second entry point to that same machinery from the edit screen. No new store, model, or dialog code.

## Goals / Non-Goals

**Goals:**
- A Delete button on the edit screen, below Save, that removes the device after the existing confirmation and returns to the device list.
- Button appears only when editing; never when adding.
- Button reachable via Tab and Up/Down like the other cells.

**Non-Goals:**
- Changing the list's Backspace delete or the `ConfirmDeleteScreen` dialog.
- New delete-without-confirmation path.
- Restyling the Save button or the form layout beyond adding the Delete button.

## Decisions

- **Reuse `ConfirmDeleteScreen`, not a new dialog.** Same prompt, same cancel-default focus, same arrow-key nav — DRY and consistent with the list-screen delete. Alternative (inline confirm on the edit screen) rejected: duplicates behavior and diverges from the list.
- **Edit-only button, added in `compose`.** Yield the Delete button only when `self._existing is not None`, so Add never renders it and no runtime hide/show is needed. `variant="error"` (red), same left alignment as Save.
- **Post-confirm: `store.delete` then `pop_screen()`.** The callback passed to `push_screen(ConfirmDeleteScreen(...), cb)` fires on dismiss; on confirm it deletes and pops the edit screen. The list's `on_screen_resume` already calls `_reload()`, so the list refreshes without the device — no extra wiring. On cancel the callback does nothing and the user stays on the edit screen.
- **Focus/nav via existing `focus_previous`/`focus_next`.** The screen already routes Up/Down to `focus_previous`/`focus_next`; a new focusable Button joins the order automatically. Save stays the initial focus target; Down from Save reaches Delete.

## Risks / Trade-offs

- [Delete button steals the Enter default on the edit screen] → It is placed after Save and Save keeps initial focus; only an explicit move to the Delete button (Tab/Down/click) then Enter deletes.
- [User confuses Delete on the edit screen with cancelling the edit] → Confirmation prompt names the device and defaults focus to Cancel, so an accidental activation is recoverable.
