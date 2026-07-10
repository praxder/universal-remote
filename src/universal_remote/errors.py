"""Errors raised across the remote-control seam."""

from __future__ import annotations


class UniversalRemoteError(Exception):
    """Base class for all universal-remote errors."""


class UnsupportedPlatformError(UniversalRemoteError):
    """No adapter is registered for the requested platform."""


class UnsupportedKeyError(UniversalRemoteError):
    """A key was sent that the adapter does not declare as supported."""


class TextUnsupportedError(UniversalRemoteError):
    """Text entry is not supported by the adapter or failed on the device."""


class SessionClosedError(UniversalRemoteError):
    """An action was attempted on a session that has been closed."""


class PairingCancelledError(UniversalRemoteError):
    """Pairing was cancelled before a credential was obtained."""
