import asyncio

from textual.widgets import Button, Checkbox

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.macros.models import Macro, key_step
from universal_remote.macros.registry import add, list_macros
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.macros_screen import (
    MacroOptionList,
    MacrosListModal,
    RecordingHintModal,
)
from universal_remote.tui.remote_screen import RemoteScreen

_FIT_SIZE = (80, 45)
# The shortest terminal the app supports; every control must stay on screen here.
_SHORT_SIZE = (80, 24)


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


async def _open_list(app, pilot):
    await pilot.click("#macros")
    await pilot.pause()
    assert isinstance(app.screen, MacrosListModal)


async def _create_macro(app, pilot):
    """Activate Create Macro and acknowledge the one-time recording hint."""
    await pilot.click("#macros-create")
    await pilot.pause()
    await pilot.click("#recording-hint-ok")
    await pilot.pause()


def _remote(app) -> RemoteScreen:
    """The live remote, whichever modal is on top of it."""
    return next(
        screen for screen in app.screen_stack if isinstance(screen, RemoteScreen)
    )


def _rows(app) -> list[str]:
    options = app.screen.query_one(MacroOptionList)
    return [
        str(options.get_option_at_index(index).prompt)
        for index in range(options.option_count)
    ]


def _messages(app) -> list[str]:
    return [str(note.message) for note in app._notifications]


def _seed(app, *names) -> None:
    for name in names:
        add(app.macros, Macro(name=name, steps=[key_step("HOME")]))


