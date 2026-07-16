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

import json
import os
import tempfile
from typing import TYPE_CHECKING, Callable

from androidtvremote2 import AndroidTVRemote

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

PLATFORM = "androidtv"
CLIENT_NAME = "Universal Remote"  # the label the TV shows during pairing
PAIR_PROMPT = "Enter the code shown on your Android TV"

_CERTFILE = "cert.pem"
_KEYFILE = "key.pem"

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
    """

    def __init__(self, remote, capabilities: Capabilities, cert_dir) -> None:
        super().__init__(capabilities)
        self._remote = remote
        self._cert_dir = cert_dir

    async def _dispatch_key(self, key: Key) -> None:
        self._remote.send_key_command(ANDROIDTV_KEYS[key])  # synchronous library call

    async def _dispatch_text(self, text: str) -> None:
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

    def __init__(self, remote_factory: RemoteFactory = AndroidTVRemote) -> None:
        self._remote_factory = remote_factory

    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

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
            await remote.async_connect()
        except Exception as exc:
            cert_dir.cleanup()
            raise ConnectionFailedError(f"Could not connect to {device.name}") from exc
        return AndroidTvSession(remote, _CAPABILITIES, cert_dir)


def register(registry: "AdapterRegistry") -> None:
    registry.register(AndroidTvAdapter())
