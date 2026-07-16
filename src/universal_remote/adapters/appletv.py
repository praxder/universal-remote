"""Apple TV adapter — wraps `pyatv`'s Companion protocol behind the seam."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pyatv
from pyatv.const import Protocol

from ..capabilities import Capabilities
from ..errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
)
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "apple-tv"
PAIR_PROMPT = "Enter the PIN shown on your Apple TV"

# Generic key -> pyatv RemoteControl method name. Volume rides RemoteControl's
# fire-and-forget HID keys, not the Audio interface: Audio.volume_up/volume_down
# block on a volume-state ack that an idle Apple TV never sends, timing out after
# 5s and crashing the remote. RemoteControl.volume_* is deprecated in pyatv (a
# docstring note, no runtime error), but it is the correct button-remote behaviour.
APPLETV_RC_KEYS: dict[Key, str] = {
    Key.UP: "up",
    Key.DOWN: "down",
    Key.LEFT: "left",
    Key.RIGHT: "right",
    Key.OK: "select",
    Key.BACK: "menu",
    Key.HOME: "home",
    Key.VOL_UP: "volume_up",
    Key.VOL_DOWN: "volume_down",
    # MENU is intentionally absent: the Apple TV menu button is the BACK key.
    Key.CH_UP: "channel_up",
    Key.CH_DOWN: "channel_down",
    Key.PLAY: "play",
    Key.PAUSE: "pause",
    Key.PLAY_PAUSE: "play_pause",
    # skip_backward/forward jump ~10s; the shared REWIND/FAST_FORWARD keys accept
    # this jump semantics on Apple TV (LG/Samsung scan) — see design.
    Key.REWIND: "skip_backward",
    Key.FAST_FORWARD: "skip_forward",
    Key.STOP: "stop",
}

# MUTE is intentionally absent: pyatv exposes no mute on RemoteControl or Audio.
_CAPABILITIES = Capabilities(keys=frozenset(APPLETV_RC_KEYS), text=True)


class AppleTvSession(BaseSession):
    """A live connection to an Apple TV; maps generic keys to pyatv actions."""

    def __init__(self, atv, capabilities: Capabilities) -> None:
        super().__init__(capabilities)
        self._atv = atv

    async def _dispatch_key(self, key: Key) -> None:
        await getattr(self._atv.remote_control, APPLETV_RC_KEYS[key])()

    async def _dispatch_text(self, text: str) -> None:
        try:
            await self._atv.keyboard.text_set(text)
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this Apple TV"
            ) from exc

    async def _release(self) -> None:
        self._atv.close()  # pyatv's close() is synchronous


class AppleTvAdapter:
    """Builds Apple TV sessions; pairing yields a Companion credential to persist."""

    platform = PLATFORM
    display_name = "Apple TV"
    # AirPlay port — a proxy for "awake"; Companion control is mDNS-dynamic.
    reachability_port = 7000

    def __init__(self, pyatv_api=pyatv) -> None:
        self._pyatv = pyatv_api

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def pair(self, device: "Device", *, prompt=None) -> str:
        # A PIN adapter cannot pair without a way to ask for the PIN.
        if prompt is None:
            raise PairingCancelledError()
        loop = asyncio.get_running_loop()
        config = (await self._pyatv.scan(loop, hosts=[device.ip]))[0]
        pairing = await self._pyatv.pair(config, Protocol.Companion, loop)
        try:
            await pairing.begin()  # the Apple TV now shows its PIN
            pairing.pin(int(await prompt(PAIR_PROMPT)))
            await pairing.finish()
            device.identifier = config.identifier
            return pairing.service.credentials
        finally:
            await pairing.close()

    async def connect(self, device: "Device") -> AppleTvSession:
        loop = asyncio.get_running_loop()
        try:
            config = (await self._pyatv.scan(loop, hosts=[device.ip]))[0]
            if config.identifier != device.identifier:
                raise ConnectionFailedError(
                    f"Device at {device.ip} is not {device.name}"
                )
            config.set_credentials(Protocol.Companion, device.credential)
            atv = await self._pyatv.connect(config, loop)
        except ConnectionFailedError:
            raise
        except Exception as exc:
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return AppleTvSession(atv, _CAPABILITIES)


def register(registry: "AdapterRegistry") -> None:
    registry.register(AppleTvAdapter())
