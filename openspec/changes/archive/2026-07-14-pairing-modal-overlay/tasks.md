## 1. Convert PairingScreen to a modal

- [x] 1.1 Change `PairingScreen` base class from `Screen[Device | None]` to `ModalScreen[Device | None]` in `src/universal_remote/tui/remote_flow.py`
- [x] 1.2 Remove `Header()` and `Footer()` from `PairingScreen.compose`; drop now-unused `Header`/`Footer` imports if no other screen in the file needs them
- [x] 1.3 Add backdrop + box CSS for `PairingScreen` / `#pairing` in `src/universal_remote/tui/app.py`, mirroring the `ConnectingModal` / `#connecting` rules (dim `$background 60%`, centered `thick $primary` bordered `$surface` box)

## 2. Verify

- [x] 2.1 Run the existing pairing behavior tests (`tests/test_tui_remote_flow.py`, `tests/test_pairing.py`) and confirm they pass unchanged
- [x] 2.2 Preflight: run formatter/linter and the full test suite
- [x] 2.3 Run the app and drive the Apple TV pairing flow to confirm the modal renders over the dimmed device selection in both the authorization-guidance and PIN-entry states
