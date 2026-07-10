import asyncio

from textual.widgets import Button

from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import DeviceListScreen
from universal_remote.tui.remote_flow import UseRemoteScreen


def _app(tmp_path):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"), registry=AdapterRegistry()
    )


class TestMenu:
    def test_given_the_app_starts_when_the_menu_shows_then_both_modes_are_present(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                labels = {str(button.label) for button in app.screen.query(Button)}
                assert "Manage Devices" in labels
                assert "Use Remote" in labels

        asyncio.run(scenario())

    def test_given_the_menu_when_the_devices_key_is_pressed_then_it_navigates_there(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

    def test_given_the_menu_when_use_remote_is_clicked_then_it_navigates_there(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.click("#use")
                await pilot.pause()
                assert isinstance(app.screen, UseRemoteScreen)

        asyncio.run(scenario())
