"""Amazon Fire TV adapter — wraps `adb-shell` over ADB behind the remote seam.

Fire OS is an Android fork whose only viable control path is ADB over TCP. ADB
authorization is a device-side popup that whitelists a client-generated RSA key;
pairing persists the private-key PEM and later connections replay it, so the
popup is not shown again — the same popup shape as Samsung/LG.
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Callable

from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.auth.keygen import keygen as adb_keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

from ..capabilities import Capabilities
from ..errors import ConnectionFailedError, TextUnsupportedError
from ..keys import Key
from ..session import BaseSession

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "firetv"
ADB_PORT = 5555
_PAIR_TIMEOUT = 30  # seconds to allow for accepting the authorization popup
_CONNECT_TIMEOUT = 10  # seconds to reach the device before treating it unreachable

# Generic key -> Android ADB key-event code (dispatched as `input keyevent <code>`).
# Codes are best-effort against Fire OS; a wrong code is a single-entry fix.
FIRETV_KEYS: dict[Key, int] = {
    Key.UP: 19,
    Key.DOWN: 20,
    Key.LEFT: 21,
    Key.RIGHT: 22,
    Key.OK: 23,
    Key.BACK: 4,
    Key.HOME: 3,
    Key.MENU: 82,
    Key.VOL_UP: 24,
    Key.VOL_DOWN: 25,
    Key.MUTE: 164,
    Key.PLAY: 126,
    Key.PAUSE: 127,
    Key.PLAY_PAUSE: 85,
    Key.STOP: 86,
    Key.REWIND: 89,
    Key.FAST_FORWARD: 90,
    # No channel up/down: a Fire TV streamer has no tuner.
    # Number pad: Android's KEYCODE_0–KEYCODE_9 are codes 7–16.
    **{Key[f"NUM_{digit}"]: 7 + digit for digit in range(10)},
}

_CAPABILITIES = Capabilities(keys=frozenset(FIRETV_KEYS), text=True)

# Generic key -> Linux evdev scancode for the on-device remote input node (mapped
# by Fire OS's Generic.kl). Sent via `sendevent`, these reach the focused window
# like the physical remote at ~300ms, vs the `input` binary's ~1.1s ART cold-start
# (see FIRETV_KEYS). This covers every declared key, so `input keyevent` is used
# only when no input node is discovered (see FireTvSession). Home, menu, and the
# media-transport codes were read from the device's Generic.kl and verified on
# hardware; `cmd media_session dispatch` was tried for media and found unimplemented.
EVDEV_KEYS: dict[Key, int] = {
    Key.UP: 103,
    Key.DOWN: 108,
    Key.LEFT: 105,
    Key.RIGHT: 106,
    Key.OK: 353,  # DPAD_CENTER via KEY_SELECT
    Key.BACK: 158,
    Key.HOME: 172,  # KEY_HOMEPAGE
    Key.MENU: 139,  # KEY_MENU
    Key.VOL_UP: 115,
    Key.VOL_DOWN: 114,
    Key.MUTE: 113,
    Key.PLAY: 207,  # KEY_PLAY
    Key.PAUSE: 201,  # KEY_PAUSECD
    Key.PLAY_PAUSE: 164,  # KEY_PLAYPAUSE
    Key.STOP: 128,  # KEY_STOP
    Key.REWIND: 168,  # KEY_REWIND
    Key.FAST_FORWARD: 208,  # KEY_FASTFORWARD
    Key.NUM_0: 11,  # KEY_0
    **{Key[f"NUM_{digit}"]: digit + 1 for digit in range(1, 10)},  # KEY_1..KEY_9
}

# evdev key names a candidate input node must expose to drive the d-pad.
_DPAD_EVDEV_NAMES = ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT")


def find_key_node(getevent_lp: str) -> str | None:
    """First `/dev/input/*` node whose `getevent -lp` block covers the d-pad keys.

    Returns None when no such node is listed, so the adapter falls back to `input`.
    """
    for block in getevent_lp.split("add device ")[1:]:
        path = block.split(":", 1)[1].split()[0] if ":" in block else ""
        if path and all(name in block for name in _DPAD_EVDEV_NAMES):
            return path
    return None


def evdev_press(node: str, code: int) -> str:
    """One key press as a single shell line: EV_KEY down, sync, up, sync."""
    return (
        f"sendevent {node} 1 {code} 1; sendevent {node} 0 0 0; "
        f"sendevent {node} 1 {code} 0; sendevent {node} 0 0 0"
    )


# Factories so tests inject fakes for the ADB device, keypair generation, and signer.
DeviceFactory = Callable[..., AdbDeviceTcpAsync]
Keygen = Callable[[], tuple[str, str]]  # returns (public, private) key contents
SignerFactory = Callable[..., PythonRSASigner]


def _keygen() -> tuple[str, str]:
    """Generate a fresh ADB keypair in a temp dir, returning (public, private).

    Uses a throwaway directory rather than `~/.android/adbkey`, so each paired
    device carries its own in-memory credential and nothing leaks to disk.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "adbkey")
        adb_keygen(path)
        with open(path) as private_file:
            private_key = private_file.read()
        with open(path + ".pub") as public_file:
            public_key = public_file.read()
    return public_key, private_key


