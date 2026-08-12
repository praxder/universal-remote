## Context

The Android TV adapter sends text over Remote v2 (`androidtvremote2.send_text`), an IME batch-edit channel. On Google TV / newer Android TV, focusing many fields raises a "Use the keyboard on your mobile device" overlay that owns the input connection; while it is up the batch edit is silently dropped (verified live on a Chromecast with Google TV, codename `sabrina`: send returns cleanly, IME counters populate, no text appears). Text does land in fields that do not raise the overlay (e.g. YouTube search), so Remote v2 text is correct but incomplete.

ADB `input text` injects through Android's InputManager — the same path as a physical keyboard — and was verified to land text with the overlay up on every surface tested. The current pip dependency `adb-shell` implements only the classic ADB-over-TCP (port 5555) RSA-popup connect that Fire TV uses; it has no support for the Android 11+ wireless-debugging pairing-code flow that Google TV requires. The system `adb` binary does support that flow and worked in testing.

## Goals / Non-Goals

**Goals:**
- Let a Google TV / Android TV device send remote text that lands everywhere, including overlay surfaces.
- Preserve the existing Remote v2 experience for keys, discovery, PIN pairing, and text on devices that do not opt in.
- Keep the ADB path opt-in and per-device.
- Degrade gracefully when the ADB path is unavailable.

**Non-Goals:**
- Replacing Remote v2 keys with ADB (keys stay on Remote v2; no full-ADB adapter).
- Adding a pure-Python ADB pairing implementation (the SPAKE2/TLS pairing protocol is out of scope; we shell out to `adb`).
- Bundling or installing the `adb` binary.
- Fixing the overlay behavior itself (a Google TV / firmware behavior we cannot change).

## Decisions

### Route text over the system `adb` binary, opt-in per device
When a device sets `text_via_adb`, `AndroidTvSession._dispatch_text` sends `adb -s <target> shell input text <escaped>` instead of Remote v2. All other devices keep using `send_text`.
- **Why not `adb-shell`?** It cannot do wireless-debugging pairing, which Google TV requires. Alternatives (adbutils, ppadb) still need the `adb` binary. Implementing pairing ourselves is high-risk and out of scope.
- **Why opt-in?** The path needs Developer options, wireless debugging, and the external binary. Most Android TV users get correct text over Remote v2 in app fields and should not be forced through ADB setup.

### The adb server owns the connection; our session shells out on demand
We do not hold a second socket. The session stores the device IP + opt-in and invokes `adb` per text send, resolving the target lazily on first send. The `adb` daemon persists device trust and the connection across our process restarts.

### Resolve the target via mDNS each session
Wireless debugging's connect port is ephemeral (changes on toggle/reboot). `resolve_target(ip)` runs `adb mdns services` and matches the row by the device IP to get the current `ip:port`, then `adb connect`s it. This keeps device identity IP-based, consistent with the rest of the app, and survives port changes without stored state.

### Inject an `AdbRunner` seam
`adb_text.py` takes an injectable `AdbRunner = Callable[[list[str]], Awaitable[...]]` (default runs `adb` via `asyncio` subprocess). Tests pass a fake that records argv and returns canned output — no shelling out — mirroring how the Fire TV adapter injects its device/keygen/signer factories.

### Escape text as a tested pure function
`escape_for_input_text(text)` maps spaces to `%s` and escapes shell-special characters so a single `input text` argument reproduces the intended string. Kept pure and unit-tested independently of any subprocess.

### The ADB text opt-in is a toggle on Add/Edit, shown only for Android TV
The text-input mode is a toggle on the Add Device / Edit Device form, visible only when the device type is Android TV (gated on an adapter capability flag, `supports_adb_text`, mirroring the existing `requires_pairing`/`reachability_port` getattr idioms). The device list carries no text-mode action. Switching the toggle to ADB launches the pairing modal live — guiding the user (Developer options → Wireless debugging → Pair with code) and collecting the ephemeral `ip:port` + 6-digit code — because the pairing address/code are only valid momentarily. On successful pairing the opt-in is held as form intent and written to `text_via_adb` when the form is saved (forced by the Add flow, where no device exists until save); cancel/failure reverts the toggle. The pairing modal only performs `adb pair` and reports success/failure — it does not persist, keeping persistence on the form's Save alongside name/IP.

## Risks / Trade-offs

- **External `adb` binary required** → Path is opt-in; `find_adb()` checks PATH + common macOS locations and reports a clear message when missing. Remote v2 remains the default for everyone else.
- **Wireless debugging can auto-disable / port changes** → Re-resolve via mDNS each session; on failure fall back to Remote v2 `send_text` with a status note so app-field text still works.
- **State leaks into the user's global adb server** (trust + connection) → Accepted; it is how `adb` works and keeps us out of the pairing protocol.
- **`input text` escaping gaps** (unicode, unusual characters) → Cover the common ASCII + space cases with tested escaping; document the limitation rather than promising full unicode.
- **Two pairings for one device** (Remote v2 PIN + ADB) → Kept separate and opt-in; only users who need overlay-proof text pay the cost.

## Migration Plan

- Additive only. `Device` gains optional `text_via_adb: bool = False`; `Device.from_dict` already ignores unknown keys, so old `devices.json` loads unchanged and existing devices default to the Remote v2 path.
- No rollback concerns: removing the opt-in flag returns a device to Remote v2 text.

## Open Questions

- None blocking. Non-unicode `input text` escaping is a known limitation, not a blocker.
