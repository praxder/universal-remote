# universal-remote

A local, terminal-based universal TV remote. Pretty, mouse-clickable, and fully
keyboard-drivable. Ships with Samsung Tizen, LG WebOS, Apple TV, and Roku
adapters; the architecture is platform-agnostic so new TV platforms are "one new
adapter module + register it."

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
2. When more than one platform is available, pick the TV's **platform**
   (Samsung Tizen, LG WebOS, Apple TV, or Roku) from the selector. With a single
   adapter installed the selector is hidden and that platform is used automatically.
3. Enter the TV's IP address and press **Probe** — the app queries the TV's info
   endpoint (`http://<ip>:8001/api/v2/`) and pre-fills name, model, and MAC.
   If the probe fails, fill the fields in manually; adding is never blocked.
   Probe targets the Samsung info endpoint, so **LG, Apple TV, and Roku use
   manual entry**.
4. **Save**.

## Pair and control

1. From the menu choose **Use Remote** (`r`) and pick your TV.
2. First time only: Samsung and LG show an **authorization popup** — accept it.
   **Apple TV** instead displays a **PIN** on the TV screen; type it into the app
   when prompted. The credential is saved so later sessions connect without
   re-pairing. Pairing is cancellable (Esc). **Roku needs no pairing** — its
   control protocol is unauthenticated, so it connects directly with no popup,
   PIN, or stored credential.
3. The remote appears. Control it by mouse (click any button) or keyboard:

   | Key | Action |
   | --- | --- |
   | Arrows or `h` `j` `k` `l` | D-pad left/down/up/right |
   | Enter | OK |
   | Esc | Back |
   | Space | Home |
   | `0`–`9` | Number-pad digits (ignored on TVs without a number pad) |
   | `t` | Enter the text field (type, Enter sends, Esc leaves the field) |
   | `q` | Exit the remote |

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

## Storage

Devices and pairing credentials are stored in
`~/.config/universal-remote/devices.json` (or `$XDG_CONFIG_HOME`), written with
owner-only (`0600`) permissions since it holds secrets.

## Development

```sh
uv run pytest        # full suite; no real TV required (fakes + mocked transport)
uv run ruff format   # format
uv run ruff check    # lint
```
