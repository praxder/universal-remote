"""ADB text seam — wraps the system `adb` binary for the opt-in text path.

Android TV / Google TV raises a "use your phone" IME overlay that silently drops
text sent over Remote v2. ADB `input text` injects through Android's InputManager
(the physical-keyboard path) and lands text even with the overlay up. This module
shells out to `adb` because `adb-shell` cannot do the Android 11+ wireless-debugging
pairing flow Google TV requires. The subprocess is injected as an `AdbRunner` so the
routing and parsing are testable without a real `adb`.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from dataclasses import dataclass
from typing import Awaitable, Callable

# Characters that carry meaning to the device-side shell `input text` runs in, so a
# literal one must be backslash-escaped. Space is handled separately (it becomes
# `%s`). Unicode is out of scope — this covers the common ASCII cases (see design).
_SHELL_SPECIAL = frozenset("'\"\\`$&|;<>()*?~#!%")

# The wireless-debugging service whose row carries the current connect port. Its
# sibling `_adb-tls-pairing._tcp.` is the one-time pairing port, deliberately skipped.
_CONNECT_SERVICE = "_adb-tls-connect"
# An `ip:port` token, pulled by pattern so column/whitespace drift does not break us.
_ADDRESS = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}:\d+")


def _escape_char(char: str) -> str:
    if char == " ":
        return "%s"
    if char in _SHELL_SPECIAL:
        return "\\" + char
    return char


def escape_for_input_text(text: str) -> str:
    """Escape `text` so one `input text` argument reproduces it on the device."""
    return "".join(_escape_char(char) for char in text)


@dataclass(frozen=True)
class AdbResult:
    """One `adb` invocation's outcome: its exit status and combined output."""

    returncode: int
    stdout: str


# Runs `adb` with the given arguments and returns its result. Injected so routing
# and parsing are tested against a fake that records argv and returns canned output.
AdbRunner = Callable[[list[str]], Awaitable[AdbResult]]

# Where `adb` commonly lives on macOS when not already on PATH.
_COMMON_ADB_PATHS = (
    "/opt/homebrew/bin/adb",
    "/usr/local/bin/adb",
    os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
)


def find_adb() -> str | None:
    """The `adb` binary's path from PATH or a common macOS location, else None."""
    found = shutil.which("adb")
    if found is not None:
        return found
    return next((path for path in _COMMON_ADB_PATHS if os.path.isfile(path)), None)


def _subprocess_runner(adb_path: str) -> AdbRunner:
    """An `AdbRunner` that invokes the real `adb` binary via an asyncio subprocess."""

    async def run(args: list[str]) -> AdbResult:
        process = await asyncio.create_subprocess_exec(
            adb_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        return AdbResult(process.returncode or 0, stdout.decode(errors="replace"))

    return run


class AdbError(Exception):
    """An `adb` command exited non-zero (device unreachable, refused, etc.)."""


def _check(result: AdbResult) -> None:
    if result.returncode != 0:
        raise AdbError(result.stdout)


class AdbText:
    """Bound to one `AdbRunner`; sends text, resolves targets, and pairs over ADB."""

    def __init__(self, run: AdbRunner) -> None:
        self._run = run

    async def resolve_target(self, ip: str) -> str | None:
        """The device's current `ip:port` from mDNS, matched by IP, else None.

        The connect port is ephemeral, so it is re-resolved each session rather than
        stored; the tls-pairing row on the same IP is skipped in favour of connect.
        """
        result = await self._run(["mdns", "services"])
        for line in result.stdout.splitlines():
            if _CONNECT_SERVICE not in line:
                continue
            match = _ADDRESS.search(line)
            if match is not None and match.group().startswith(f"{ip}:"):
                return match.group()
        return None

    async def send_text(self, target: str, text: str) -> None:
        """Connect to `target` (idempotent) then type `text` via `input text`.

        Raises `AdbError` if the connect or the send exits non-zero, so the caller
        can fall back to Remote v2 when the device is unreachable over ADB.
        """
        _check(await self._run(["connect", target]))
        argv = ["-s", target, "shell", "input", "text", escape_for_input_text(text)]
        _check(await self._run(argv))

    async def pair(self, ip: str, port: str, code: str) -> bool:
        """Run the one-time wireless-debugging pairing; True if `adb pair` succeeds."""
        result = await self._run(["pair", f"{ip}:{port}", code])
        return result.returncode == 0


def find_adb_text() -> AdbText | None:
    """An `AdbText` bound to the system `adb`, or None when `adb` is not installed."""
    adb_path = find_adb()
    return AdbText(_subprocess_runner(adb_path)) if adb_path is not None else None
