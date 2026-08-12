## Context

`AddDeviceScreen` (used for both Add and Edit) saves unconditionally in `_save`: it reads name/IP, then calls `store.add(...)` or `store.update(...)` and pops the screen. `DeviceStore` has no uniqueness enforcement, and the screen has no mechanism to display an error — the codebase currently shows errors nowhere (only a confirm-delete `ModalScreen` exists). This change adds duplicate detection and the first inline error surface on that screen.

## Goals / Non-Goals

**Goals:**
- Block a save whose name or IP already belongs to a different saved device.
- Tell the user which field collided, and keep them on the screen to fix it.
- Make the collision rule unit-testable without driving the TUI.

**Non-Goals:**
- Validating IP format or reachability (no network probe; unchanged).
- Rejecting blank name/IP (existing behavior: blank name defaults to IP; out of scope).
- Normalizing IP representations (e.g. `10.0.0.5` vs `010.000.000.005`) — exact string match after trim.
- A general-purpose form-validation framework; one error label suffices.

## Decisions

### Detection lives on `DeviceStore`, not the screen
Add `find_conflict(name: str, ip: str, exclude_id: str | None = None) -> str | None`. It iterates saved devices, skips the device whose `id == exclude_id`, and returns a ready-to-show message for the first collision, or `None`.

- Name match: `d.name.strip().casefold() == name.strip().casefold()`.
- IP match: `d.ip.strip() == ip.strip()`.
- Name is checked before IP; the first hit wins (single message).

*Why:* keeps the rule where the data lives, so it is testable via `test_device_crud.py` with no Textual pilot. Returning the message (rather than a bool or an enum) keeps the screen dumb — it just displays whatever comes back. Alternative considered: raising an exception from `store.add/update`. Rejected — the screen must catch and stay put anyway, and add/update are also used by tests/other callers that would then need try/except.

### Case-insensitive name, exact IP
Names are human labels where `"Living Room"` and `"living room"` are the same device to a person, so `casefold()` after `strip()`. IPs are machine addresses; exact trimmed comparison avoids guessing at equivalent notations.

### Inline `Label` error, save stays on screen
Add `yield Label("", id="error")` between `#ip` and `#save`. In `_save`, compute the conflict first; if a message comes back, set the label text and `return` (do not add/update, do not pop). On a clean save, clear the label and pop as today. The label is recomputed on every save attempt, so fixing a field and re-saving clears a stale message.

*Why inline over toast/modal:* a toast is ephemeral and easy to miss; a modal is heavy for field validation and would need its own screen. An inline label sits with the fields the user is editing.

### Edit excludes self by `id`
`_save` passes `exclude_id = self._existing.id if self._existing else None`. Re-saving a device without changing its name/IP must not collide with itself; renaming onto another device still collides.

## Risks / Trade-offs

- [Blank name defaults to IP, so two blank-name devices compare their IPs-as-names] → Harmless: if IPs differ the names differ; if IPs match the IP rule already blocks the save. No extra handling.
- [Message text is produced by the store, coupling copy to the data layer] → Accepted; the strings are trivial and keeping the screen display-only is the larger win. Revisit only if localization is introduced.
- [Exact IP match lets `10.0.0.5` and `010.0.0.5` both save] → Accepted as a Non-Goal; IP-format normalization is out of scope.
