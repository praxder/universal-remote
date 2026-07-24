import asyncio

from textual.widgets import Button, RadioSet, TextArea

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.actions import (
    ActionTypeListModal,
    RunScriptConfigModal,
    ScriptResultModal,
)
from universal_remote.preferences.store import Preferences, PreferencesStore
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.custom_buttons import ButtonScope, set_action
from universal_remote.tui.remote_screen import ButtonConfigModal, RemoteScreen

_FIT_SIZE = (90, 45)

_SHOW_OK_ACTION = {
    "type": "run_script",
    "source": "inline",
    "script": "exit 0",
    "show_results": True,
}


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


async def _wait_for(app, pilot, screen_type, tries=50):
    for _ in range(tries):
        await pilot.pause()
        if isinstance(app.screen, screen_type):
            return
    raise AssertionError(
        f"{screen_type.__name__} never appeared; on {type(app.screen)}"
    )


class TestRunOnClick:
    def test_given_a_button_with_an_action_when_clicked_then_it_runs_not_configures(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    _SHOW_OK_ACTION,
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await pilot.click("#custom-1")
                # The action runs in a worker and, with Show, surfaces a result modal —
                # the config modal must NOT open.
                await _wait_for(app, pilot, ScriptResultModal)

        asyncio.run(scenario())

    def test_given_a_button_with_no_action_when_clicked_then_config_opens(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#custom-1")
                await pilot.pause()
                assert isinstance(app.screen, ButtonConfigModal)

        asyncio.run(scenario())


class TestEditGesture:
    def test_given_edit_mode_armed_when_a_button_with_an_action_is_clicked_then_config_opens(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    _SHOW_OK_ACTION,
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await pilot.press("e")  # arm edit-mode
                await pilot.pause()
                await pilot.click("#custom-1")
                await pilot.pause()
                # The armed gesture opens config instead of running the action.
                assert isinstance(app.screen, ButtonConfigModal)
                # And edit-mode has cleared: after cancelling, a plain click runs again.
                await pilot.click("#button-config-cancel")
                await pilot.pause()
                assert app.screen._edit_mode is False

        asyncio.run(scenario())

    def test_given_edit_mode_armed_then_the_custom_buttons_show_an_indicator(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                button = app.screen.query_one("#custom-1", Button)
                assert button.has_class("edit-armed") is False
                await pilot.press("e")  # arm edit-mode
                await pilot.pause()
                # Every custom button carries the armed cue while edit-mode is on.
                assert button.has_class("edit-armed") is True
                # Activating a button disarms it, so the cue clears on return.
                await pilot.click("#custom-1")
                await pilot.pause()
                await pilot.click("#button-config-cancel")
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)
                assert (
                    app.screen.query_one("#custom-1", Button).has_class("edit-armed")
                    is False
                )

        asyncio.run(scenario())

    def test_given_edit_mode_armed_when_the_edit_key_is_pressed_again_then_it_disarms(
        self, tmp_path
    ):
        # The edit-mode key toggles: `e` arms it, `e` again disarms it without opening
        # any configuration, and the armed indicator clears with it.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                button = app.screen.query_one("#custom-1", Button)

                await pilot.press("e")  # arm
                await pilot.pause()
                assert app.screen._edit_mode is True
                assert button.has_class("edit-armed") is True

                await pilot.press("e")  # press again disarms
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._edit_mode is False
                assert button.has_class("edit-armed") is False

        asyncio.run(scenario())

    def test_given_a_stale_reserved_override_on_e_when_pressed_then_edit_mode_arms(
        self, tmp_path
    ):
        # A pre-reservation override bound Stop to `e`. It is pruned on load, so `e`
        # arms edit-mode as intended rather than sending Stop.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        PreferencesStore().save(Preferences(shortcuts={"remote.stop": "e"}))

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    _SHOW_OK_ACTION,
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await pilot.press("e")  # must arm edit-mode, not send Stop
                await pilot.pause()
                await pilot.click("#custom-1")
                await pilot.pause()
                assert isinstance(app.screen, ButtonConfigModal)

        asyncio.run(scenario())

    def test_given_edit_mode_armed_when_the_shortcut_fires_then_config_opens(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    2,
                    _SHOW_OK_ACTION,
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                app.shortcut_overrides["remote.custom_2"] = "f2"
                app.apply_shortcuts()
                await _goto_remote(app, pilot)
                await pilot.press("e")  # arm edit-mode
                await pilot.pause()
                await pilot.press("f2")  # activate via shortcut
                await pilot.pause()
                assert isinstance(app.screen, ButtonConfigModal)

        asyncio.run(scenario())


class TestActionTypeControl:
    def test_given_the_action_type_control_when_selected_then_the_list_opens(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#custom-1")
                await pilot.pause()
                action_type = app.screen.query_one("#button-config-action-type", Button)
                assert action_type.disabled is False
                await pilot.click("#button-config-action-type")
                await pilot.pause()
                assert isinstance(app.screen, ActionTypeListModal)

        asyncio.run(scenario())

    def test_given_an_action_configured_when_ok_then_it_persists_at_the_scope(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#custom-1")
                await pilot.pause()
                # Action Type → list → Run Custom Script → config modal.
                await pilot.click("#button-config-action-type")
                await _wait_for(app, pilot, ActionTypeListModal)
                await pilot.press("enter")
                await _wait_for(app, pilot, RunScriptConfigModal)
                await pilot.click("#source-inline")
                await pilot.pause()
                app.screen.query_one("#run-script-inline", TextArea).text = "echo hi"
                await pilot.click("#run-script-ok")
                await _wait_for(app, pilot, ButtonConfigModal)
                # Back in Button Config; OK persists title + action together.
                await pilot.click("#button-config-ok")
                await pilot.pause()
                entry = app.preferences.load().custom_buttons["device"][device.id]["1"]
                assert entry["action"]["source"] == "inline"
                assert entry["action"]["script"] == "echo hi"

        asyncio.run(scenario())

    def test_given_a_configured_action_when_reopened_then_the_config_prefills(
        self, tmp_path
    ):
        # Re-editing a button that already has an action must reopen its Run Script
        # config with the stored source, script, and results choice filled in — not
        # blank. _SHOW_OK_ACTION is an inline "exit 0" with results shown.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    _SHOW_OK_ACTION,
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await pilot.press("e")  # edit gesture, so the click opens config
                await pilot.pause()
                await pilot.click("#custom-1")
                await _wait_for(app, pilot, ButtonConfigModal)
                await pilot.click("#button-config-action-type")
                await _wait_for(app, pilot, ActionTypeListModal)
                await pilot.press("enter")  # choose Run Custom Script
                await _wait_for(app, pilot, RunScriptConfigModal)

                screen = app.screen
                assert screen.query_one("#run-script-inline", TextArea).text == "exit 0"
                # Inline source (index 1) and Show results (index 1) are preselected.
                assert (
                    screen.query_one("#run-script-source", RadioSet).pressed_index == 1
                )
                assert (
                    screen.query_one("#run-script-results", RadioSet).pressed_index == 1
                )

        asyncio.run(scenario())
