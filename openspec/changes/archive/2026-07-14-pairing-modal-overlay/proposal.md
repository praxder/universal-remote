## Why

Pairing currently replaces the whole screen with a full-page view (Header, Footer, and body), while connecting to a device already shows as a modal spinner overlaid on the device selection. The two steps of one flow look inconsistent, and the full-page pairing view loses the context of the device the user just picked. Presenting pairing as a modal overlay makes the flow feel continuous and matches the connecting-spinner treatment.

## What Changes

- Present the pairing guidance — both the initial "Accept the authorization popup on your TV." state and the "Enter the PIN shown on your Apple TV" PIN-entry state — as a modal dialog overlaid on the device selection, instead of as a full-screen page.
- The pairing dialog dims the device selection behind it and shows in a centered bordered box, mirroring the existing connecting-spinner modal.
- No change to pairing behavior: guidance text, the PIN prompt/input, submit, and cancel all work exactly as before.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-remote`: The "Use Remote entry, selection, and pairing" requirement changes so that pairing guidance is presented as a modal overlaid on the device selection (rather than being silent on presentation / implying a full-screen page), reusing the connecting-spinner overlay language.

## Impact

- `src/universal_remote/tui/remote_flow.py`: `PairingScreen` converts from `Screen` to `ModalScreen`; drops `Header()`/`Footer()`.
- `src/universal_remote/tui/app.py`: add backdrop + box CSS for `PairingScreen`/`#pairing`, mirroring `ConnectingModal`.
- No adapter or store changes. Existing pairing behavior tests remain the regression net.
