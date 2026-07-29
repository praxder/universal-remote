"""Android TV adapter — wraps `androidtvremote2`'s Remote v2 protocol behind the seam.

Android TV / Google TV ships the Android TV Remote protocol v2, enabled by default
with no developer mode. Pairing shows a code on the TV that the user reads back (the
same PIN shape as Apple TV), and yields a client certificate that later connections
replay over TLS. The library is file-path based, so the adapter bridges its cert+key
files to the seam's single-string credential: pack both PEMs into one opaque string,
and materialize them to an ephemeral temp dir at pair and connect time so no key
material outlives the operation on disk.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from typing import TYPE_CHECKING, Awaitable, Callable

from androidtvremote2 import AndroidTVRemote

from ..capabilities import Capabilities
from ..discovery import DiscoveredDevice, MdnsHit, browse_mdns
from ..errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
)
from ..keys import Key
from ..session import BaseSession
from .adb_text import AdbText, find_adb_text

if TYPE_CHECKING:
    from ..devices.models import Device
    from ..registry import AdapterRegistry

PLATFORM = "androidtv"
CLIENT_NAME = "Universal Remote"  # the label the TV shows during pairing
PAIR_PROMPT = "Enter the code shown on your Android TV"
# The Remote v2 mDNS service; its instance name is the TV's friendly name.
DISCOVERY_SERVICE = "_androidtvremote2._tcp.local."

_CERTFILE = "cert.pem"
_KEYFILE = "key.pem"
_CONNECT_TIMEOUT = 10  # seconds to reach the TV before treating it as unreachable

# Generic key -> Android TV Remote v2 keycode name, accepted by send_key_command.
# Names are the fully-prefixed KEYCODE_* members of the library's RemoteKeyCode enum.
ANDROIDTV_KEYS: dict[Key, str] = {
    Key.UP: "KEYCODE_DPAD_UP",
    Key.DOWN: "KEYCODE_DPAD_DOWN",
    Key.LEFT: "KEYCODE_DPAD_LEFT",
    Key.RIGHT: "KEYCODE_DPAD_RIGHT",
    Key.OK: "KEYCODE_DPAD_CENTER",
    Key.BACK: "KEYCODE_BACK",
    Key.HOME: "KEYCODE_HOME",
    Key.MENU: "KEYCODE_MENU",
    Key.VOL_UP: "KEYCODE_VOLUME_UP",
    Key.VOL_DOWN: "KEYCODE_VOLUME_DOWN",
    Key.MUTE: "KEYCODE_VOLUME_MUTE",
    Key.CH_UP: "KEYCODE_CHANNEL_UP",
    Key.CH_DOWN: "KEYCODE_CHANNEL_DOWN",
    Key.PLAY: "KEYCODE_MEDIA_PLAY",
    Key.PAUSE: "KEYCODE_MEDIA_PAUSE",
    Key.PLAY_PAUSE: "KEYCODE_MEDIA_PLAY_PAUSE",
    Key.STOP: "KEYCODE_MEDIA_STOP",
    Key.REWIND: "KEYCODE_MEDIA_REWIND",
    Key.FAST_FORWARD: "KEYCODE_MEDIA_FAST_FORWARD",
    # Number pad: KEYCODE_0..KEYCODE_9.
    **{Key[f"NUM_{digit}"]: f"KEYCODE_{digit}" for digit in range(10)},
}

_CAPABILITIES = Capabilities(keys=frozenset(ANDROIDTV_KEYS), text=True)

# A factory so tests inject a fake in place of the real library client.
RemoteFactory = Callable[..., AndroidTVRemote]

# The mDNS browse seam, injected so discovery is testable without a live network.
MdnsBrowser = Callable[[str, float], Awaitable[list[MdnsHit]]]

# Builds the ADB text seam (or None when `adb` is missing), injected so text routing
# is tested with a fake `adb` and so the binary is only located when it is needed.
AdbTextFactory = Callable[[], AdbText | None]


def _pack_credential(cert: str, key: str) -> str:
    """Pack the paired client cert and key PEMs into one opaque credential string."""
    return json.dumps({"cert": cert, "key": key})


def _unpack_credential(credential: str) -> tuple[str, str]:
    """Recover the cert and key PEMs a credential was packed from."""
    data = json.loads(credential)
    return data["cert"], data["key"]


def _cert_paths(directory: str) -> tuple[str, str]:
    """The cert and key file paths the library reads within a temp dir."""
    return os.path.join(directory, _CERTFILE), os.path.join(directory, _KEYFILE)


def _write(path: str, contents: str) -> None:
    with open(path, "w") as out:
        out.write(contents)


def _read(path: str) -> str:
    with open(path) as src:
        return src.read()


class AndroidTvSession(BaseSession):
    """A live Remote v2 connection to an Android TV; maps generic keys to keycodes.

    Owns the temp dir holding the connection's cert and key for the session's whole
    lifetime and removes it on release, so no key material outlives the session on disk.

    When opted in (`text_via_adb`), text is routed over the system `adb` binary so it
    lands even under the IME overlay; keys always stay on Remote v2. If the ADB path
    is unavailable the session falls back to Remote v2 text and flags it so the remote
    surface can say so (`adb_text_unavailable`).
    """

    def __init__(
        self,
        remote,
        capabilities: Capabilities,
        cert_dir,
        *,
        device_ip: str = "",
        text_via_adb: bool = False,
        adb_text: AdbText | None = None,
    ) -> None:
        super().__init__(capabilities)
        self._remote = remote
        self._cert_dir = cert_dir
        self._device_ip = device_ip
        self._text_via_adb = text_via_adb
        self._adb_text = adb_text
        self._adb_target: str | None = None  # resolved lazily on first ADB send
        # Set after each send: True when an opted-in send fell back to Remote v2.
        self.adb_text_unavailable = False

    async def _dispatch_key(self, key: Key) -> None:
        self._remote.send_key_command(ANDROIDTV_KEYS[key])  # synchronous library call

    async def _dispatch_text(self, text: str) -> None:
        self.adb_text_unavailable = False
        if self._text_via_adb and await self._send_via_adb(text):
            return
        if self._text_via_adb:
            self.adb_text_unavailable = True  # opted in but ADB was unavailable
        self._send_via_remote_v2(text)

    async def _send_via_adb(self, text: str) -> bool:
        """Send `text` over ADB, returning False if the ADB path is unavailable."""
        if self._adb_text is None:  # `adb` binary missing
            return False
        target = await self._resolve_adb_target()
        if target is None:  # device not reachable over wireless debugging
            return False
        try:
            await self._adb_text.send_text(target, text)
            return True
        except Exception:
            return False

    async def _resolve_adb_target(self) -> str | None:
        # Cache a real hit for the session; a miss (None) is re-resolved next send.
        if self._adb_target is None:
            self._adb_target = await self._adb_text.resolve_target(self._device_ip)
        return self._adb_target

    def _send_via_remote_v2(self, text: str) -> None:
        try:
            self._remote.send_text(text)  # synchronous library call
        except Exception as exc:
            raise TextUnsupportedError(
                "Text input failed or is unsupported on this Android TV"
            ) from exc

    async def _release(self) -> None:
        self._remote.disconnect()  # the library's disconnect() is synchronous
        self._cert_dir.cleanup()


class AndroidTvAdapter:
    """Builds Android TV sessions; pairing yields a packed cert+key credential."""

    platform = PLATFORM
    display_name = "Android TV"
    reachability_port = 6466  # Remote v2 api/command port
    supports_adb_text = True  # offers the opt-in ADB text path (see adb_text.py)

    def __init__(
        self,
        remote_factory: RemoteFactory = AndroidTVRemote,
        browse: MdnsBrowser = browse_mdns,
        adb_text_factory: AdbTextFactory = find_adb_text,
        connect_timeout: float = _CONNECT_TIMEOUT,
    ) -> None:
        self._remote_factory = remote_factory
        self._browse = browse
        self._adb_text_factory = adb_text_factory
        self._connect_timeout = connect_timeout

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    async def discover(self, timeout: float) -> list[DiscoveredDevice]:
        # The mDNS instance name is the TV's friendly name; a blank one falls back
        # to the IP inside DiscoveredDevice.
        hits = await self._browse(DISCOVERY_SERVICE, timeout)
        return [
            DiscoveredDevice(name=hit.name, platform=PLATFORM, ip=hit.ip)
            for hit in hits
        ]

    async def pair(self, device: "Device", *, prompt=None) -> str:
        # A PIN adapter cannot pair without a way to ask for the code.
        if prompt is None:
            raise PairingCancelledError()
        # Generate the cert into a throwaway temp dir, run the code exchange, then
        # read both PEMs back to persist; nothing is left on disk once pairing returns.
        with tempfile.TemporaryDirectory() as tmp:
            certfile, keyfile = _cert_paths(tmp)
            remote = self._remote_factory(
                client_name=CLIENT_NAME,
                certfile=certfile,
                keyfile=keyfile,
                host=device.ip,
            )
            await remote.async_generate_cert_if_missing()
            try:
                await remote.async_start_pairing()  # the TV now shows its code
                await remote.async_finish_pairing(await prompt(PAIR_PROMPT))
            finally:
                remote.disconnect()
            return _pack_credential(_read(certfile), _read(keyfile))

    async def connect(self, device: "Device") -> AndroidTvSession:
        # Materialize the stored cert+key into a fresh temp dir the session owns, then
        # connect. Unpacking is inside the try so a malformed credential also surfaces
        # as a failed connect. The library's connect confirms the remote actually starts.
        cert_dir = tempfile.TemporaryDirectory()
        try:
            cert, key = _unpack_credential(device.credential)
            certfile, keyfile = _cert_paths(cert_dir.name)
            _write(certfile, cert)
            _write(keyfile, key)
            remote = self._remote_factory(
                client_name=CLIENT_NAME,
                certfile=certfile,
                keyfile=keyfile,
                host=device.ip,
            )
            # The library's connect takes no timeout, so bound it here; both a
            # transport failure and a timeout surface as ConnectionFailedError.
            await asyncio.wait_for(remote.async_connect(), self._connect_timeout)
        except Exception as exc:
            cert_dir.cleanup()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        # Build the ADB seam only for an opted-in device, so `adb` is located lazily.
        adb_text = self._adb_text_factory() if device.text_via_adb else None
        return AndroidTvSession(
            remote,
            _CAPABILITIES,
            cert_dir,
            device_ip=device.ip,
            text_via_adb=device.text_via_adb,
            adb_text=adb_text,
        )

    async def pair_adb(self, address: str, code: str) -> bool:
        """Run the one-time ADB wireless-debugging pairing; True if it succeeds.

        Distinct from Remote v2 PIN pairing: `address` is the `ip:port` the TV shows
        on its "Pair with code" screen. Returns False (never raising) when `adb` is
        missing or the pairing is rejected, so the caller leaves the device unchanged.
        """
        adb_text = self._adb_text_factory()
        if adb_text is None:
            return False
        ip, _, port = address.partition(":")
        return await adb_text.pair(ip, port, code)


def register(registry: "AdapterRegistry") -> None:
    registry.register(AndroidTvAdapter())
