from pathlib import Path

from universal_remote.error_log import default_log_path, log_exception


class TestDefaultLogPath:
    def test_given_xdg_config_home_when_resolving_then_path_is_under_it(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        path = default_log_path()

        assert path == tmp_path / "universal-remote" / "error.log"

    def test_given_no_xdg_config_home_when_resolving_then_it_falls_back_to_dot_config(
        self, monkeypatch
    ):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        path = default_log_path()

        assert path == Path.home() / ".config" / "universal-remote" / "error.log"


class TestLogException:
    def test_given_a_raised_exception_when_logged_then_type_message_and_traceback_are_written(
        self, tmp_path
    ):
        # Arrange: a real exception carrying a traceback.
        path = tmp_path / "error.log"
        try:
            raise ValueError("boom detail")
        except ValueError as error:
            # Act
            log_exception(error, path=path)

        # Assert
        contents = path.read_text()
        assert "ValueError" in contents
        assert "boom detail" in contents
        assert "Traceback" in contents

    def test_given_no_log_dir_when_logged_then_parent_is_created(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "error.log"

        log_exception(RuntimeError("x"), path=path)

        assert path.exists()
