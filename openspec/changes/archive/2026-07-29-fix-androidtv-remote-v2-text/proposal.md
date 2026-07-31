## Why

Android TV text was believed to be impossible over Remote v2 on Google TV's launcher search box, so the app grew an opt-in ADB text path to work around it — which forces the user to enable developer mode and wireless debugging, and collides with using `adb` for anything else (notably sideloading an app under test while the remote is connected).

The premise was wrong. Live protocol tracing against a Chromecast/Google TV (remote service 6.9.906821247, Android 14) shows text lands over Remote v2 on that exact surface with no ADB at all. `androidtvremote2`'s `send_text` builds two of the four batch-edit fields incorrectly, and it discards the inbound message that carries the state needed to build them correctly. Fixing that removes the entire reason the ADB path exists.

## What Changes

- Send Android TV text by building the Remote v2 IME batch edit from the device's live text-field state, instead of calling `androidtvremote2`'s `send_text`:
  - the edit's field counter comes from the counter the TV reports on its text-field status, re-read on every send
  - the edit's cursor span is the resulting cursor position — the current field contents plus the inserted text
- Track the focused text field's state by consuming the inbound IME show-request message the library currently drops as unhandled.
- Report text as unsupported when no text field is focused, rather than sending an edit that the TV silently discards.
- **BREAKING** Remove the Android TV ADB text path entirely: the per-device text-input opt-in flag, the ADB target resolution and pairing used only by that path, the Android-TV-only text-input-mode toggle and its pairing prompt on the Add/Edit Device screens, the post-add hint suggesting ADB text, and the "ADB text unavailable" status on the remote surface. Devices previously opted in silently return to Remote v2 text, which now works.
- Fire TV is untouched and keeps its own ADB path, including the shared `input text` command building and escaping.

## Capabilities

### New Capabilities

None. This corrects and simplifies existing behaviour.

### Modified Capabilities

- `androidtv-adapter`: text sending is redefined in terms of the Remote v2 IME batch edit built from live field state, with text reported unsupported when no field is focused; the opt-in ADB text routing, ADB target resolution, ADB fallback signalling, and one-time ADB wireless-debugging pairing requirements are removed.
- `device-management`: the saved-device model and store no longer carry the Android TV text-input opt-in flag.
- `tui-remote`: the Android TV text-input-mode toggle, the post-add ADB text hint, and the ADB-text-unavailable status requirements are removed.

## Impact

- `src/universal_remote/adapters/androidtv.py` — text dispatch rebuilt; `pair_adb`, `supports_adb_text`, `text_via_adb` routing and `adb_text_unavailable` removed.
- New module owning the Remote v2 IME text path, so all contact with `androidtvremote2` internals is confined to one tested file.
- `src/universal_remote/adapters/adb_text.py` — reduced to the `input text` command building and escaping that Fire TV still uses; the `AdbText` client, `adb` binary discovery, mDNS target resolution, and ADB pairing are deleted.
- `src/universal_remote/devices/models.py` — `Device.text_via_adb` removed; stored entries carrying it are ignored on load, as unknown legacy fields already are.
- `src/universal_remote/tui/devices_screen.py`, `discover_screen.py`, `remote_screen.py`, `app.py` — toggle, pairing modal, hint, and status removed.
- Tests: `test_tui_adb_text.py` removed; `test_androidtv_adapter.py`, `test_device_model.py`, `test_tui_discover.py`, `tests/fakes.py` updated; `test_adb_text.py` narrowed to the escaping helpers.
- Dependencies unchanged — `adb-shell` stays for Fire TV, `androidtvremote2` stays for keys, pairing, and transport.
- Depends on `androidtvremote2` private members (the protocol object, its inbound message handling, and its send path). Version-pinning and an upstream fix are follow-ups, not part of this change.
