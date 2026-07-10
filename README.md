# universal-remote

A local, terminal-based universal TV remote. Pretty, mouse-clickable, and fully
keyboard-drivable. Ships with a Samsung Tizen adapter; the architecture is
platform-agnostic so new TV platforms are "one new adapter module + register it."

## Requirements

- Python 3.13 (pinned via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/)

## Install & run

```sh
uv sync
uv run universal-remote
```

The app opens a menu with two modes: **Manage Devices** and **Use Remote**.
Everything is reachable by keyboard and by mouse.

## Add a Samsung TV

1. From the menu choose **Manage Devices** (`d`), then **Add** (`a`).
2. Enter the TV's IP address and press **Probe** — the app queries the TV's info
   endpoint (`http://<ip>:8001/api/v2/`) and pre-fills name, model, and MAC.
   If the probe fails, fill the fields in manually; adding is never blocked.
3. **Save**.

## Pair and control

1. From the menu choose **Use Remote** (`r`) and pick your TV.
2. First time only: the TV shows an **authorization popup** — accept it. The
   pairing token is saved so later sessions connect without a popup. Pairing is
   cancellable (Esc).
3. The remote appears. Control it by mouse (click any button) or keyboard:

   | Key | Action |
   | --- | --- |
   | Arrows | D-pad up/down/left/right |
   | Enter | OK |
   | Esc | Back |
   | `h` | Home |
   | `t` | Enter the text field (type, Enter sends, Esc leaves the field) |
   | `q` | Exit the remote |

   Volume, mute, and power are on-screen buttons. Buttons the connected TV does
   not support are shown disabled.

## Caveats (Samsung hardware reality)

- **Text entry is best-effort.** `SendInputString` is unreliable or removed on
  newer Tizen firmware. When a text send fails, the field reports "not supported"
  rather than silently dropping input.
- **Power-on is best-effort.** A TV with a dead WebSocket (off) is woken with a
  Wake-on-LAN magic packet to its stored MAC — which requires the TV's
  "Network Standby / Wake on LAN" setting to be **on** (off by default on many
  Samsungs). Power-**off** (the power key while connected) is reliable.

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
