import asyncio
import time

from textual.widgets import DataTable, Input

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import AddDeviceScreen, DeviceListScreen
from universal_remote.tui.remote_screen import RemoteScreen, TextEntryModal
from universal_remote.tui.shortcuts_screen import CaptureModal, ShortcutsScreen

_SIZE = (100, 50)


def _app(tmp_path, store=None, adapter=None):
    registry = AdapterRegistry()
    # Add Device and the remote both need a registered platform.
    registry.register(adapter or FakeAdapter(platform="fake-tv"))
    return UniversalRemoteApp(
        store=store or DeviceStore(path=tmp_path / "d.json"),
        registry=registry,
        preferences=PreferencesStore(path=tmp_path / "settings.json"),
    )


def _store_with_device(tmp_path):
    store = DeviceStore(path=tmp_path / "d.json")
    store.add(Device(name="TV", platform="fake-tv", ip="1.1.1.1", credential="tok"))
    return store


async def _goto_remote(app, pilot):
    """Connect to the saved device and return the remote's live session."""
    await pilot.press("r")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(app.screen, RemoteScreen)
    return app.screen._session


class TestCtrlCQuits:
    def test_given_the_menu_when_ctrl_c_is_pressed_then_the_app_quits(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.press("ctrl+c")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())

    def test_given_a_non_menu_screen_when_ctrl_c_is_pressed_then_the_app_quits(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

                await pilot.press("ctrl+c")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())

    def test_given_a_focused_text_input_when_ctrl_c_is_pressed_then_the_app_quits(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(AddDeviceScreen())
                await pilot.pause()
                app.screen.query_one("#name", Input).focus()
                await pilot.pause()

                await pilot.press("ctrl+c")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())

    def test_given_the_capture_modal_when_ctrl_c_is_pressed_then_the_app_quits(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                app.push_screen(ShortcutsScreen())
                await pilot.pause()
                table = app.screen.query_one(DataTable)
                table.move_cursor(row=table.get_row_index("home.manage_devices"))
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, CaptureModal)

                await pilot.press("ctrl+c")
                await pilot.pause()
                assert app._exit is True
                assert app.shortcut_overrides == {}  # captured nothing on the way out

        asyncio.run(scenario())

    def test_given_the_remote_when_ctrl_c_is_pressed_then_the_device_session_closes(
        self, tmp_path
    ):
        # Only Go Back used to close the live session, so quitting from the remote
        # left the adapter's HTTP client session open — aiohttp then printed
        # "Unclosed client session" after the app exited.
        store = _store_with_device(tmp_path)

        async def scenario():
            app = _app(tmp_path, store=store)
            async with app.run_test(size=_SIZE) as pilot:
                session = await _goto_remote(app, pilot)

                await pilot.press("ctrl+c")
                await pilot.pause()
            return session  # asserted after shutdown, which is where teardown runs

        session = asyncio.run(scenario())

        assert session.closed is True

    def test_given_a_modal_over_the_remote_when_ctrl_c_quits_then_the_session_closes(
        self, tmp_path
    ):
        # The remote is not the top screen here, so its teardown happens further down
        # the stack — the session must still be released.
        store = _store_with_device(tmp_path)

        async def scenario():
            app = _app(tmp_path, store=store)
            async with app.run_test(size=_SIZE) as pilot:
                session = await _goto_remote(app, pilot)
                await pilot.press("t")  # the text-entry modal, over the remote
                await pilot.pause()
                assert isinstance(app.screen, TextEntryModal)

                await pilot.press("ctrl+c")
                await pilot.pause()
            return session

        session = asyncio.run(scenario())

        assert session.closed is True

    def test_given_a_failing_session_close_when_ctrl_c_quits_then_the_app_still_exits(
        self, tmp_path
    ):
        # A device that went away raises on close. This runs during shutdown, outside
        # the app's error net, so an unguarded release would dump a traceback into the
        # terminal after the app exits — the very thing closing the session prevents.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(tmp_path, store=store, adapter=adapter)
            async with app.run_test(size=_SIZE) as pilot:
                session = await _goto_remote(app, pilot)
                session.close_error = OSError("device went away")

                await pilot.press("ctrl+c")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())  # the raising close must not escape shutdown

    def test_given_a_hanging_session_close_when_ctrl_c_quits_then_it_is_abandoned(
        self, tmp_path
    ):
        # A websocket close to a sleeping TV can block; quitting must not wait on it.
        store = _store_with_device(tmp_path)

        async def scenario():
            app = _app(tmp_path, store=store)
            async with app.run_test(size=_SIZE) as pilot:
                session = await _goto_remote(app, pilot)
                session.close_delay = RemoteScreen.CLOSE_TIMEOUT * 3

                await pilot.press("ctrl+c")
                await pilot.pause()
            return session

        started = time.monotonic()
        session = asyncio.run(scenario())
        elapsed = time.monotonic() - started

        assert session.closed is False  # the release was abandoned, not awaited
        assert elapsed < RemoteScreen.CLOSE_TIMEOUT * 3

    def test_given_the_menu_when_ctrl_q_is_pressed_then_the_app_quits(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.press("ctrl+q")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())
