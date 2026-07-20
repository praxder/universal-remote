# universal-remote

A local, terminal-based universal TV remote. Pretty, mouse-clickable, and fully
keyboard-drivable. Ships with Samsung Tizen, LG WebOS, Apple TV, Roku, Fire TV,
and Android TV / Google TV adapters; the architecture is platform-agnostic so new
TV platforms are "one new adapter module + register it."

## Requirements

- Python 3.13 (pinned via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/)

## Install & run

```sh
uv sync
uv run universal-remote
```

The app opens a menu with two modes: **Manage Devices** and **Use Remote**.
Everything is reachable by keyboard and by mouse. Device lists number each saved
device — press its number (`1`–`9`) to open it — and `h`/`j`/`k`/`l` move through
menus and lists alongside the arrow keys.

## Add a TV

1. From the menu choose **Manage Devices** (`d`), then **Add** (`a`).
2. The app scans your local network and lists the TVs it finds — each row shows the
   device's **name**, its **platform**, and its **IP address**. Rows stream in as
   each platform answers, so you don't have to wait for the whole scan to finish.
3. **Select a discovered TV** to add it — no platform or IP typing, and no pairing
   yet (that happens the first time you use the remote). TVs you have already saved
   are left out of the list.
4. If your TV isn't listed, choose **+ Add manually** (always the last row) to open
   the manual form: pick the **platform** (Samsung Tizen, LG WebOS, Apple TV, Roku,
   Fire TV, or Android TV — the selector is hidden when only one adapter is
   installed), enter a **name** and the TV's **IP address**, and **Save**.

Discovery is best-effort: a TV that is off, on another subnet, or not yet set up
(for example, a Fire TV with ADB debugging still disabled) simply won't appear, so
manual entry is always available. You can leave the discovery screen (`Esc`) at any
time, even while it is still scanning.

## Pair and control

1. From the menu choose **Use Remote** (`r`) and pick your TV. Each device shows a
   **reachability bubble** before its number — 🟢 green (on the network), 🔴 red
   (unreachable), 🟡 yellow (still checking, or unknown for a platform with no
   probe port). It refreshes every few seconds and is advisory only: you can still
   select a red device to connect.
2. First time only: Samsung, LG, and Fire TV show an **authorization popup** —
   accept it. **Apple TV** instead displays a **PIN** on the TV screen, and
   **Android TV / Google TV** a pairing **code**; type it into the app when
   prompted. The credential is saved so later sessions connect without
   re-pairing. Pairing is cancellable (Esc). **Roku needs no pairing** — its
   control protocol is unauthenticated, so it connects directly with no popup,
   PIN, or stored credential.
3. The remote appears. Control it by mouse (click any button) or keyboard:

   | Key | Action |
   | --- | --- |
   | Arrows or `h` `j` `k` `l` | D-pad left/down/up/right |
   | Enter | OK |
   | Backspace | Back (sent to the TV) |
   | Space | Home |
   | `0`–`9` | Number-pad digits (ignored on TVs without a number pad) |
   | `t` | Enter the text field (type, Enter sends, Esc leaves the field) |
   | Esc | Exit the remote (back to the previous page) |

   Menu, channel up/down, volume, mute, the media-transport keys (play, pause,
   play/pause, rewind, fast-forward, stop), the number pad, and power are
   on-screen buttons; the digit keys above also drive the number pad. Buttons the
   connected TV does not support are shown disabled.

## Caveats (Samsung hardware reality)

- **Text entry is best-effort.** `SendInputString` is unreliable or removed on
  newer Tizen firmware. When a text send fails, the field reports "not supported"
  rather than silently dropping input.
- **Power-on is best-effort.** A TV with a dead WebSocket (off) is woken with a
  Wake-on-LAN magic packet to its stored MAC — which requires the TV's
  "Network Standby / Wake on LAN" setting to be **on** (off by default on many
  Samsungs). Power-**off** (the power key while connected) is reliable.

## Caveats (LG WebOS reality)

- **Pairing prompt.** First connect shows an on-screen authorization prompt;
  accept it and the client-key is saved for later sessions.
