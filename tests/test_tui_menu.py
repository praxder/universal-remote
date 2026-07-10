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

    def test_given_the_app_when_it_starts_then_the_title_is_universal_remote(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test():
                assert app.title == "Universal Remote"

        asyncio.run(scenario())

    def test_given_the_menu_when_shown_then_the_title_is_a_multiline_ascii_banner(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                title = app.screen.query_one("#title")
                assert "\n" in str(title.render())

        asyncio.run(scenario())

    def test_given_focus_on_manage_when_down_arrow_then_focus_moves_to_use(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#manage", Button))
                await pilot.press("down")
                assert app.focused is not None
                assert app.focused.id == "use"

        asyncio.run(scenario())

    def test_given_focus_on_use_when_up_arrow_then_focus_moves_to_manage(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#use", Button))
                await pilot.press("up")
                assert app.focused is not None
                assert app.focused.id == "manage"

        asyncio.run(scenario())

    def test_given_focus_on_use_when_down_arrow_then_focus_cycles_to_manage(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#use", Button))
                await pilot.press("down")
                assert app.focused is not None
                assert app.focused.id == "manage"

        asyncio.run(scenario())

    def test_given_focus_on_manage_when_up_arrow_then_focus_cycles_to_use(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#manage", Button))
                await pilot.press("up")
                assert app.focused is not None
                assert app.focused.id == "use"

        asyncio.run(scenario())

    def test_given_the_menu_when_shown_then_the_arrow_bindings_are_hidden_from_the_footer(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                bindings = app.screen.active_bindings
                assert bindings["up"].binding.show is False
                assert bindings["down"].binding.show is False

        asyncio.run(scenario())

    def test_given_the_menu_when_q_is_pressed_then_the_app_quits(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.press("q")
                await pilot.pause()
                assert app._exit is True

        asyncio.run(scenario())
