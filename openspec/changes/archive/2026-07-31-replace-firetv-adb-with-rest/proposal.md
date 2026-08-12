## Why

Controlling a Fire TV over ADB requires leaving Developer options and ADB debugging enabled, and the adapter's long-lived ADB connection conflicts with any other ADB use of the same device — sideloading an APK, for instance. The Fire TV exposes the undocumented REST API that Amazon's own remote app uses, which needs no developer mode, holds no socket, is roughly four times faster per keypress, and supports text entry and press-and-hold that the ADB path handles worse or not at all.

## What Changes

- **BREAKING** Replace the Fire TV transport: ADB over TCP (`adb-shell`, port 5555) is removed in favour of the Amazon REST remote API over HTTPS (port 8080), woken via a DIAL app launch on port 8009.
- **BREAKING** Fire TV pairing changes from a device-side authorization popup to a PIN displayed on the TV and typed by the user, using the existing `Prompt` seam. Existing Fire TV credentials (ADB RSA private keys) become invalid and affected devices must be re-paired.
- **BREAKING** Drop `PLAY_PAUSE`, `STOP`, `VOL_UP`, `VOL_DOWN`, and `MUTE` from declared Fire TV capabilities. `PLAY_PAUSE` and `STOP` have no REST action. The volume keys are reported unsupported by the device itself (`isVolumeControlsSupported: false`) and were verified to do nothing.
- Map `FAST_FORWARD` and `REWIND` onto the player-context d-pad scrub (`dpad_right` / `dpad_left`, ±10s per press) rather than a dedicated transport action, which the REST API does not provide.
- Route `NUM_0`–`NUM_9` through the text endpoint rather than a key event, since the REST API exposes no arbitrary keycode path.
- Replace the ADB `input text` path with the REST keyboard endpoint, which requires no shell escaping and supports Unicode.
- Change the Fire TV reachability port from 5555 to 8009, which is open on a stock device whether or not the remote service has been woken.
- Remove `adapters/adb_text.py` and its tests, which exist solely for the Fire TV ADB text path.
- Drop the `adb-shell` dependency. `adapters/firetv.py` and `tests/test_firetv_adapter.py` are its only users; no other adapter imports it.

## Capabilities

### New Capabilities

None. This change replaces the transport behind an existing capability.

### Modified Capabilities

- `firetv-adapter`: pairing becomes PIN-based rather than popup-based; the declared key set loses the volume keys, `PLAY_PAUSE`, and `STOP`; text entry and the low-latency dispatch requirements are restated against the REST transport instead of ADB input nodes.
- `homebrew-distribution`: `adb-shell` leaves the list of dynamic-import dependencies the frozen bundle must carry, since the dependency is removed. The PyInstaller spec's `collect_all('adb_shell')` goes with it — left in place it would fail the build outright.

## Impact

- `src/universal_remote/adapters/firetv.py` — rewritten against the REST API; `FireTvSession` no longer holds a persistent connection.
- `src/universal_remote/adapters/adb_text.py` and `tests/test_adb_text.py` — removed.
- `tests/test_firetv_adapter.py` — rewritten against an injected HTTP seam.
- `pyproject.toml` and `uv.lock` — `adb-shell[async]` dependency removed, along with the transitive packages it alone pulled in.
- `universal-remote.spec` — the `collect_all('adb_shell')` bundling step removed; `THIRD_PARTY_LICENSES.md` regenerated from the new lock.
- Users with a paired Fire TV must re-pair; the stored credential format changes from an RSA private-key PEM to a short opaque token.
- The on-screen remote will disable the five dropped keys for Fire TV devices via the existing capability mechanism.
