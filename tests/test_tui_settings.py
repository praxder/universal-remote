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
from universal_remote.tui.shortcuts_screen import ShortcutsScreen


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
            async with app.run_test(size=(100, 40)) as pilot:
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
            async with app.run_test(size=(100, 40)) as pilot:
                app.push_screen(SettingsScreen(url_opener=opened.append))
                await pilot.pause()
                await pilot.click("#repo")
                await pilot.pause()
                assert opened == [REPO_URL]

        asyncio.run(scenario())

    def test_given_the_keyboard_shortcuts_row_when_shown_then_it_is_enabled(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                assert app.screen.query_one("#keybindings", Button).disabled is False

        asyncio.run(scenario())

    def test_given_the_keyboard_shortcuts_row_when_activated_then_the_screen_opens(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test(size=(100, 50)) as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                await pilot.click("#keybindings")
                await pilot.pause()
                assert isinstance(app.screen, ShortcutsScreen)

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

    def test_given_focus_on_theme_when_j_then_focus_moves_to_the_shortcuts_row(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#theme", Button))
                await pilot.press("j")
                assert app.focused is not None
                assert app.focused.id == "keybindings"

        asyncio.run(scenario())

    def test_given_focus_on_theme_when_k_then_focus_cycles_to_the_last_row(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#theme", Button))
                await pilot.press("k")
                assert app.focused is not None
                assert app.focused.id == "repo"

        asyncio.run(scenario())

    def test_given_focus_on_repo_when_l_then_focus_cycles_to_theme(self, tmp_path):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                app.push_screen(SettingsScreen())
                await pilot.pause()
                app.screen.set_focus(app.screen.query_one("#repo", Button))
                await pilot.press("l")
                assert app.focused is not None
                assert app.focused.id == "theme"

        asyncio.run(scenario())
