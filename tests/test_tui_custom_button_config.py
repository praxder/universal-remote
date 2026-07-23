import asyncio

from textual.widgets import Button, Input, RadioSet

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.preferences.store import Preferences, PreferencesStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.custom_buttons import ButtonScope, set_title
from universal_remote.tui.remote_screen import ButtonConfigModal, RemoteScreen

# The full remote fits without scrolling here, so the bottom custom row is clickable.
_FIT_SIZE = (80, 45)


def _app(store, adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return UniversalRemoteApp(store=store, registry=registry)


def _store_with_device(tmp_path):
    store = DeviceStore(path=tmp_path / "d.json")
    store.add(Device(name="TV", platform="fake-tv", ip="1.1.1.1", credential="tok"))
    return store


async def _goto_remote(app, pilot):
    await pilot.press("r")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(app.screen, RemoteScreen)


async def _open_config(app, pilot, index):
    await pilot.click(f"#custom-{index}")
    await pilot.pause()
    assert isinstance(app.screen, ButtonConfigModal)


class TestButtonConfigModal:
    def test_given_a_custom_button_when_clicked_then_config_opens_with_defaults(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                # Scope defaults to This Device (the first option).
                assert (
                    app.screen.query_one("#button-config-scope", RadioSet).pressed_index
                    == 0
                )
                # The Action Type placeholder is present but cannot be activated.
                action_type = app.screen.query_one("#button-config-action-type", Button)
                assert action_type.disabled is True

        asyncio.run(scenario())

    def test_given_a_title_when_ok_on_this_device_then_the_button_shows_it(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                app.screen.query_one("#button-config-title-input", Input).value = "News"
                await pilot.click("#button-config-ok")
                await pilot.pause()
                # Back on the remote, the button shows the entered title.
                assert isinstance(app.screen, RemoteScreen)
                assert str(app.screen.query_one("#custom-1", Button).label) == "News"

        asyncio.run(scenario())

    def test_given_type_scope_when_ok_then_saved_for_the_device_type(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                app.screen.query_one("#button-config-title-input", Input).value = "Kids"
                await pilot.click("#scope-type")
                await pilot.pause()
                await pilot.click("#button-config-ok")
                await pilot.pause()
                assert str(app.screen.query_one("#custom-1", Button).label) == "Kids"
                # It was stored under the device-type scope, not the device scope.
                assert app.custom_buttons["type"]["fake-tv"]["1"]["title"] == "Kids"

        asyncio.run(scenario())

    def test_given_global_scope_when_ok_then_saved_globally(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                app.screen.query_one(
                    "#button-config-title-input", Input
                ).value = "Reboot"
                await pilot.click("#scope-global")
                await pilot.pause()
                await pilot.click("#button-config-ok")
                await pilot.pause()
                assert str(app.screen.query_one("#custom-1", Button).label) == "Reboot"
                assert app.custom_buttons["global"]["1"]["title"] == "Reboot"

        asyncio.run(scenario())

    def test_given_edits_when_cancel_then_the_saved_title_is_unchanged(self, tmp_path):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_title(
                    app.custom_buttons,
                    1,
                    "Netflix",
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                app.screen.query_one(
                    "#button-config-title-input", Input
                ).value = "Changed"
                await pilot.click("#button-config-cancel")
                await pilot.pause()
                # Cancel discards: both the shown label and the stored title stand.
                assert isinstance(app.screen, RemoteScreen)
                assert str(app.screen.query_one("#custom-1", Button).label) == "Netflix"
                assert (
                    app.custom_buttons["device"][device.id]["1"]["title"] == "Netflix"
                )

        asyncio.run(scenario())

    def test_given_a_configured_button_when_config_opens_then_the_input_prefills_its_title(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_title(
                    app.custom_buttons,
                    1,
                    "Netflix",
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                title_input = app.screen.query_one("#button-config-title-input", Input)
                assert title_input.value == "Netflix"

        asyncio.run(scenario())


class TestButtonConfigPersistence:
    def test_given_ok_when_saved_then_the_title_persists_to_the_store(self, tmp_path):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_config(app, pilot, 1)
                app.screen.query_one("#button-config-title-input", Input).value = "News"
                await pilot.click("#button-config-ok")
                await pilot.pause()
                # Persisted to the same settings file the store loads from.
                reloaded = app.preferences.load().custom_buttons
                assert reloaded["device"][device.id]["1"]["title"] == "News"

        asyncio.run(scenario())

    def test_given_a_saved_title_when_the_app_starts_then_the_remote_shows_it(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        # Pre-seed the isolated settings file with a device-scoped title.
        saved: dict = {}
        set_title(
            saved,
            3,
            "Plex",
            ButtonScope.DEVICE,
            device_id=device.id,
            platform="fake-tv",
        )
        PreferencesStore().save(Preferences(custom_buttons=saved))

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                assert str(app.screen.query_one("#custom-3", Button).label) == "Plex"

        asyncio.run(scenario())
