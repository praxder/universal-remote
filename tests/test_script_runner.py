import asyncio
import os
import stat

from universal_remote.tui.actions import ScriptResult, run_script


def _inline(script: str) -> dict:
    return {"type": "run_script", "source": "inline", "script": script}


def _file(path: str) -> dict:
    return {"type": "run_script", "source": "file", "script": path}


class TestRunScriptOutcome:
    def test_given_a_successful_inline_script_when_run_then_it_reports_success(self):
        result = asyncio.run(run_script(_inline("exit 0"), "10.0.0.5"))

        assert isinstance(result, ScriptResult)
        assert result.ok is True
        assert result.exit_code == 0

    def test_given_a_nonzero_inline_script_when_run_then_it_reports_the_exit_code(self):
        result = asyncio.run(run_script(_inline("exit 7"), "10.0.0.5"))

        assert result.ok is False
        assert result.exit_code == 7

    def test_given_stdout_when_run_then_it_is_captured(self):
        result = asyncio.run(run_script(_inline("printf hello"), "10.0.0.5"))

        assert result.stdout == "hello"

    def test_given_stderr_when_run_then_it_is_captured(self):
        result = asyncio.run(run_script(_inline("printf oops 1>&2"), "10.0.0.5"))

        assert result.stderr == "oops"


class TestRemoteIp:
    def test_given_a_device_ip_when_run_then_remote_ip_is_in_the_environment(self):
        # The script echoes its own REMOTE_IP; the runner must have injected it.
        result = asyncio.run(run_script(_inline('printf "%s" "$REMOTE_IP"'), "1.2.3.4"))

        assert result.stdout == "1.2.3.4"

    def test_given_a_run_when_started_then_remote_ip_is_the_only_injected_value(self):
        # A variable the app does not inject and the environment does not hold must be
        # empty, proving REMOTE_IP is added but nothing else is fabricated.
        os.environ.pop("UR_SHOULD_NOT_EXIST", None)
        result = asyncio.run(
            run_script(_inline('printf "%s" "$UR_SHOULD_NOT_EXIST"'), "1.2.3.4")
        )

        assert result.stdout == ""


class TestTimeout:
    def test_given_a_hung_script_when_the_timeout_elapses_then_it_fails(self):
        # A tiny timeout stands in for the fixed 30s guard so the test stays fast.
        result = asyncio.run(run_script(_inline("sleep 30"), "10.0.0.5", timeout=0.2))

        assert result.ok is False
        assert "timed out" in result.message.lower()

    def test_given_a_hung_script_when_terminated_then_it_does_not_block_for_its_full_run(
        self,
    ):
        # The kill-and-reap path returns promptly rather than waiting out the sleep.
        async def scenario():
            return await asyncio.wait_for(
                run_script(_inline("sleep 30"), "10.0.0.5", timeout=0.2), timeout=5
            )

        result = asyncio.run(scenario())  # must not raise asyncio.TimeoutError

        assert result.ok is False


class TestUnstartableScript:
    def test_given_a_missing_file_path_when_run_then_it_fails_without_raising(self):
        result = asyncio.run(run_script(_file("/no/such/script/here"), "10.0.0.5"))

        assert result.ok is False
        assert result.message  # a human-readable failure reason, not an exception

    def test_given_an_existing_script_file_when_run_then_it_executes(self, tmp_path):
        # Arrange: a real executable script that prints its injected REMOTE_IP.
        script = tmp_path / "run.sh"
        script.write_text('#!/bin/sh\nprintf "%s" "$REMOTE_IP"\n')
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

        result = asyncio.run(run_script(_file(str(script)), "9.9.9.9"))

        assert result.ok is True
        assert result.stdout == "9.9.9.9"

    def test_given_a_file_without_shebang_or_exec_bit_when_run_then_it_still_runs(
        self, tmp_path
    ):
        # A plain shell file with no shebang and no execute permission: exec-ing it
        # directly would fail with "Exec format error", but the runner invokes it
        # through the shell so it still runs.
        script = tmp_path / "plain.sh"
        script.write_text('printf "%s" "$REMOTE_IP"\n')

        result = asyncio.run(run_script(_file(str(script)), "5.5.5.5"))

        assert result.ok is True
        assert result.stdout == "5.5.5.5"

    def test_given_a_tilde_path_when_run_then_the_home_prefix_is_expanded(
        self, tmp_path, monkeypatch
    ):
        # A `~/...` path is expanded against HOME so a user's stored tilde path runs.
        monkeypatch.setenv("HOME", str(tmp_path))
        (tmp_path / "tilde.sh").write_text("printf ok\n")

        result = asyncio.run(run_script(_file("~/tilde.sh"), "1.1.1.1"))

        assert result.ok is True
        assert result.stdout == "ok"
