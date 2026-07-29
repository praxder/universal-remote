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


def _batch_edit(protocol: FakeRemoteProtocol):
    """The batch edit carried by the last message the seam sent."""
    return protocol.sent[-1].remote_ime_batch_edit


def _cursor(protocol: FakeRemoteProtocol) -> tuple[int, int]:
    status = _batch_edit(protocol).edit_info[0].text_field_status
    return status.start, status.end


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
        protocol = FakeRemoteProtocol(ime_counter=7)
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value=""))

        text.send("hi")

        assert _batch_edit(protocol).field_counter == 41

    def test_given_a_field_with_contents_when_text_is_sent_then_the_span_is_the_new_cursor(
        self,
    ):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value="abc"))

        text.send("de")

        assert _cursor(protocol) == (5, 5)  # len("abc") + len("de")

    def test_given_text_when_sent_then_the_edit_inserts_only_that_text(self):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value="abc"))

        text.send("de")

        edit = _batch_edit(protocol).edit_info[0]
        assert edit.text_field_status.value == "de"
        assert edit.insert == 1

    def test_given_a_later_report_when_text_is_sent_again_then_the_newer_counter_is_used(
        self,
    ):
        # The counter advances unpredictably (by 3 on a session's first edit, by 1
        # after), so it is re-read from the newest report rather than incremented.
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value=""))
        text.send("hi")

        protocol.receive(ime_show_request(counter=44, value="hi"))
        text.send("there")

        assert _batch_edit(protocol).field_counter == 44

    def test_given_a_first_send_when_a_second_follows_then_it_appends_after_it(self):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value=""))
        text.send("hi")

        protocol.receive(ime_show_request(counter=44, value="hi"))
        text.send("there")

        assert _cursor(protocol) == (7, 7)  # len("hi") + len("there")


class TestImeCounter:
    def test_given_a_reported_editor_counter_when_text_is_sent_then_the_edit_matches_it(
        self,
    ):
        # The device matches an edit against the focused editor's own counter, which
        # rides on the key-inject report — not the inbound batch edit, whose counter
        # is a fixed greeting of 1 on every surface.
        protocol = FakeRemoteProtocol(ime_counter=1)
        text = AndroidTvText(protocol)
        protocol.receive(ime_key_inject(counter=20, value="", app_counter=2))

        text.send("hi")

        assert _batch_edit(protocol).ime_counter == 2

    def test_given_a_newer_editor_counter_when_text_is_sent_then_the_newer_one_is_used(
        self,
    ):
        # Moving to another app re-reports it; the previous editor's value is stale.
        protocol = FakeRemoteProtocol(ime_counter=1)
        text = AndroidTvText(protocol)
        protocol.receive(ime_key_inject(counter=20, value="", app_counter=2))
        protocol.receive(ime_key_inject(counter=46, value="", app_counter=5))

        text.send("hi")

        assert _batch_edit(protocol).ime_counter == 5

    def test_given_no_editor_counter_reported_when_text_is_sent_then_the_greeting_is_used(
        self,
    ):
        # Only the show-request arrived, which carries no editor counter; falling back
        # to what the library tracked keeps the previously working surfaces working.
        protocol = FakeRemoteProtocol(ime_counter=1)
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=20, value=""))

        text.send("hi")

        assert _batch_edit(protocol).ime_counter == 1


class TestSendWithNoFocusedField:
    def test_given_no_field_focused_when_text_is_sent_then_text_unsupported_is_raised(
        self,
    ):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)

        with pytest.raises(TextUnsupportedError):
            text.send("hi")

    def test_given_no_field_focused_when_text_is_sent_then_nothing_goes_to_the_device(
        self,
    ):
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)

        with pytest.raises(TextUnsupportedError):
            text.send("hi")

        assert protocol.sent == []


class TestSendWithEmptyText:
    def test_given_a_focused_field_when_empty_text_is_sent_then_nothing_goes_out(self):
        # A macro step whose text is missing replays as "", which the library's own
        # send_text refused; refusing it here keeps a no-op edit off the wire.
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value="ab"))

        with pytest.raises(TextUnsupportedError):
            text.send("")

        assert protocol.sent == []


class TestOutboundMessages:
    def test_given_a_focused_field_when_text_is_sent_then_no_field_state_report_is_emitted(
        self,
    ):
        # Sending the device's own report back makes it reset both counters and tear
        # down the input-method session, so it must never leave the client.
        protocol = FakeRemoteProtocol()
        text = AndroidTvText(protocol)
        protocol.receive(ime_show_request(counter=41, value="ab"))

        text.send("cd")

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
