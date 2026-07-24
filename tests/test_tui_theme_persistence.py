import asyncio

from textual.constants import DEFAULT_THEME

from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import Preferences, PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import DeviceListScreen
from universal_remote.tui.menu import MenuScreen


def _app(tmp_path, preferences=None):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
        preferences=preferences or PreferencesStore(path=tmp_path / "settings.json"),
    )


class TestThemePersistence:
    def test_given_the_app_when_the_theme_changes_then_it_is_saved(self, tmp_path):
        async def scenario():
            prefs = PreferencesStore(path=tmp_path / "settings.json")
            app = _app(tmp_path, preferences=prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.theme = "gruvbox"
                await pilot.pause()
                assert prefs.load().theme == "gruvbox"

        asyncio.run(scenario())

    def test_given_a_saved_theme_when_the_app_launches_then_it_is_applied(
        self, tmp_path
    ):
        async def scenario():
            prefs = PreferencesStore(path=tmp_path / "settings.json")
            prefs.save(Preferences(theme="nord"))
            app = _app(tmp_path, preferences=prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.theme == "nord"

        asyncio.run(scenario())

    def test_given_no_saved_theme_when_the_app_launches_then_the_default_is_used(
        self, tmp_path
    ):
        async def scenario():
            app = _app(tmp_path)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.theme == DEFAULT_THEME

        asyncio.run(scenario())

    def test_given_an_unknown_saved_theme_when_the_app_launches_then_the_default_is_used(
        self, tmp_path
    ):
        async def scenario():
            prefs = PreferencesStore(path=tmp_path / "settings.json")
            prefs.save(Preferences(theme="no-such-theme"))
            app = _app(tmp_path, preferences=prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.theme == DEFAULT_THEME

        asyncio.run(scenario())

    def test_given_a_saved_shortcut_when_the_app_launches_then_it_is_applied(
        self, tmp_path
    ):
        async def scenario():
            prefs = PreferencesStore(path=tmp_path / "settings.json")
            prefs.save(Preferences(shortcuts={"home.manage_devices": "x"}))
            app = _app(tmp_path, preferences=prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("x")  # the custom key works from launch
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

    def test_given_a_saved_theme_and_shortcut_when_saving_a_theme_then_shortcut_stays(
        self, tmp_path
    ):
        async def scenario():
            prefs = PreferencesStore(path=tmp_path / "settings.json")
            prefs.save(Preferences(theme="nord", shortcuts={"remote.vol_up": "v"}))
            app = _app(tmp_path, preferences=prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.theme = "gruvbox"  # changing the theme must not drop shortcuts
                await pilot.pause()
                reloaded = prefs.load()
                assert reloaded.theme == "gruvbox"
                assert reloaded.shortcuts == {"remote.vol_up": "v"}

        asyncio.run(scenario())

    def test_given_the_startup_theme_save_fails_when_launching_then_the_app_still_starts(
        self, tmp_path
    ):
        async def scenario():
            path = tmp_path / "settings.json"
            prefs = PreferencesStore(path=path)
            prefs.save(Preferences(theme="nord"))
            path.chmod(0o444)  # read-only: the startup re-save write will fail
            app = _app(tmp_path, preferences=prefs)
            try:
                async with app.run_test() as pilot:
                    await pilot.pause()
                    assert app.theme == "nord"
                    assert isinstance(app.screen, MenuScreen)
            finally:
                path.chmod(0o644)

        asyncio.run(scenario())