class TestMacrosList:
    def test_given_saved_macros_when_opened_then_they_are_listed_in_saved_order(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login", "Bedtime")

                await _open_list(app, pilot)

                assert _rows(app) == ["Login", "Bedtime"]

        asyncio.run(scenario())

    def test_given_no_saved_macros_when_opened_then_a_placeholder_row_is_shown(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _open_list(app, pilot)

                assert _rows(app) == ["No macros yet"]

        asyncio.run(scenario())

    def test_given_the_placeholder_row_when_enter_is_pressed_then_nothing_opens(
        self, tmp_path
    ):
        # The placeholder is not a macro: Enter on it must not open a detail modal.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)

                await pilot.press("enter")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert list_macros(app.macros) == []

        asyncio.run(scenario())

    def test_given_the_list_when_navigated_by_arrows_then_the_highlight_moves(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login", "Bedtime")
                await _open_list(app, pilot)
                options = app.screen.query_one(MacroOptionList)

                await pilot.press("down")
                await pilot.pause()
                assert options.highlighted == 1

                await pilot.press("up")
                await pilot.pause()
                assert options.highlighted == 0

        asyncio.run(scenario())

    def test_given_the_list_when_navigated_by_vim_keys_then_the_highlight_moves(
        self, tmp_path
    ):
        # `j`/`k`, matching the reserved D-pad aliases used everywhere else.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login", "Bedtime")
                await _open_list(app, pilot)
                options = app.screen.query_one(MacroOptionList)

                await pilot.press("j")
                await pilot.pause()
                assert options.highlighted == 1

                await pilot.press("k")
                await pilot.pause()
                assert options.highlighted == 0

        asyncio.run(scenario())

    def test_given_the_list_when_closed_then_nothing_changed(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login")
                await _open_list(app, pilot)

                await pilot.click("#macros-close")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._recording is None
                assert [m.name for m in list_macros(app.macros)] == ["Login"]

        asyncio.run(scenario())


class TestCreateMacro:
    def test_given_create_macro_when_activated_then_the_modal_is_dismissed(
        self, tmp_path
    ):
        # Dismissed, not merely covered: a modal left on the screen stack truncates
        # the remote's binding chain, so the remote would ignore every key.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)

                await _create_macro(app, pilot)

                assert isinstance(app.screen, RemoteScreen)
                assert not any(
                    isinstance(screen, MacrosListModal) for screen in app.screen_stack
                )
                assert app.screen._recording is not None

        asyncio.run(scenario())

    def test_given_a_recording_started_from_the_list_when_a_key_is_pressed_then_it_records(
        self, tmp_path
    ):
        # The regression the dismissal exists for: a live remote that still answers.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await _create_macro(app, pilot)

                await pilot.press("space")  # the Home shortcut
                await pilot.pause()

                assert app.screen._recording.steps == [key_step("HOME")]

        asyncio.run(scenario())


class TestRecordingHint:
    def test_given_create_macro_when_activated_then_the_hint_explains_the_recording(
        self, tmp_path
    ):
        # Create Macro hands back a remote that looks unchanged, so the hint is what
        # says a recording is about to start. Nothing records until it is confirmed.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)

                await pilot.click("#macros-create")
                await pilot.pause()

                assert isinstance(app.screen, RecordingHintModal)
                assert _remote(app)._recording is None
                # Nothing here is destructive, so OK carries the focus.
                assert app.screen.focused is app.screen.query_one(
                    "#recording-hint-ok", Button
                )
                assert not app.screen.query_one(
                    "#recording-hint-suppress", Checkbox
                ).value

        asyncio.run(scenario())

    def test_given_the_hint_when_ok_is_activated_then_the_recording_starts(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()

                await pilot.click("#recording-hint-ok")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._recording is not None

        asyncio.run(scenario())

    def test_given_the_hint_when_cancelled_then_nothing_records_and_the_list_reopens(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login")
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()

                await pilot.click("#recording-hint-cancel")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _rows(app) == ["Login"]
                assert _remote(app)._recording is None

        asyncio.run(scenario())

    def test_given_the_hint_when_escape_is_pressed_then_it_cancels(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()

                await pilot.press("escape")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _remote(app)._recording is None

        asyncio.run(scenario())


class TestSuppressingTheRecordingHint:
    def test_given_the_box_checked_when_ok_is_activated_then_the_hint_does_not_return(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()
                app.screen.query_one("#recording-hint-suppress", Checkbox).value = True
                await pilot.click("#recording-hint-ok")
                await pilot.pause()
                # Out of the first recording and back to the list.
                await pilot.press("escape")
                await pilot.pause()

                await pilot.click("#macros-create")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._recording is not None
                # And on disk, so the next run skips it too.
                assert app.preferences.load().hide_recording_hint is True

        asyncio.run(scenario())

    def test_given_the_box_checked_when_cancelled_then_the_hint_returns(self, tmp_path):
        # Cancel means nothing happened, the checkbox included.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()
                app.screen.query_one("#recording-hint-suppress", Checkbox).value = True
                await pilot.click("#recording-hint-cancel")
                await pilot.pause()

                await pilot.click("#macros-create")
                await pilot.pause()

                assert isinstance(app.screen, RecordingHintModal)
                assert app.hide_recording_hint is False

        asyncio.run(scenario())

    def test_given_ok_without_the_box_when_creating_again_then_the_hint_returns(
        self, tmp_path
    ):
        # Acknowledging it never suppresses it: only the checkbox does.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await _create_macro(app, pilot)
                await pilot.press("escape")  # cancel the recording
                await pilot.pause()

                await pilot.click("#macros-create")
                await pilot.pause()

                assert isinstance(app.screen, RecordingHintModal)

        asyncio.run(scenario())

    def test_given_a_saved_suppression_when_creating_then_recording_starts_at_once(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                app.hide_recording_hint = True
                await _open_list(app, pilot)

                await pilot.click("#macros-create")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._recording is not None

        asyncio.run(scenario())


class TestRecordingHintFits:
    def test_given_a_short_terminal_when_the_hint_opens_then_every_control_fits(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_SHORT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await pilot.click("#macros-create")
                await pilot.pause()

                width, height = _SHORT_SIZE
                checkbox = app.screen.query_one("#recording-hint-suppress", Checkbox)
                for widget in (*app.screen.query(Button), checkbox):
                    region = widget.region
                    assert region.width > 0 and region.height > 0
                    assert region.right <= width
                    assert region.bottom <= height

        asyncio.run(scenario())


class TestRecordingReturnPaths:
    def test_given_captured_steps_when_stopped_then_a_macro_is_saved_and_selected(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await _create_macro(app, pilot)
                await pilot.press("space")
                await pilot.pause()

                await pilot.click("#macros")  # Stop
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _rows(app) == ["Macro 1"]
                assert app.screen.query_one(MacroOptionList).highlighted == 0
                saved = list_macros(app.macros)
                assert saved[0].steps == [key_step("HOME")]
                # And it is on disk, not only in memory.
                assert app.preferences.load().macros["items"]

        asyncio.run(scenario())

    def test_given_a_recording_when_cancelled_then_the_list_reopens_unchanged(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                _seed(app, "Login")
                await _open_list(app, pilot)
                await _create_macro(app, pilot)
                await pilot.press("space")
                await pilot.pause()

                await pilot.press("escape")  # Go Back cancels the recording
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _rows(app) == ["Login"]

        asyncio.run(scenario())

    def test_given_no_interaction_when_stopped_then_no_macro_is_created(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_list(app, pilot)
                await _create_macro(app, pilot)

                await pilot.click("#macros")  # Stop, having captured nothing
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert list_macros(app.macros) == []
                assert any("nothing was recorded" in m.lower() for m in _messages(app))

        asyncio.run(scenario())

    def test_given_two_recordings_when_saved_then_they_are_numbered_in_sequence(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                for _ in range(2):
                    await _open_list(app, pilot)
                    await _create_macro(app, pilot)
                    await pilot.press("space")
                    await pilot.pause()
                    await pilot.click("#macros")  # Stop
                    await pilot.pause()
                    await pilot.click("#macros-close")
                    await pilot.pause()

                assert [m.name for m in list_macros(app.macros)] == [
                    "Macro 1",
                    "Macro 2",
                ]

        asyncio.run(scenario())
