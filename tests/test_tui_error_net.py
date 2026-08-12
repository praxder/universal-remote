import asyncio

import pytest
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button

import universal_remote.tui.remote_flow as remote_flow
from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.errors import ConnectionFailedError
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.discover_screen import DiscoverScreen
from universal_remote.tui.remote_flow import UseRemoteScreen


def _app(tmp_path) -> UniversalRemoteApp:
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"), registry=AdapterRegistry()
    )


async def _boom() -> None:
    raise RuntimeError("worker boom")


class _BoomScreen(Screen):
    """A screen whose message handler raises, to drive a handler failure."""

    def compose(self) -> ComposeResult:
        yield Button("go", id="go")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        raise RuntimeError("handler boom")


def _severities(app) -> list[str]:
    return [n.severity for n in app._notifications]


class TestWorkerErrorNet:
    def test_given_a_worker_error_while_running_then_app_stays_open_with_error_toast(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.run_worker(_boom())
                await pilot.pause()
                await pilot.pause()
                captured["running"] = app.is_running
                captured["severities"] = _severities(app)

        # The net keeps the bookkeeping so run_test() re-raises at teardown
        # (tests still surface bugs); absorb that here.
        with pytest.raises(Exception):
            asyncio.run(scenario())

        assert captured.get("running") is True
        assert "error" in captured.get("severities", [])


class TestMessageHandlerErrorNet:
    def test_given_a_handler_error_while_running_then_app_stays_open_with_error_toast(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(_BoomScreen())
                await pilot.pause()
                await pilot.click("#go")
                await pilot.pause()
                await pilot.pause()
                captured["running"] = app.is_running
                captured["severities"] = _severities(app)

        with pytest.raises(Exception):
            asyncio.run(scenario())

        assert captured.get("running") is True
        assert "error" in captured.get("severities", [])


class TestErrorLogged:
    def test_given_a_caught_error_then_its_traceback_is_written_to_the_log_file(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.run_worker(_boom())
                await pilot.pause()
                await pilot.pause()

        with pytest.raises(Exception):
            asyncio.run(scenario())

        log = tmp_path / "universal-remote" / "error.log"
        assert log.exists()
        contents = log.read_text()
        assert "RuntimeError" in contents
        assert "Traceback" in contents


class _StartupBoomApp(UniversalRemoteApp):
    """An app whose own compose fails, standing in for a startup/mount error."""

    def compose(self) -> ComposeResult:
        raise RuntimeError("startup boom")
        yield  # pragma: no cover - makes compose a generator


class TestStartupErrorStillExits:
    def test_given_a_compose_error_before_mount_then_the_net_does_not_keep_it_open(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            app = _StartupBoomApp(
                store=DeviceStore(path=tmp_path / "d.json"),
                registry=AdapterRegistry(),
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                captured["severities"] = _severities(app)

        with pytest.raises(Exception):
            asyncio.run(scenario())

        # A mounted error toasts (see TestWorkerErrorNet); a pre-mount compose
        # error must instead fall through to teardown, posting no error toast.
        assert "error" not in captured.get("severities", [])


class TestBookkeepingPreserved:
    def test_given_a_caught_error_then_exception_is_recorded_so_tests_surface_bugs(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.run_worker(_boom())
                await pilot.pause()
                await pilot.pause()
                captured["exception_recorded"] = app._exception is not None

        with pytest.raises(Exception):
            asyncio.run(scenario())

        assert captured.get("exception_recorded") is True


class TestProbeStaysOffNet:
    def test_given_a_failing_probe_then_no_error_toast_and_app_stays_open(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        async def boom_probe(ip, port, timeout):
            raise RuntimeError("probe boom")

        monkeypatch.setattr(remote_flow, "probe", boom_probe)
        captured: dict = {}

        async def scenario():
            store = DeviceStore(path=tmp_path / "d.json")
            store.add(Device(name="TV", platform="fake-tv", ip="1.1.1.1"))
            registry = AdapterRegistry()
            registry.register(FakeAdapter(platform="fake-tv", reachability_port=9999))
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(UseRemoteScreen())
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()
                captured["severities"] = _severities(app)
                captured["running"] = app.is_running

        asyncio.run(scenario())

        assert "error" not in captured.get("severities", [])
        assert captured.get("running") is True


class _BoomDiscoverAdapter:
    """A discovery adapter whose scan raises, to prove the scan seam is isolated."""

    platform = "boom-tv"
    display_name = "Boom TV"

    async def discover(self, timeout: float) -> list:
        raise RuntimeError("scan boom")


class TestDiscoveryScanStaysOffNet:
    def test_given_a_failing_scan_then_no_error_toast_and_app_stays_open(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            store = DeviceStore(path=tmp_path / "d.json")
            registry = AdapterRegistry()
            registry.register(_BoomDiscoverAdapter())
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                captured["severities"] = _severities(app)
                captured["running"] = app.is_running

        asyncio.run(scenario())

        assert "error" not in captured.get("severities", [])
        assert captured.get("running") is True


class TestNetNeverCrashesOnItsOwnLogging:
    def test_given_an_unwritable_log_dir_then_a_handler_error_still_does_not_crash(
        self, monkeypatch, tmp_path
    ):
        # Arrange: point the log dir under a regular file so mkdir/open raises —
        # standing in for an unwritable or full config directory.
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(blocker / "x"))
        captured: dict = {}

        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(_BoomScreen())
                await pilot.pause()
                await pilot.click("#go")
                await pilot.pause()
                await pilot.pause()
                captured["running"] = app.is_running

        # The net must never crash on its own logging: the app stays up, and the
        # only thing re-raised at teardown is the original handler error.
        with pytest.raises(RuntimeError):
            asyncio.run(scenario())

        assert captured.get("running") is True


class TestExpectedDomainErrorMessage:
    def test_given_a_domain_error_then_its_own_message_is_shown_verbatim(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        captured: dict = {}

        async def scenario():
            app = _app(tmp_path)

            async def raise_domain() -> None:
                raise ConnectionFailedError("device is unreachable")

            async with app.run_test() as pilot:
                app.run_worker(raise_domain())
                await pilot.pause()
                await pilot.pause()
                captured["messages"] = [n.message for n in app._notifications]

        with pytest.raises(Exception):
            asyncio.run(scenario())

        assert any("device is unreachable" in m for m in captured.get("messages", []))
