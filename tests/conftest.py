import pytest


@pytest.fixture(autouse=True)
def _isolate_config_dir(tmp_path_factory, monkeypatch):
    """Point the default XDG config dir at a throwaway tmp dir for every test.

    Both `DeviceStore` and `PreferencesStore` resolve their default file under
    `$XDG_CONFIG_HOME`; without this, a test that builds the app with default
    stores would read and write the developer's real `~/.config` files — and the
    theme-persistence wiring makes the app write `settings.json` on startup when a
    theme is saved. Tests that pass explicit store paths are unaffected, and a test
    that sets `XDG_CONFIG_HOME` itself overrides this (monkeypatch stacks per-test).
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("xdg-config")))
