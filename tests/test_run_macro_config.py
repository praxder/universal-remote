import asyncio

from textual.widgets import Button, RadioSet

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.macros.models import Macro, key_step
from universal_remote.macros.registry import add
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.actions import (
    RUN_MACRO,
    ActionTypeListModal,
    RunMacroConfigModal,
)
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.custom_buttons import ButtonScope, resolve_action, set_action
from universal_remote.tui.macros_screen import MacroOptionList
from universal_remote.tui.remote_screen import ButtonConfigModal, RemoteScreen

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


async def _wait_for(app, pilot, screen_type, tries=50):
    for _ in range(tries):
        await pilot.pause()
        if isinstance(app.screen, screen_type):
            return
    raise AssertionError(
        f"{screen_type.__name__} never appeared; on {type(app.screen)}"
    )


async def _open_picker(app, pilot):
    """Reach the Run Macro configuration through the Button Config chain."""
    await pilot.click("#custom-1")
    await _wait_for(app, pilot, ButtonConfigModal)
    await pilot.click("#button-config-action-type")
    await _wait_for(app, pilot, ActionTypeListModal)
    await pilot.press("down")  # highlight Run Macro
    await pilot.press("enter")
    await _wait_for(app, pilot, RunMacroConfigModal)


def _rows(app) -> list[str]:
    options = app.screen.query_one(MacroOptionList)
    return [
        str(options.get_option_at_index(index).prompt)
        for index in range(options.option_count)
    ]


class TestRunMacroPicker:
    def test_given_saved_macros_when_the_picker_opens_then_it_lists_them_by_name(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, Macro(name="Login"))
                add(app.macros, Macro(name="Bedtime"))

                await _open_picker(app, pilot)

                assert _rows(app) == ["Login", "Bedtime"]

        asyncio.run(scenario())

    def test_given_a_chosen_macro_when_confirmed_then_the_action_holds_its_id(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Login", steps=[key_step("HOME")])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, macro)

                await _open_picker(app, pilot)
                await pilot.click("#run-macro-ok")
                await _wait_for(app, pilot, ButtonConfigModal)
                await pilot.click("#button-config-ok")
                await pilot.pause()

                stored = resolve_action(
                    app.custom_buttons, 1, device_id=device.id, platform="fake-tv"
                )
                assert stored == {"type": RUN_MACRO, "macro_id": macro.id}
                # The id, not a copy: the macro's steps are nowhere in the action.
                assert "steps" not in stored

        asyncio.run(scenario())

    def test_given_the_picker_when_cancelled_then_no_action_is_stored(self, tmp_path):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, Macro(name="Login"))

                await _open_picker(app, pilot)
                await pilot.click("#run-macro-cancel")
                await _wait_for(app, pilot, ButtonConfigModal)
                await pilot.click("#button-config-ok")
                await pilot.pause()

                assert (
                    resolve_action(
                        app.custom_buttons, 1, device_id=device.id, platform="fake-tv"
                    )
                    is None
                )

        asyncio.run(scenario())

    def test_given_no_saved_macros_when_the_picker_opens_then_it_says_so(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _open_picker(app, pilot)

                assert _rows(app) == ["No macros to choose — record one first"]

                # And confirming stores nothing, since there is nothing to choose.
                await pilot.click("#run-macro-ok")
                await _wait_for(app, pilot, ButtonConfigModal)
                await pilot.click("#button-config-ok")
                await pilot.pause()
                assert (
                    resolve_action(
                        app.custom_buttons, 1, device_id=device.id, platform="fake-tv"
                    )
                    is None
                )

        asyncio.run(scenario())

    def test_given_the_picker_when_open_then_it_offers_no_results_toggle(
        self, tmp_path
    ):
        # Playback presents its own progress modal and reports a failing step, so a
        # Results choice would have nothing to control.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, Macro(name="Login"))

                await _open_picker(app, pilot)

                assert list(app.screen.query(RadioSet)) == []
                labels = [str(b.label) for b in app.screen.query(Button)]
                assert labels == ["OK", "Cancel"]

        asyncio.run(scenario())

    def test_given_an_assigned_macro_when_the_picker_reopens_then_it_is_preselected(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        first, second = Macro(name="Login"), Macro(name="Bedtime")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, first)
                add(app.macros, second)
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": RUN_MACRO, "macro_id": second.id},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                await pilot.press("e")  # edit gesture, so the click opens config
                await pilot.pause()
                await _open_picker(app, pilot)

                assert app.screen.query_one(MacroOptionList).highlighted == 1

        asyncio.run(scenario())


class TestTheActionRefersToTheMacro:
    def test_given_an_assigned_macro_when_it_is_edited_then_the_button_plays_the_edit(
        self, tmp_path
    ):
        # The action holds an id, so renaming the macro and adding a step change what
        # the button does without touching the button.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Login", steps=[key_step("HOME")])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, macro)
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": RUN_MACRO, "macro_id": macro.id},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                # Rename it and give it a second step, as the detail modal's Save does.
                add(
                    app.macros,
                    Macro(
                        name="Renamed",
                        steps=[key_step("HOME"), key_step("OK")],
                        id=macro.id,
                        step_pause_ms=0,  # no gap to wait out in a test
                    ),
                )

                await pilot.click("#custom-1")
                for _ in range(80):
                    await pilot.pause()
                    if len(adapter.sessions[-1].sent_keys) == 2:
                        break

                assert adapter.sessions[-1].sent_keys == [Key.HOME, Key.OK]

        asyncio.run(scenario())
