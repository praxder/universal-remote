import asyncio
from importlib.metadata import version

from textual.widgets import Button, Static

from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.settings_screen import (
    LICENSES_URL,
    REPO_URL,
    SettingsScreen,
)


def _app(tmp_path):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
        preferences=PreferencesStore(path=tmp_path / "settings.json"),
    )


class TestSettingsScreen:
    def test_given_the_settings_screen_when_shown_then_a_settings_banner_is_present(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                banner = app.screen.query_one("#settings-title")
                assert "\n" in str(banner.render())

        asyncio.run(scenario())

    def test_given_the_theme_row_when_activated_then_the_theme_picker_opens(
        self, tmp_path
    ):
        async def scenario():
            calls = []
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.search_themes = lambda: calls.append(True)
                app.push_screen(SettingsScreen())
                await pilot.pause()
                await pilot.click("#theme")
                await pilot.pause()
                assert calls == [True]

        asyncio.run(scenario())

    def test_given_the_licenses_row_when_activated_then_the_licenses_url_opens(
        self, tmp_path
    ):
        async def scenario():
            opened = []
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen(url_opener=opened.append))
                await pilot.pause()
                await pilot.click("#licenses")
                await pilot.pause()
                assert opened == [LICENSES_URL]

        asyncio.run(scenario())

    def test_given_the_repo_row_when_activated_then_the_repo_url_opens(self, tmp_path):
        async def scenario():
            opened = []
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen(url_opener=opened.append))
                await pilot.pause()
                await pilot.click("#repo")
                await pilot.pause()
                assert opened == [REPO_URL]

        asyncio.run(scenario())

    def test_given_the_key_bindings_row_when_shown_then_it_is_a_disabled_placeholder(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                assert app.screen.query_one("#keybindings", Button).disabled is True

        asyncio.run(scenario())

    def test_given_the_version_label_when_shown_then_it_displays_the_package_version(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                label = app.screen.query_one("#version", Static)
                assert version("universal-remote") in str(label.render())

        asyncio.run(scenario())

    def test_given_the_version_label_when_shown_then_it_cannot_be_focused(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                assert app.screen.query_one("#version", Static).can_focus is False

        asyncio.run(scenario())

    def test_given_the_settings_screen_when_escape_is_pressed_then_it_returns_to_the_menu(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())

    def test_given_the_settings_screen_when_q_is_pressed_then_it_returns_to_the_menu(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                await pilot.press("q")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())