- **Text and power-on are best-effort**, as with Samsung: `insertText` support
  varies by app/firmware, and power-on relies on Wake-on-LAN to the stored MAC
  (the TV's "Wake on LAN / Mobile TV On" setting must be enabled).

## Caveats (Apple TV reality)

- **PIN pairing.** First connect shows a PIN on the Apple TV; type it into the
  app to pair over the Companion protocol. The credential is saved for later
  sessions, and the device's identity is re-verified on reconnect.
- **No mute.** The Companion remote has no mute action, so **MUTE is unavailable
  on Apple TV** — the on-screen button is shown disabled.
- **Text is best-effort**, as with the other platforms: keyboard entry depends on
  a focused text field, and a failed send reports "not supported" rather than
  silently dropping input.

## Caveats (Roku reality)

- **No pairing.** Roku's External Control Protocol is an unauthenticated HTTP API
  on the LAN, so there is no popup, no PIN, and no saved credential — Use Remote
  connects directly. Add a Roku by **manual IP entry** (the probe is
  Samsung-only), and connect verifies the device is reachable first.
- **Some keys are unavailable.** Roku's protocol exposes only a single
  **play/pause** toggle (no discrete play, pause, or stop), has **no number pad**,
  and has **no menu** key — those on-screen buttons are shown disabled for Roku.
  Volume, mute, channel up/down, rewind, and fast-forward are available.
- **Text is best-effort**, as with the other platforms: literal entry depends on
  a focused on-screen keyboard, and a failed send reports "not supported" rather
  than silently dropping input.

## Caveats (Fire TV reality)

- **Enable ADB debugging first.** Fire OS exposes no companion or PIN-paired
  remote protocol, so control runs over ADB. On the TV, go to **Settings →
  My Fire TV → Developer Options** and turn **ADB debugging** on before pairing.
- **Authorization popup.** First connect shows an "Allow ADB debugging?" dialog
  on the TV; accept it and tick **"Always allow from this computer"** so later
  connections skip the dialog. The app generates a per-device key and saves its
  private key as the credential; without the "always allow" tick the dialog
  reappears each connect.
- **No channel keys.** A Fire TV streamer has no tuner, so **channel up/down are
  unavailable** — those on-screen buttons are shown disabled for Fire TV.
- **Keys use a fast native input path.** Every key — d-pad, OK, back, home, menu,
  volume, mute, the media-transport keys, and the number pad — dispatches over a
  fast native path (kernel `sendevent`) and responds promptly. If the remote input
  device can't be found, all keys fall back to `adb shell input keyevent`, which
  cold-starts a runtime on Fire OS and lags ~1s.
- **Text and key codes are best-effort**, as with the other platforms: key
  events and `input text` are sent over ADB, and a failed text send reports
  "not supported" rather than silently dropping input.

## Caveats (Android TV / Google TV reality)

- **Works out of the box — no developer mode.** Android TV / Google TV (Sony,
  TCL, Nvidia Shield, Philips, Chromecast with Google TV) ships the native
  Android TV Remote protocol v2, on by default, so unlike Fire TV there is no ADB
  setup.
- **Code pairing.** First connect shows a pairing **code** on the TV; type it
  into the app to pair. A client certificate is saved as the credential and
  replayed on later connections, so the code is not shown again.
- **Full key set.** The d-pad, OK, back, home, menu, volume, **mute**, **channel
  up/down**, the media-transport keys, and the number pad are all available.
- **Text is best-effort**, as with the other platforms: entry depends on the
  focused app's input field, and a failed send reports "not supported" rather
  than silently dropping input.
- **Optional ADB text for overlay-proof typing.** On Google TV / newer Android TV,
  focusing many fields raises a "use the keyboard on your mobile device" overlay
  that silently swallows text sent over Remote v2. To make text land everywhere,
  opt a device into the **ADB text path**: in **Manage Devices**, highlight the TV
  and press **`t` (Text input (ADB))**. On the TV, enable **Settings → System →
  Developer options → Wireless debugging → Pair device with pairing code**, then
  type the address and code it shows into the app. This runs a one-time `adb pair`
  and remembers the opt-in; text is then sent via `input text` over the system
  `adb` binary while keys stay on Remote v2. Requires the external `adb` binary
  (Android platform-tools) on your machine and wireless debugging left enabled on
  the TV; if the ADB path is unavailable, text falls back to Remote v2 and the
  remote shows a one-line "ADB text unavailable" status. Non-ASCII characters are
  a known limitation of the ADB escaping.

## Storage

Devices and pairing credentials are stored in
`~/.config/universal-remote/devices.json` (or `$XDG_CONFIG_HOME`), written with
owner-only (`0600`) permissions since it holds secrets.

## When something goes wrong

The app is meant to stay up. An unexpected error while it is running — a device
that drops mid-command, an adapter that misbehaves — is caught, shown as a brief
error toast, and the app keeps running rather than crashing to the terminal. The
full traceback is written to `~/.config/universal-remote/error.log` (or
`$XDG_CONFIG_HOME`) so a real bug is still investigable. Expected, routine
failures are handled where they happen (a failed key or text send reports a
status; a failed reachability probe just leaves the bubble unresolved) and never
raise a toast. A failure during startup still exits — there is no running screen
to show a toast on yet.

## Development

```sh
uv run pytest        # full suite; runs across all cores (add -n0 for a serial run)
uv run ruff format   # format
uv run ruff check    # lint
```

Tests need no real TV — adapters run against in-memory fakes and mocked transport.
