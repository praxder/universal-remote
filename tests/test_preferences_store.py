from pathlib import Path

from universal_remote.preferences.store import (
    Preferences,
    PreferencesStore,
    default_settings_path,
)


class TestDefaultSettingsPath:
    def test_given_xdg_config_home_is_set_when_resolving_then_it_lives_under_it(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        assert (
            default_settings_path() == tmp_path / "universal-remote" / "settings.json"
        )

    def test_given_xdg_config_home_is_unset_when_resolving_then_it_falls_back_to_home_config(
        self, monkeypatch
    ):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        expected = Path.home() / ".config" / "universal-remote" / "settings.json"
        assert default_settings_path() == expected


class TestPreferencesStorePersistence:
    def test_given_no_file_when_loaded_then_defaults_are_returned(self, tmp_path):
        store = PreferencesStore(path=tmp_path / "missing.json")

        assert store.load() == Preferences()

    def test_given_a_corrupt_file_when_loaded_then_defaults_are_returned(
        self, tmp_path
    ):
        path = tmp_path / "settings.json"
        path.write_text("{not valid json")

        assert PreferencesStore(path=path).load() == Preferences()

    def test_given_a_saved_theme_when_reloaded_then_it_round_trips(self, tmp_path):
        path = tmp_path / "settings.json"
        PreferencesStore(path=path).save(Preferences(theme="gruvbox"))

        assert PreferencesStore(path=path).load() == Preferences(theme="gruvbox")

    def test_given_theme_and_shortcuts_when_reloaded_then_both_round_trip(
        self, tmp_path
    ):
        path = tmp_path / "settings.json"
        preferences = Preferences(theme="gruvbox", shortcuts={"remote.vol_up": "="})

        PreferencesStore(path=path).save(preferences)

        assert PreferencesStore(path=path).load() == preferences

    def test_given_an_old_file_with_only_a_theme_when_loaded_then_shortcuts_are_empty(
        self, tmp_path
    ):
        path = tmp_path / "settings.json"
        path.write_text('{"theme": "nord"}')

        loaded = PreferencesStore(path=path).load()

        assert loaded.theme == "nord"
        assert loaded.shortcuts == {}
