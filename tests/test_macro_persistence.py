import asyncio

from universal_remote.devices.store import DeviceStore
from universal_remote.macros.models import Macro, key_step
from universal_remote.macros.registry import add, create, get, list_macros
from universal_remote.preferences.store import Preferences, PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp


def _app(tmp_path, preferences):
    return UniversalRemoteApp(
        store=DeviceStore(path=tmp_path / "d.json"),
        registry=AdapterRegistry(),
        preferences=preferences,
    )


def _registry_with(name: str) -> dict:
    """A saved registry holding one macro of one key step."""
    macros: dict = {}
    macro = create(macros, [key_step("HOME")])
    macro.name = name
    add(macros, macro)
    return macros


class TestMacrosLoadedAtStartup:
    def test_given_saved_macros_when_the_app_launches_then_they_are_available(
        self, tmp_path
    ):
        # Arrange
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        prefs.save(Preferences(macros=_registry_with("Login")))

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()

                # Assert: the registry is on the app, with its name and steps.
                macros = list_macros(app.macros)
                assert [macro.name for macro in macros] == ["Login"]
                assert macros[0].steps == [key_step("HOME")]

        asyncio.run(scenario())

    def test_given_no_saved_macros_when_the_app_launches_then_the_registry_is_empty(
        self, tmp_path
    ):
        prefs = PreferencesStore(path=tmp_path / "settings.json")

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert list_macros(app.macros) == []

        asyncio.run(scenario())

    def test_given_a_changed_default_pause_when_relaunched_then_it_is_still_held(
        self, tmp_path
    ):
        # The pacing rides inside the macro body already round-tripping under the
        # `macros` key, so the persistence chain itself needs nothing added.
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        saved: dict = {}
        macro = create(saved, [key_step("HOME")])
        macro.step_pause_ms = 1200
        add(saved, macro)
        prefs.save(Preferences(macros=saved))

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()

                assert get(app.macros, macro.id).step_pause_ms == 1200

        asyncio.run(scenario())

    def test_given_two_saved_macros_when_relaunched_then_the_counter_continues(
        self, tmp_path
    ):
        # The default-name counter rides in the persisted registry, so the next macro
        # recorded after a restart is `Macro 3` rather than reusing `Macro 1`.
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        saved: dict = {}
        create(saved, [])
        create(saved, [])
        prefs.save(Preferences(macros=saved))

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert create(app.macros, []).name == "Macro 3"

        asyncio.run(scenario())


class TestMacrosSurviveOtherWrites:
    def test_given_a_saved_macro_when_the_theme_changes_then_the_macro_survives(
        self, tmp_path
    ):
        # The guard on the one link that silently eats data: `persist_preferences`
        # rebuilds Preferences from keyword arguments and `watch_theme` calls it on
        # every theme change, so omitting `macros=` would erase every macro.
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        prefs.save(Preferences(macros=_registry_with("Login")))

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()

                app.theme = "gruvbox"
                await pilot.pause()

                reloaded = prefs.load()
                assert [m.name for m in list_macros(reloaded.macros)] == ["Login"]

        asyncio.run(scenario())

    def test_given_every_preference_saved_when_relaunched_then_all_of_them_apply(
        self, tmp_path
    ):
        # Theme, shortcuts, custom buttons, and macros coexist across a restart, and
        # saving one does not overwrite the others.
        prefs = PreferencesStore(path=tmp_path / "settings.json")
        prefs.save(
            Preferences(
                theme="nord",
                shortcuts={"remote.vol_up": "v"},
                custom_buttons={"global": {"1": {"title": "Reboot"}}},
                macros=_registry_with("Login"),
            )
        )

        async def scenario():
            app = _app(tmp_path, prefs)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.theme == "nord"
                assert app.shortcut_overrides == {"remote.vol_up": "v"}
                assert app.custom_buttons == {"global": {"1": {"title": "Reboot"}}}
                assert [m.name for m in list_macros(app.macros)] == ["Login"]

                # A later write of one preference keeps every other one.
                add(app.macros, Macro(name="Second"))
                app.persist_preferences()
                await pilot.pause()

                reloaded = prefs.load()
                assert reloaded.theme == "nord"
                assert reloaded.shortcuts == {"remote.vol_up": "v"}
                assert reloaded.custom_buttons == {"global": {"1": {"title": "Reboot"}}}
                assert sorted(m.name for m in list_macros(reloaded.macros)) == [
                    "Login",
                    "Second",
                ]

        asyncio.run(scenario())

    def test_given_an_unwritable_settings_file_when_a_macro_is_saved_then_it_is_ignored(
        self, tmp_path
    ):
        # A best-effort write: an unwritable configuration file must not crash the app.
        path = tmp_path / "settings.json"
        prefs = PreferencesStore(path=path)
        prefs.save(Preferences())
        path.chmod(0o444)

        async def scenario():
            app = _app(tmp_path, prefs)
            try:
                async with app.run_test() as pilot:
                    await pilot.pause()
                    macro = create(app.macros, [key_step("OK")])
                    app.persist_preferences()  # must not raise
                    await pilot.pause()
                    assert get(app.macros, macro.id) is not None
            finally:
                path.chmod(0o644)

        asyncio.run(scenario())
