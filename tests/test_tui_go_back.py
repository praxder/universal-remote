import asyncio

from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import DeviceListScreen
from universal_remote.tui.discover_screen import DiscoverScreen
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.remote_flow import UseRemoteScreen
from universal_remote.tui.settings_screen import SettingsScreen


def _app(tmp_path):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
    )


class TestGoBackDefault:
    def test_given_the_devices_screen_when_escape_pressed_then_it_returns_to_the_menu(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())

    def test_given_the_discover_screen_when_escape_pressed_then_it_returns_to_devices(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("a")  # + Add opens Discover
                await pilot.pause()
                assert isinstance(app.screen, DiscoverScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

    def test_given_the_use_remote_picker_when_escape_pressed_then_it_returns_to_menu(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                assert isinstance(app.screen, UseRemoteScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())

    def test_given_the_settings_screen_when_escape_pressed_then_it_returns_to_menu(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("s")
                await pilot.pause()
                assert isinstance(app.screen, SettingsScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())


class TestGoBackRebound:
    def test_given_go_back_rebound_when_the_new_key_pressed_then_it_returns(
        self, tmp_path
    ):
        app = _app(tmp_path)
        app.shortcut_overrides["global.go_back"] = "b"

        async def scenario():
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                await pilot.press("b")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())

    def test_given_go_back_rebound_when_escape_pressed_then_nothing_happens(
        self, tmp_path
    ):
        app = _app(tmp_path)
        app.shortcut_overrides["global.go_back"] = "b"

        async def scenario():
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("escape")  # the old Go Back key no longer fires
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())
