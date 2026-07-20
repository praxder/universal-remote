import asyncio

import pytest

from tests.fakes import FAKE_MDNS_SERVICES, FakeAdbRunner
from universal_remote.adapters.adb_text import (
    AdbError,
    AdbText,
    build_input_text_command,
    escape_for_input_text,
)


def run(coro):
    return asyncio.run(coro)


class TestEscapeForInputText:
    def test_given_a_plain_word_when_escaped_then_it_is_unchanged(self):
        assert escape_for_input_text("hello") == "hello"

    def test_given_spaces_when_escaped_then_they_become_percent_s(self):
        assert escape_for_input_text("hello world") == "hello%sworld"

    def test_given_shell_special_characters_when_escaped_then_they_are_backslashed(
        self,
    ):
        assert escape_for_input_text("a&b|c;d") == "a\\&b\\|c\\;d"

    def test_given_a_dollar_sign_when_escaped_then_it_is_backslashed(self):
        assert escape_for_input_text("$HOME") == "\\$HOME"


class TestBuildInputTextCommand:
    def test_given_plain_text_when_built_then_a_single_input_text_call(self):
        assert build_input_text_command("hi there") == "input text hi%sthere"

    def test_given_a_literal_percent_s_when_built_then_it_is_split_across_calls(self):
        # Android's `input text` collapses "%s" to a space, so a literal "%s" must
        # be split between the % and the s across separate calls to survive.
        assert build_input_text_command("50%s") == "input text 50\\%; input text s"


class TestResolveTarget:
    def test_given_the_device_answers_mdns_when_resolving_then_the_connect_address_returns(
        self,
    ):
        runner = FakeAdbRunner(mdns_output=FAKE_MDNS_SERVICES)
        adb = AdbText(runner)

        target = run(adb.resolve_target("10.0.0.5"))

        # The tls-connect row, not the tls-pairing row on the same IP.
        assert target == "10.0.0.5:37451"

    def test_given_resolution_when_run_then_it_queries_mdns_services(self):
        runner = FakeAdbRunner(mdns_output=FAKE_MDNS_SERVICES)
        adb = AdbText(runner)

        run(adb.resolve_target("10.0.0.5"))

        assert runner.calls == [["mdns", "services"]]

    def test_given_the_device_is_absent_from_mdns_when_resolving_then_none_returns(
        self,
    ):
        runner = FakeAdbRunner(mdns_output=FAKE_MDNS_SERVICES)
        adb = AdbText(runner)

        assert run(adb.resolve_target("10.0.0.200")) is None


class TestSendText:
    def test_given_a_target_when_sending_then_it_connects_then_types_escaped_text(self):
        runner = FakeAdbRunner()
        adb = AdbText(runner)

        run(adb.send_text("10.0.0.5:37451", "hi there"))

        assert runner.calls == [
            ["connect", "10.0.0.5:37451"],
            ["-s", "10.0.0.5:37451", "shell", "input text hi%sthere"],
        ]

    def test_given_a_literal_percent_s_when_sending_then_the_command_is_split(self):
        runner = FakeAdbRunner()
        adb = AdbText(runner)

        run(adb.send_text("10.0.0.5:37451", "50%s"))

        assert runner.calls == [
            ["connect", "10.0.0.5:37451"],
            ["-s", "10.0.0.5:37451", "shell", "input text 50\\%; input text s"],
        ]

    def test_given_the_connect_fails_when_sending_then_adb_error_is_raised(self):
        runner = FakeAdbRunner(fail={"connect"})
        adb = AdbText(runner)

        with pytest.raises(AdbError):
            run(adb.send_text("10.0.0.5:37451", "hello"))


class TestPair:
    def test_given_a_passing_pairing_when_run_then_the_exact_argv_is_used_and_true_returns(
        self,
    ):
        runner = FakeAdbRunner()
        adb = AdbText(runner)

        ok = run(adb.pair("10.0.0.5", "42133", "123456"))

        assert ok is True
        assert runner.calls == [["pair", "10.0.0.5:42133", "123456"]]

    def test_given_a_failing_pairing_when_run_then_false_returns(self):
        runner = FakeAdbRunner(fail={"pair"})
        adb = AdbText(runner)

        assert run(adb.pair("10.0.0.5", "42133", "000000")) is False
