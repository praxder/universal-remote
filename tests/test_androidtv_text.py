import asyncio
from types import SimpleNamespace

import pytest

from tests.fakes import (
    FakeRemoteProtocol,
    foreground_app,
    ime_key_inject,
    ime_show_request,
)
from universal_remote.adapters.androidtv_text import AndroidTvText, install_text
from universal_remote.errors import TextUnsupportedError

# Short enough that a test for a discarded edit does not sit out the real timeout.
FAST_ACK = 0.01


def run(coro):
    return asyncio.run(coro)


def _batch_edit(protocol: FakeRemoteProtocol):
    """The batch edit carried by the last message the seam sent."""
    return protocol.sent[-1].remote_ime_batch_edit


def _cursor(protocol: FakeRemoteProtocol) -> tuple[int, int]:
    status = _batch_edit(protocol).edit_info[0].text_field_status
    return status.start, status.end


def _sent_after(reports, *texts, ime_counter: int = 0) -> FakeRemoteProtocol:
    """Deliver `reports`, send each of `texts`, and hand back the protocol."""

    async def scenario() -> FakeRemoteProtocol:
        protocol = FakeRemoteProtocol(ime_counter=ime_counter)
        text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
        for report in reports:
            protocol.receive(report)
        for value in texts:
            await text.send(value)
        return protocol

    return run(scenario())


class TestFieldStateTracking:
    def test_given_nothing_reported_when_the_seam_is_built_then_no_field_is_focused(
        self,
    ):
        protocol = FakeRemoteProtocol()

        text = AndroidTvText(protocol)

        assert text.field_focused is False

    def test_given_a_show_request_when_received_then_a_field_is_focused(self):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)

        protocol.receive(ime_show_request(counter=41, value="ab"))

        assert text.field_focused is True

    def test_given_a_key_inject_report_when_received_then_a_field_is_focused(self):
        # The device reports field state two ways: on focus (key-inject) and after
        # every edit (show-request); the seam must consume both.
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)

        protocol.receive(ime_key_inject(counter=7, value=""))

        assert text.field_focused is True

    def test_given_only_a_foreground_app_report_when_received_then_no_field_is_focused(
        self,
    ):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)

        protocol.receive(foreground_app("com.google.android.youtube.tv"))

        assert text.field_focused is False

    def test_given_an_inbound_message_when_observed_then_the_library_still_handles_it(
        self,
    ):
        # The tap must not swallow inbound traffic: the library answers pings on this
        # path, and an unanswered ping makes the device drop the whole connection.
        protocol = FakeRemoteProtocol()
        AndroidTvText(protocol)
        message = ime_show_request(counter=41, value="ab")

        protocol.receive(message)

        assert protocol.handled == [message.SerializeToString()]


class TestBatchEdit:
    def test_given_a_reported_counter_when_text_is_sent_then_the_edit_carries_it(self):
        protocol = _sent_after([ime_show_request(counter=41, value="")], "hi")

        assert _batch_edit(protocol).field_counter == 41

    def test_given_a_field_with_contents_when_text_is_sent_then_the_span_is_the_new_cursor(
        self,
    ):
        protocol = _sent_after([ime_show_request(counter=41, value="abc")], "de")

        assert _cursor(protocol) == (5, 5)  # len("abc") + len("de")

    def test_given_text_when_sent_then_the_edit_inserts_only_that_text(self):
        protocol = _sent_after([ime_show_request(counter=41, value="abc")], "de")

        edit = _batch_edit(protocol).edit_info[0]
        assert edit.text_field_status.value == "de"
        assert edit.insert == 1

    def test_given_a_later_report_when_text_is_sent_again_then_the_newer_counter_is_used(
        self,
    ):
        # The counter advances unpredictably (by 3 on a session's first accepted edit
        # and by 1 after), so it is re-read from the newest report, never incremented.
        async def scenario():
            protocol = FakeRemoteProtocol()
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            protocol.receive(ime_show_request(counter=41, value=""))
            await text.send("hi")
            protocol.receive(ime_show_request(counter=44, value="hi"))
            await text.send("there")
            return protocol

        protocol = run(scenario())

        assert _batch_edit(protocol).field_counter == 44

    def test_given_a_first_send_when_a_second_follows_then_it_appends_after_it(self):
        protocol = _sent_after([ime_show_request(counter=41, value="")], "hi", "there")

        assert _cursor(protocol) == (7, 7)  # len("hi") + len("there")


