import asyncio

from textual.widgets import Label

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.errors import ConnectionFailedError
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.remote_flow import ConnectingModal


def _app(adapter, tmp_path):
    registry = AdapterRegistry()
    registry.register(adapter)
    store = DeviceStore(path=tmp_path / "d.json")
    return UniversalRemoteApp(store=store, registry=registry)


def _dev(**overrides) -> Device:
    base = dict(name="TV", platform="fake-tv", ip="1.1.1.1", credential="tok")
    base.update(overrides)
    return Device(**base)


class TestConnectingModalSuccess:
    def test_given_a_reachable_device_when_connecting_then_it_dismisses_with_a_session(
        self, tmp_path
    ):
        adapter = FakeAdapter(platform="fake-tv")
        result: dict = {}

        async def scenario():
            app = _app(adapter, tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(
                    ConnectingModal(_dev()),
                    lambda session: result.__setitem__("session", session),
                )
                await pilot.pause()
                await pilot.pause()

        asyncio.run(scenario())

        assert result.get("session") is not None
        assert len(adapter.sessions) == 1


class TestConnectingModalFailure:
    def test_given_a_failing_adapter_when_connecting_then_the_error_state_names_the_device(
        self, tmp_path
    ):
        adapter = FakeAdapter(
            platform="fake-tv", connect_error=ConnectionFailedError("unreachable")
        )

        async def scenario():
            app = _app(adapter, tmp_path)
            async with app.run_test() as pilot:
                modal = ConnectingModal(_dev(name="Living Room"))
                app.push_screen(modal)
                await pilot.pause()
                await pilot.pause()
                message = str(modal.query_one("#connect-error", Label).content)
                assert "Living Room" in message
                assert isinstance(app.screen, ConnectingModal)

        asyncio.run(scenario())


class TestConnectingModalRetry:
    def test_given_a_failure_when_retry_pressed_then_it_reattempts_and_succeeds(
        self, tmp_path
    ):
        adapter = FakeAdapter(
            platform="fake-tv", connect_error=ConnectionFailedError("unreachable")
        )
        result: dict = {}

        async def scenario():
            app = _app(adapter, tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(
                    ConnectingModal(_dev()),
                    lambda session: result.__setitem__("session", session),
                )
                await pilot.pause()
                await pilot.pause()
                adapter.connect_error = None  # the device is reachable now
                await pilot.click("#retry")
                await pilot.pause()
                await pilot.pause()

        asyncio.run(scenario())

        assert result.get("session") is not None


class TestConnectingModalCancel:
    def test_given_a_connect_in_flight_when_cancelled_then_it_dismisses_with_no_session(
        self, tmp_path
    ):
        adapter = FakeAdapter(platform="fake-tv")
        captured: dict = {}

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # keep the connect pending
            app = _app(adapter, tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(
                    ConnectingModal(_dev()),
                    lambda session: captured.__setitem__("session", session),
                )
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(scenario())

        assert "session" in captured
        assert captured["session"] is None
        assert adapter.sessions == []
