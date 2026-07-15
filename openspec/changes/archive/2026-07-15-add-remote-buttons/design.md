## Context

The remote stack has a clean seam. `keys.py` defines a generic `Key` enum; `Capabilities` holds the `frozenset[Key]` an adapter supports plus a `text` flag; each adapter owns a `Key -> platform-code` dict and builds its `Capabilities` from that dict's keys. `BaseSession.send_key` rejects any key the adapter did not declare (`UnsupportedKeyError`). `RemoteScreen.on_mount` already loops `for key in Key` and disables the button `#key-<name>` for every key the active adapter lacks — so per-adapter enable/disable is fully generic and needs no new code.

Two existing tests pin the invariants this change must preserve: `test_keys.py` asserts the exact vocabulary set, and `test_tui_remote_surface.py::test_..._every_key_has_a_button` asserts every `Key` has a rendered `#key-<name>` button. The second is load-bearing: `on_mount` calls `query_one(f"#key-{key.name.lower()}")`, which raises if any key lacks a button. Every new key must therefore ship with a button in the same change.

## Goals / Non-Goals

**Goals:**

- Add nineteen keys to the vocabulary: `MENU`, `CH_UP`, `CH_DOWN`, `PLAY`, `PAUSE`, `PLAY_PAUSE`, `REWIND`, `FAST_FORWARD`, `STOP`, `NUM_0`–`NUM_9`.
- Map each new key on every adapter whose protocol supports it; leave it unmapped (auto-disabled) where it does not.
- Render the fuller remote so it fits an 80×24 terminal without scrolling, with digit keys bound to the number pad.

**Non-Goals:**

- No "Source", "Search", or "Settings" buttons (see the drop decision below).
- No keyboard bindings for the non-digit new buttons — mouse-only, like Mute today.
- No input-picker / `set_input` feature; the seam stays key-only.
- No store, pairing, or connect changes.

## Decisions

### "Supported" means the protocol accepts the code

A button is enabled iff the active adapter's protocol exposes its key — not iff a physical remote carries the button. The app is a superset remote, not a clone of any one vendor's handset. This resolves the Apple TV channel question: the Siri remote has no channel buttons, but pyatv's `RemoteControl` exposes `channel_up`/`channel_down` (they act in live-TV and TV-provider apps), so Apple TV declares them and the buttons are enabled.

### Per-adapter mapping matrix

pyatv's row was confirmed by inspecting `RemoteControl` on the installed library. LG button names and Samsung `KEY_` codes are the documented vocabularies; the ones marked ⚠ were **not** found in the vendored library source and need a real-device check (see Risks).

| Key | Apple TV (`remote_control.<m>`) | LG (`.button(name)`) | Samsung (`SendRemoteKey.click`) |
|---|---|---|---|
| MENU | — (menu = BACK) | `MENU` | `KEY_MENU` |
| CH_UP | `channel_up` | `CHANNELUP` | `KEY_CHUP` |
| CH_DOWN | `channel_down` | `CHANNELDOWN` | `KEY_CHDOWN` |
| PLAY | `play` | `PLAY` | `KEY_PLAY` ⚠ |
| PAUSE | `pause` | `PAUSE` | `KEY_PAUSE` ⚠ |
| PLAY_PAUSE | `play_pause` | — | — |
| REWIND | `skip_backward` | `REWIND` | `KEY_REWIND` ⚠ |
| FAST_FORWARD | `skip_forward` | `FASTFORWARD` | `KEY_FF` ⚠ |
| STOP | `stop` | `STOP` | `KEY_STOP` ⚠ |
| NUM_0–NUM_9 | — | `"0"`–`"9"` | `KEY_0`–`KEY_9` |

### Play, Pause, and Play/Pause are three independent keys

Apple TV exposes `play`, `pause`, **and** `play_pause`, so under the protocol-support rule it declares all three and shows three buttons. LG and Samsung have separate `PLAY`/`PAUSE` but no combined toggle (tracking toggle state we do not have would be the only alternative), so `PLAY_PAUSE` stays unmapped and renders disabled on both. Modeling them as three separate keys keeps each adapter declaring exactly what it supports — no state, no special cases.

### Rewind / Fast-forward use scan icons, unify two semantics

Apple TV's `skip_backward`/`skip_forward` jump ~10s; LG/Samsung `REWIND`/`FASTFORWARD` scan. The single `REWIND`/`FAST_FORWARD` keys render with scan icons (`◀◀` / `▶▶`), accepting that the Apple TV feel is a jump rather than a hold-to-scan. One key per direction, mapped to each platform's nearest transport control.

### Drop Source, Search, Settings

- **Source:** Samsung has `KEY_SOURCE`, but Apple TV *is* the source and LG switches inputs via `set_input(...)` — a picker, not a key. A single `SOURCE` key cannot express "which input", and modeling an input picker is a separate feature outside the key vocabulary. Dropped.
- **Search / Settings:** no clean code on Apple TV or LG, and only fuzzy Samsung equivalents. They would render disabled on two or three of three adapters. Low payoff. Dropped.

### Number-pad keys: `NUM_0`–`NUM_9`, bound to digit keys

Ten enum members `NUM_0`…`NUM_9`, buttons `#key-num_0`…`#key-num_9`, laid out as a 3×4 pad (1-2-3 / 4-5-6 / 7-8-9 / 0). On Apple TV the whole pad renders disabled (pyatv exposes no digits) — accepted. Digit keys `0`–`9` are bound on `RemoteScreen` to send the matching `NUM_x`; while the text field is focused the `Input` consumes digits as typed characters, exactly as it already consumes `hjkl`, so the bindings never fire mid-typing.