class TestImeCounter:
    def test_given_a_reported_editor_counter_when_text_is_sent_then_the_edit_matches_it(
        self,
    ):
        # The device matches an edit against the focused editor's own counter, which
        # rides on the key-inject report — not the inbound batch edit, whose counter
        # is a fixed greeting of 1 on every surface.
        protocol = _sent_after(
            [ime_key_inject(counter=20, value="", app_counter=2)], "hi", ime_counter=1
        )

        assert _batch_edit(protocol).ime_counter == 2

    def test_given_a_newer_editor_counter_when_text_is_sent_then_the_newer_one_is_used(
        self,
    ):
        # Moving to another app re-reports it; the previous editor's value is stale.
        protocol = _sent_after(
            [
                ime_key_inject(counter=20, value="", app_counter=2),
                ime_key_inject(counter=46, value="", app_counter=5),
            ],
            "hi",
            ime_counter=1,
        )

        assert _batch_edit(protocol).ime_counter == 5

    def test_given_no_editor_counter_reported_when_text_is_sent_then_the_greeting_is_used(
        self,
    ):
        # Only the show-request arrived, which carries no editor counter; falling back
        # to what the library tracked keeps the previously working surfaces working.
        protocol = _sent_after(
            [ime_show_request(counter=20, value="")], "hi", ime_counter=1
        )

        assert _batch_edit(protocol).ime_counter == 1


class TestSendWithNoFocusedField:
    def test_given_no_field_focused_when_text_is_sent_then_text_unsupported_is_raised(
        self,
    ):
        async def scenario():
            text = AndroidTvText(FakeRemoteProtocol(), ack_timeout=FAST_ACK)
            with pytest.raises(TextUnsupportedError):
                await text.send("hi")

        run(scenario())

    def test_given_no_field_focused_when_text_is_sent_then_nothing_goes_to_the_device(
        self,
    ):
        async def scenario():
            protocol = FakeRemoteProtocol()
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            with pytest.raises(TextUnsupportedError):
                await text.send("hi")
            return protocol

        assert run(scenario()).sent == []


class TestSendWithEmptyText:
    def test_given_a_focused_field_when_empty_text_is_sent_then_nothing_goes_out(self):
        # A macro step whose text is missing replays as "", which the library's own
        # send_text refused; refusing it here keeps a no-op edit off the wire.
        async def scenario():
            protocol = FakeRemoteProtocol()
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            protocol.receive(ime_show_request(counter=41, value="ab"))
            with pytest.raises(TextUnsupportedError):
                await text.send("")
            return protocol

        assert run(scenario()).sent == []


class TestDiscardedEdit:
    def test_given_the_device_does_not_report_the_edit_then_text_unsupported_is_raised(
        self,
    ):
        # The device answers an accepted edit with a fresh report and a discarded one
        # with nothing, so silence is the only signal that the text did not land —
        # as happens once the user navigates away from the field it was tracking.
        async def scenario():
            protocol = FakeRemoteProtocol(echo=False)
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            protocol.receive(ime_show_request(counter=41, value=""))
            with pytest.raises(TextUnsupportedError):
                await text.send("hi")

        run(scenario())

    def test_given_a_discarded_edit_when_it_is_reported_then_the_edit_was_still_sent(
        self,
    ):
        # The failure is the device's silence, not a refusal to try.
        async def scenario():
            protocol = FakeRemoteProtocol(echo=False)
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            protocol.receive(ime_show_request(counter=41, value=""))
            with pytest.raises(TextUnsupportedError):
                await text.send("hi")
            return protocol

        assert len(run(scenario()).sent) == 1

    def test_given_the_device_reports_the_edit_when_sending_then_it_succeeds(self):
        async def scenario():
            protocol = FakeRemoteProtocol()
            text = AndroidTvText(protocol, ack_timeout=FAST_ACK)
            protocol.receive(ime_show_request(counter=41, value=""))
            await text.send("hi")  # no raise

        run(scenario())


class TestOutboundMessages:
    def test_given_a_focused_field_when_text_is_sent_then_no_field_state_report_is_emitted(
        self,
    ):
        # Sending the device's own report back makes it reset both counters and tear
        # down the input-method session, so it must never leave the client.
        protocol = _sent_after([ime_show_request(counter=41, value="ab")], "cd")

        assert not any(
            message.HasField("remote_ime_show_request") for message in protocol.sent
        )


class TestInstallText:
    def test_given_a_connected_remote_when_installed_then_its_protocol_is_tracked(self):
        protocol = FakeRemoteProtocol()
        remote = SimpleNamespace(_remote_message_protocol=protocol)

        text = install_text(remote)
        protocol.receive(ime_show_request(counter=41, value=""))

        assert text.field_focused is True
