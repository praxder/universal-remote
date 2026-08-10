import asyncio

from textual.widgets import DataTable, Input

from tests.fakes import FakeAdapter
from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import AddDeviceScreen, DeviceListScreen
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

    def test_given_the_menu_when_ctrl_q_is_pressed_then_the_app_quits(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=_SIZE) as pilot:
                await pilot.press("ctrl+q")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())
