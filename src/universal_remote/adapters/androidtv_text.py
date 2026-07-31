"""Remote v2 IME text path — the app's only contact with `androidtvremote2` internals.

`androidtvremote2`'s `send_text` builds three of the four batch-edit fields wrongly: it
takes both counters from the inbound batch edit, which is a fixed `{1, 1}` greeting
rather than live state, and derives the cursor span from the sent text alone, ignoring
what the field already holds. Google TV silently discards edits built that way — which
is what the withdrawn ADB text path existed to work around. The values the device
actually wants ride on its own inbound reports, which the library logs as `Unhandled:`
and drops, so patching the outgoing message alone cannot fix it.

This module therefore taps the protocol's inbound handler to keep that state fresh and
builds the batch edit itself; `send_text` takes no parameters that would let a caller
supply either value, so there is nothing to reuse. Every private member the app touches
— the protocol object, the inbound hook, and the send path — lives here, so a library
upgrade breaks in one obvious, tested place rather than across the adapter.

A send is confirmed by the device's own echo. The device reports a field gaining focus
but never reports losing it, so tracked state cannot be trusted to still be current: an
edit built from a stale counter is discarded in silence, which would otherwise be
reported to the user as a success. Every accepted edit produces a fresh field-state
report within about 90ms while a discarded one produces nothing at all, so waiting for
that report turns silent discards into an honest failure — on stale state, and on any
device whose input method this recipe has not been verified against.
"""

from __future__ import annotations

import asyncio

from androidtvremote2 import remotemessage_pb2 as pb
from google.protobuf.message import DecodeError

from ..errors import TextUnsupportedError

NO_FIELD_MESSAGE = "No text field is focused on this Android TV"
EMPTY_TEXT_MESSAGE = "Text cannot be empty"
NO_ACK_MESSAGE = (
    "The Android TV discarded the text — refocus the text field, then retry"
)

# Seconds to wait for the device to echo an accepted edit. Observed echoes arrive in
# 30–90ms; the margin is generous because it is only ever spent on a failing send.
_ACK_TIMEOUT = 1.0


def _reported_field(message: pb.RemoteMessage) -> pb.RemoteTextFieldStatus | None:
    """The device's text-field state, from whichever inbound message carries it.

    It arrives on the key-inject message when a field gains focus, and on the
    show-request message after every edit — including edits made with the physical
    remote. A key-inject naming only the foreground app carries no state.
    """
    if message.remote_ime_key_inject.HasField("text_field_status"):
        return message.remote_ime_key_inject.text_field_status
    if message.remote_ime_show_request.HasField("remote_text_field_status"):
        return message.remote_ime_show_request.remote_text_field_status
    return None


class AndroidTvText:
    """Sends Remote v2 text built from the device's most recent text-field report."""

    def __init__(self, protocol, *, ack_timeout: float = _ACK_TIMEOUT) -> None:
        self._protocol = protocol
        self._counter: int | None = None  # None until the device reports a field
        self._editor_counter: int | None = None
        self._value = ""
        self._ack_timeout = ack_timeout
        # Set on every inbound field-state report, so a send can await its echo.
        self._reported = asyncio.Event()
        self._observe_inbound()

    @property
    def field_focused(self) -> bool:
        """Whether the device has reported a focused text field to send into."""
        return self._counter is not None

    async def send(self, text: str) -> None:
        """Append `text` to the focused field, waiting for the device to confirm it.

        With no field focused the device reports no counter, so any edit would be
        discarded silently — failing here says so instead. Empty text is refused as
        the library's own `send_text` refused it, rather than putting a no-op edit
        on the wire (macro playback can replay a step whose text is missing).
        """
        if not text:
            raise TextUnsupportedError(EMPTY_TEXT_MESSAGE)
        if self._counter is None:
            raise TextUnsupportedError(NO_FIELD_MESSAGE)
        self._reported.clear()
        self._protocol._send_message(self._batch_edit(text))
        await self._await_echo()

    async def _await_echo(self) -> None:
        """Wait for the device's report of the edit; its absence means it was dropped.

        Any fresh report is the acknowledgement rather than one whose contents match
        what was sent, because a field may transform what it stores — a masked entry
        echoes no readable value — while a discarded edit draws no report at all.
        """
        try:
            await asyncio.wait_for(self._reported.wait(), self._ack_timeout)
        except asyncio.TimeoutError:
            raise TextUnsupportedError(NO_ACK_MESSAGE) from None

    def _batch_edit(self, text: str) -> pb.RemoteMessage:
        """The edit the device accepts: live field counter, resulting cursor span."""
        # The span is where the cursor ends up — what the field already holds plus
        # what is being inserted — while the value is only the inserted text. The two
        # are deliberately different strings; making them agree is what gets dropped.
        cursor = len(self._value) + len(text)
        message = pb.RemoteMessage()
        message.remote_ime_batch_edit.CopyFrom(
            pb.RemoteImeBatchEdit(
                ime_counter=self._ime_counter(),
                field_counter=self._counter,
                edit_info=[
                    pb.RemoteEditInfo(
                        insert=1,
                        text_field_status=pb.RemoteImeObject(
                            start=cursor, end=cursor, value=text
                        ),
                    )
                ],
            )
        )
        return message

    def _ime_counter(self) -> int:
        """The counter the device matches an edit against.

        It is the focused editor's own counter, which the device reports alongside the
        foreground app. The inbound batch edit's counter looks like the obvious source
        and is what the library uses, but it is a fixed greeting — `1` on every
        surface observed — so it only happens to be right where the editor's counter
        is also 1. The launcher search box reports 1; an app's field reported 2 and
        silently discarded edits carrying 1.
        """
        if self._editor_counter is None:
            return self._protocol.ime_counter
        return self._editor_counter

    def _observe_inbound(self) -> None:
        """Watch inbound messages for field state, leaving the library's own intact."""
        library_handler = self._protocol._handle_message

        def handle(raw_msg: bytes) -> None:
            # The library answers pings on this path, so it runs first: a fault in
            # text tracking must never cost the connection its keys.
            library_handler(raw_msg)
            self._track(raw_msg)

        self._protocol._handle_message = handle

    def _track(self, raw_msg: bytes) -> None:
        message = pb.RemoteMessage()
        try:
            message.ParseFromString(raw_msg)
        except DecodeError:
            return  # not a message we can read; the library ignores it too
        if message.remote_ime_key_inject.HasField("app_info"):
            # Re-read per report: it belongs to the focused editor, so it changes when
            # the user moves to another app's field.
            self._editor_counter = message.remote_ime_key_inject.app_info.counter
        status = _reported_field(message)
        if status is not None:
            # Re-read, never incremented: the counter advanced by 3 on a session's
            # first accepted edit and by 1 on later ones, so no local step is right.
            self._counter = status.counter_field
            self._value = status.value
            self._reported.set()


def install_text(remote) -> AndroidTvText:
    """Attach the text path to a connected `AndroidTVRemote`.

    The protocol object exists only once the connection is up, so this runs after
    connect — and it lives here so the private attribute stays in this module.
    """
    return AndroidTvText(remote._remote_message_protocol)