### Keyboard actions respect capabilities (no unsupported-key noise)

Digits are the first bound key that is *routinely* unsupported: every existing binding (D-pad, OK, Back, Home) maps to a key all three adapters declare, so the keyboard has never reached an unsupported key. On Apple TV the digit bindings would — pressing `5` would flow through `_send(Key.NUM_5)` to `UnsupportedKeyError` and flash *"NUM_5 is not supported on this device"*. That is noise, and it makes the hotkey behave differently from the button (which is simply disabled and silent).

Decision: `action_send` checks `self._capabilities.supports(key)` and no-ops silently when the key is unsupported, so a bound hotkey behaves exactly like its disabled button — nothing happens, no message. The click path cannot reach this (disabled buttons do not fire); only the keyboard path can. The `UnsupportedKeyError` branch in `_send` stays as a defensive backstop.

### Compact one-row buttons so the remote fits without scrolling

Textual `Button`s default to three rows tall; today's remote is already ~23 rows and the new groups would push it past ~40, overflowing an 80×24 terminal. Rather than add a scroll container (which would fight the D-pad arrow bindings for arrow-key focus), remote buttons render one row tall and borderless via CSS scoped to `RemoteScreen`. Groups: top row (Menu / Home / Back), D-pad, channel + volume row, media-transport row, 3×4 number pad, text field — ~15 rows, no scroll.

**Alternative considered:** keep the chunky buttons and wrap the remote in a `VerticalScroll`. Rejected — a scrolling remote is poor UX, and a focusable scroll container would capture the arrow keys the D-pad needs.

**Revised — bordered, bigger buttons over the strict 80×24 fit.** The one-row compact style read as cramped in practice, so the buttons are now bordered (`border: round`, three rows tall, padded) and laid out to resemble a physical remote: each group is a full-width centered row, and the D-pad is a cross (Up/OK/Down aligned, Left/Right flanking). This trades away the 80×24 no-scroll guarantee — the full bordered set needs a terminal ~41 rows tall — so the requirement is relaxed: the remote sizes to its content and the *screen* scrolls on a too-short terminal (every button stays reachable) rather than clipping. The supported baseline is pinned by `test_..._does_not_scroll` at 80×45. The device name lives in the header (app title, restored on unmount) rather than a dedicated title row, giving the button set that row back.

**As built:** the rules live in `RemoteScreen.DEFAULT_CSS` (a `Screen`'s inline styles are `DEFAULT_CSS`, not `CSS` — the latter is silently ignored). The button rule is `#remote Button { … border: round }`, id-scoped on purpose: Textual sets Button borders per-variant (`Button.-default`), and that class specificity beats a plain `RemoteScreen Button`, so the border only wins from an id-scoped selector. `#remote` and its row containers are `height: auto`; auto-height matters because a filling (`1fr`) container clips overflow silently (the fit test cannot see it), whereas with `height: auto` an over-tall set makes the screen scroll — a visible, asserted signal (`screen.max_scroll_y`). The D-pad cross uses three per-row Horizontals (`#dpad-up`/`#dpad-mid`/`#dpad-down`), each centering its own content; `align-horizontal` on the vertical `#dpad` alone would center the block but left-pack the narrow ▲/▼. Groups center via full-width rows with `align-horizontal: center`; the number pad sits in a centering `#numpad-row`.

**Disabled affordance.** The unmodified "Capability-driven button state" requirement says a button is disabled *and visibly indicated* (Apple TV shows ~11 disabled at once). The dim uses `text-opacity: 40% !important` (beating Textual's built-in 0.6) plus a `$panel` background, asserted by `test_..._visibly_dimmed`.

## Risks / Trade-offs

- **Unverified Samsung media codes (⚠ rows)** → `KEY_PLAY`, `KEY_PAUSE`, `KEY_STOP`, `KEY_REWIND`, `KEY_FF` are the well-known Samsung codes but were not found in the vendored `samsungtvws` source (the library takes arbitrary strings and enumerates nothing). `KEY_0`–`KEY_9`, `KEY_CHUP`, `KEY_CHDOWN`, `KEY_MENU` were found. Tasks include verifying the media codes on real hardware; if any is wrong, only that one mapping changes.
- **LG combined toggle / Samsung toggle** → neither has `PLAY_PAUSE`; the button is correctly disabled there, so a user on those TVs uses the separate Play and Pause buttons.
- **Apple TV rewind is a jump, not a scan** → the scan icon slightly overstates the behavior on Apple TV. Accepted for a single unified key.
- **Number pad dead on Apple TV** → ten disabled buttons plus a disabled Menu is a lot of dark surface on Apple TV. Accepted; the disable state is exactly the honest capability signal.
- **Big-bang risk** → nineteen keys at once is large. Mitigated by phasing (vocabulary + adapter maps first, then button groups render/bind, then per-adapter verification) so each step compiles and the two invariant tests stay green throughout.
- **Compact style changes the whole remote's look** → the D-pad and volume buttons also become one row tall. This is a deliberate visual change to make room; it keeps the surface consistent rather than mixing button heights.
- **Disabled affordance under borderless buttons** → removing borders may weaken the disabled cue; must be verified visually (see the layout decision), not just by tests.
