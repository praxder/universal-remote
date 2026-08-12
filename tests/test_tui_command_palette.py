import asyncio

from textual.widgets import Button

from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp


def _app(tmp_path):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
    )


def _palette_titles(app):
    return {command.title for command in app.get_system_commands(app.screen)}


class TestCommandPalette:
    def test_given_the_palette_when_opened_then_it_lists_only_theme_quit_and_keys(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#manage", Button))
                assert _palette_titles(app) == {"Theme", "Quit", "Keys"}

        asyncio.run(scenario())

    def test_given_the_palette_when_opened_then_maximize_is_excluded(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#manage", Button))
                assert "Maximize" not in _palette_titles(app)

        asyncio.run(scenario())

    def test_given_the_palette_when_opened_then_screenshot_is_excluded(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert "Screenshot" not in _palette_titles(app)

        asyncio.run(scenario())