class FireTvSession(BaseSession):
    """A live ADB connection to a Fire TV.

    Keys dispatch via `sendevent` to the discovered remote input node (`EVDEV_KEYS`
    covers every declared key). When no node was found the whole session falls back
    to `input keyevent`.
    """

    def __init__(
        self,
        device: AdbDeviceTcpAsync,
        capabilities: Capabilities,
        key_node: str | None = None,
    ) -> None:
        super().__init__(capabilities)
        self._device = device
        self._key_node = key_node

    async def _dispatch_key(self, key: Key) -> None:
        code = EVDEV_KEYS.get(key)
        if self._key_node is not None and code is not None:
            await self._device.shell(evdev_press(self._key_node, code))
        else:
            await self._device.shell(f"input keyevent {FIRETV_KEYS[key]}")

    async def _dispatch_text(self, text: str) -> None:
        try:
            await self._device.shell(f"input text {text}")
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this Fire TV"
            ) from exc

    async def _release(self) -> None:
        await self._device.close()


class FireTvAdapter:
    """Builds Fire TV sessions; pairing yields an RSA private-key PEM to persist."""

    platform = PLATFORM
    display_name = "Fire TV"
    reachability_port = ADB_PORT

    def __init__(
        self,
        device_factory: DeviceFactory = AdbDeviceTcpAsync,
        keygen: Keygen = _keygen,
        signer_factory: SignerFactory = PythonRSASigner,
        connect_timeout: float = _CONNECT_TIMEOUT,
    ) -> None:
        self._device_factory = device_factory
        self._keygen = keygen
        self._signer_factory = signer_factory
        self._connect_timeout = connect_timeout

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def pair(self, device: "Device", *, prompt=None) -> str:
        # Popup pairing (like Samsung/LG): generate a keypair, connect to trigger
        # the TV's authorization dialog, and persist the private-key PEM.
        public_key, private_key = self._keygen()
        signer = self._signer_factory(pub=public_key, priv=private_key)
        adb = self._device_factory(host=device.ip, port=ADB_PORT)
        try:
            await adb.connect(rsa_keys=[signer], auth_timeout_s=_PAIR_TIMEOUT)
            return private_key
        finally:
            await adb.close()

    async def connect(self, device: "Device") -> FireTvSession:
        # Replay the stored private key; the public key is already whitelisted, so
        # no dialog appears and pub=None suffices. Building the signer is inside the
        # try so a missing or malformed credential also surfaces as a failed connect.
        adb = self._device_factory(host=device.ip, port=ADB_PORT)
        try:
            signer = self._signer_factory(priv=device.credential)
            await adb.connect(
                rsa_keys=[signer],
                transport_timeout_s=self._connect_timeout,
                auth_timeout_s=self._connect_timeout,
            )
        except Exception as exc:
            await adb.close()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return FireTvSession(adb, _CAPABILITIES, await self._discover_key_node(adb))

    async def _discover_key_node(self, adb: AdbDeviceTcpAsync) -> str | None:
        # Locate the remote's input node once, so key routing is fixed per session;
        # any failure means the whole session falls back to `input keyevent`.
        try:
            return find_key_node(await adb.shell("getevent -lp"))
        except Exception:
            return None


def register(registry: "AdapterRegistry") -> None:
    registry.register(FireTvAdapter())
