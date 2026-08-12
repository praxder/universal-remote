## Why

On Google TV / newer Android TV, the "Use the keyboard on your mobile device" IME overlay silently swallows text sent over the Remote v2 protocol (`androidtvremote2.send_text` returns cleanly, IME counters populate, but nothing is typed). This makes remote text entry fail on the launcher search and any app that raises that overlay. ADB `input text` injects through Android's InputManager — the same path as a physical keyboard — and lands text even with the overlay up. The fix is to let a device route text over ADB while keeping the snappy Remote v2 path for everything else.

## What Changes

- Add an **opt-in ADB text path** to the existing Android TV adapter. Keys, discovery, and PIN pairing stay on Remote v2; only text is routed over ADB when a device opts in.
- Add a persisted per-device flag so a device remembers it should send text over ADB.
- Add a text-input-mode toggle on the Add/Edit device screen, shown only for Android TV: switching it to ADB guides the user to enable Developer options → Wireless debugging → "Pair with code", collects the pairing address and code, and runs the one-time `adb pair`; the opt-in is recorded when the form is saved.
- Route text at send time: opted-in devices send `input text` over the system `adb` binary; all others keep using Remote v2 `send_text`.
- Fall back to Remote v2 `send_text` (with a status note) when an opted-in device's ADB path is unavailable (adb binary missing, or wireless debugging off), so app-field text still works.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `androidtv-adapter`: text input gains an optional ADB path. When a device is opted in, the adapter sends text via the `adb` binary (`input text`) instead of Remote v2, resolving the device's ephemeral wireless-debugging address via mDNS each session, and falls back to Remote v2 when ADB is unavailable.
- `tui-remote`: adds an Android-TV-only text-input-mode toggle on the Add/Edit device screen; switching it to ADB performs the one-time `adb pair` and records the opt-in on save.

## Impact

- **Code**: `src/universal_remote/adapters/androidtv.py` (text routing), new `src/universal_remote/adapters/adb_text.py` seam (wraps the `adb` binary), `src/universal_remote/devices/models.py` (new `text_via_adb` field), TUI (Add/Edit text-input-mode toggle + pairing prompts).
- **Dependencies**: requires the external `adb` binary (Android platform-tools) on the host for the ADB text path only. No new pip dependency — `adb-shell` cannot do the Android 11+ wireless-debugging pairing flow, so the design shells out to `adb`.
- **Persistence**: `devices.json` gains an optional `text_via_adb` field; backward-compatible (`Device.from_dict` already ignores unknown keys and the field defaults to `False`).
- **User setup**: opted-in devices require Developer options + Wireless debugging to remain enabled; the connect port is ephemeral and re-resolved via mDNS.
