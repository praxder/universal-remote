## Context

`PairingScreen` (`src/universal_remote/tui/remote_flow.py`) is a full-screen `Screen` yielding `Header()`, the pairing body, and `Footer()`. It is pushed onto the stack over `UseRemoteScreen`, fully hiding it. The sibling `ConnectingModal` in the same file is already a `ModalScreen` that dims the device selection behind a centered bordered box; its CSS lives in `app.py`. Both pairing states the user sees (authorization guidance, then PIN entry) are the *same* `PairingScreen` — the PIN group (`#pin-entry`) is revealed in place by `_prompt` when the adapter asks. So one conversion covers both states.

## Goals / Non-Goals

**Goals:**
- Render `PairingScreen` as a modal overlaid on `UseRemoteScreen`, matching `ConnectingModal`.
- Preserve all pairing behavior: guidance text, adapter PIN prompt/input, submit, cancel.

**Non-Goals:**
- No change to adapters, the store, or the pairing worker logic.
- No change to the connecting-spinner modal or any other screen.
- No new widgets or restructuring of the pairing body beyond removing the frame.

## Decisions

- **Convert `PairingScreen` from `Screen[Device | None]` to `ModalScreen[Device | None]`.** `push_screen`/`dismiss` semantics are identical for both; only rendering differs (opaque page vs dim-backdrop overlay). This is the minimal change that yields the desired presentation. Alternative — a separate modal wrapper delegating to the existing screen — adds a class for no benefit; rejected.
- **Drop `Header()` and `Footer()` from `compose`.** The sibling modals (`ConnectingModal`, `ConfirmDeleteScreen`) have neither; the frame is what makes it read as a full page. The Esc-to-cancel binding stays functional; losing the Footer hint is consistent with the other modals.
- **Add backdrop + box CSS mirroring `ConnectingModal`.** New rules: `PairingScreen { align: center middle; background: $background 60%; }` and a `#pairing` box (`width/height: auto; padding: 1 2; border: thick $primary; background: $surface;`). Existing `#pin-entry` and `#pairing #submit,#cancel` rules keep working inside the box.

## Risks / Trade-offs

- [Existing behavior tests query `#pairing-guidance` / `#pin-entry` / assert `isinstance(app.screen, PairingScreen)`] → all remain valid: the class name is unchanged and `ModalScreen` is still a screen on the stack. Tests are the regression net and should pass unmodified.
- [Visual-only change not captured by unit tests] → verify by running the app and driving the Apple TV pairing flow to confirm the modal renders over the dimmed device selection (per the verify skill).
