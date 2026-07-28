import asyncio

from textual.widgets import Button, Footer, Input, Label

from tests.fakes import FakeAdapter
from universal_remote.capabilities import Capabilities
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.macros.models import action_step, key_step, text_step
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.custom_buttons import ButtonScope, set_action
from universal_remote.tui.macros_screen import MacrosListModal
from universal_remote.tui.remote_screen import RecordMode, RemoteScreen

# The supported baseline the full button set fits without scrolling; the recording
# state must not cost a row, so it is asserted at exactly this size.
_FIT_SIZE = (80, 45)

_SCRIPT_ACTION = {
    "type": "run_script",
    "source": "inline",
    "script": "exit 0",
    "show_results": False,
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


async def _record(pilot, screen, mode=RecordMode.APPEND_UNTIL_STOP) -> list:
    """Start a recording on `screen`; the returned list receives its outcome.

    Awaits a refresh before returning: the recording state relabels the Macros button
    and shows the indicator, so the top row re-lays out and a click issued before that
    settles would land on the wrong button.
    """
    outcomes: list = []
    screen._start_recording(mode, outcomes.append)
    await pilot.pause()
    return outcomes


def _indicator(screen) -> str:
    return str(screen.query_one("#recording-indicator", Label).content)


def _messages(app) -> list[str]:
    return [str(note.message) for note in app._notifications]


class TestMacrosControl:
    def test_given_the_remote_when_shown_then_the_top_row_ends_with_a_macros_button(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                ids = [button.id for button in app.screen.query("#row-top Button")]
                assert ids == ["key-menu", "key-home", "key-back", "macros"]

        asyncio.run(scenario())

    def test_given_no_recording_when_shown_then_the_indicator_is_hidden(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                assert app.screen.query_one("#recording-indicator").display is False
                assert str(app.screen.query_one("#macros", Button).label) == "Macros"

        asyncio.run(scenario())

    def test_given_a_shortcut_assigned_to_macros_then_it_opens_the_list_and_no_hint(
        self, tmp_path
    ):
        # The Macros action mirrors a click, and stays out of the footer: the
        # 80-column footer has no room for a further hint.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                app.shortcut_overrides["remote.macros"] = "f5"
                app.apply_shortcuts()
                await pilot.pause()

                footer = app.screen.query_one(Footer)
                keys = list(footer.query("FooterKey"))
                assert sum(key.size.width for key in keys) <= footer.size.width
                assert "Macros" not in {key.description for key in keys}

                await pilot.press("f5")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)

        asyncio.run(scenario())


class TestRecordingState:
    def test_given_a_recording_at_the_baseline_size_then_the_remote_does_not_scroll(
        self, tmp_path
    ):
        # Recording must cost zero rows: the indicator lives in the existing top row
        # and the Stop control is the Macros button relabelled.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _record(pilot, app.screen)
                await pilot.pause()

                assert app.screen.max_scroll_y == 0

        asyncio.run(scenario())

    def test_given_an_append_recording_then_the_macros_button_becomes_stop(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _record(pilot, app.screen, RecordMode.APPEND_UNTIL_STOP)
                await pilot.pause()

                assert str(app.screen.query_one("#macros", Button).label) == "■ Stop"
                assert app.screen.query_one("#recording-indicator").display is True

        asyncio.run(scenario())

    def test_given_a_capture_one_recording_then_the_macros_button_becomes_cancel(
        self, tmp_path
    ):
        # There is nothing to stop when capturing a single step, so the control reads
        # Cancel — pressing it returns without capturing, exactly as Go Back does.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _record(pilot, app.screen, RecordMode.CAPTURE_ONE)
                await pilot.pause()

                assert str(app.screen.query_one("#macros", Button).label) == "■ Cancel"

        asyncio.run(scenario())

    def test_given_a_recording_when_stopped_then_the_button_reads_macros_again(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)
                await pilot.pause()

                await pilot.click("#macros")  # the Stop control
                await pilot.pause()

                assert str(app.screen.query_one("#macros", Button).label) == "Macros"
                assert app.screen.query_one("#recording-indicator").display is False

        asyncio.run(scenario())


class TestCancelHint:
    def test_given_a_recording_when_started_then_the_indicator_names_the_cancel_key(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _record(pilot, app.screen)
                await pilot.pause()

                assert "ESC" in _indicator(app.screen)

        asyncio.run(scenario())

    def test_given_go_back_rebound_when_recording_then_the_hint_names_the_new_key(
        self, tmp_path
    ):
        # The hint is rendered from the Go Back action's current key, not a fixed one,
        # so it stays accurate after the user rebinds it.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                app.shortcut_overrides["global.go_back"] = "f4"
                app.apply_shortcuts()

                await _record(pilot, app.screen)
                await pilot.pause()

                hint = _indicator(app.screen)
                assert "F4" in hint
                assert "ESC" not in hint

        asyncio.run(scenario())


class TestKeyCapture:
    def test_given_a_clicked_key_when_recording_then_it_is_captured(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.click("#key-home")
                await pilot.pause()

                assert app.screen._recording.steps == [key_step("HOME")]

        asyncio.run(scenario())

    def test_given_several_keys_when_recording_then_they_are_captured_in_order(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.click("#key-home")
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()

                assert app.screen._recording.steps == [
                    key_step("HOME"),
                    key_step("DOWN"),
                    key_step("OK"),
                ]

        asyncio.run(scenario())

    def test_given_a_key_sent_by_shortcut_when_recording_then_it_is_captured(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.press("space")  # the Home shortcut
                await pilot.pause()

                assert app.screen._recording.steps == [key_step("HOME")]

        asyncio.run(scenario())

    def test_given_an_unsupported_key_when_recording_then_nothing_is_captured(
        self, tmp_path
    ):
        # Arrange: an adapter without number keys, so a digit hotkey sends nothing.
        store = _store_with_device(tmp_path)
        keys = frozenset(key for key in Key if not key.name.startswith("NUM_"))
        adapter = FakeAdapter(
            platform="fake-tv", capabilities=Capabilities(keys=keys, text=True)
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.press("1")
                await pilot.pause()

                assert app.screen._recording.steps == []

        asyncio.run(scenario())

    def test_given_a_failed_send_when_recording_then_nothing_is_captured(
        self, tmp_path
    ):
        # A key the device never received must not become a step.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[-1].dispatch_error = RuntimeError("unreachable")
                await _record(pilot, app.screen)

                await pilot.click("#key-home")
                await pilot.pause()

                assert app.screen._recording.steps == []

        asyncio.run(scenario())


class TestTextCapture:
    def test_given_text_sent_when_recording_then_it_is_captured(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.press("t")
                await pilot.pause()
                app.screen.query_one("#text-entry-input", Input).value = "hello"
                await pilot.press("enter")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert app.screen._recording.steps == [text_step("hello")]

        asyncio.run(scenario())

    def test_given_a_failed_text_send_when_recording_then_nothing_is_captured(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[-1].text_dispatch_error = RuntimeError("unreachable")
                await _record(pilot, app.screen)

                await pilot.press("t")
                await pilot.pause()
                app.screen.query_one("#text-entry-input", Input).value = "hello"
                await pilot.press("enter")
                await pilot.pause()

                assert app.screen._recording.steps == []

        asyncio.run(scenario())

    def test_given_the_text_modal_cancelled_when_recording_then_nothing_is_captured(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.press("t")
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()

                assert app.screen._recording.steps == []

        asyncio.run(scenario())


class TestCustomButtonCapture:
    def test_given_a_dispatched_custom_action_when_recording_then_a_copy_is_captured(
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
                    dict(_SCRIPT_ACTION),
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.click("#custom-1")
                await pilot.pause()

                assert app.screen._recording.steps == [action_step(_SCRIPT_ACTION)]

        asyncio.run(scenario())

    def test_given_a_captured_action_when_its_button_is_reconfigured_then_the_step_stands(
        self, tmp_path
    ):
        # The step holds a frozen copy, so retuning the button never reaches into it.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    dict(_SCRIPT_ACTION),
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)
                await pilot.click("#custom-1")
                await pilot.pause()

                set_action(
                    app.custom_buttons,
                    1,
                    {**_SCRIPT_ACTION, "script": "echo changed"},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                assert app.screen._recording.steps[0]["action"]["script"] == "exit 0"

        asyncio.run(scenario())

    def test_given_an_unconfigured_button_when_activated_while_recording_then_nothing_is_captured(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)
                recording = app.screen._recording

                await pilot.click("#custom-1")  # opens its configuration instead
                await pilot.pause()

                assert recording.steps == []

        asyncio.run(scenario())

    def test_given_edit_mode_armed_when_a_button_is_activated_then_nothing_is_captured(
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
                    dict(_SCRIPT_ACTION),
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)
                recording = app.screen._recording
                await pilot.press("e")  # arm edit-mode
                await pilot.pause()

                await pilot.click("#custom-1")  # opens configuration, runs nothing
                await pilot.pause()

                assert recording.steps == []

        asyncio.run(scenario())


class TestNestedMacrosRefused:
    def test_given_a_run_macro_button_when_activated_while_recording_then_it_is_refused(
        self, tmp_path
    ):
        # It still runs, but nothing is captured and the refusal is reported: a
        # captured Run Macro step could recurse forever.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": "run_macro", "macro_id": "abc"},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )
                await _goto_remote(app, pilot)
                await _record(pilot, app.screen)

                await pilot.click("#custom-1")
                await pilot.pause()

                assert app.screen._recording.steps == []
                assert any("nested" in message.lower() for message in _messages(app))

        asyncio.run(scenario())


class TestGoBackWhileRecording:
    def test_given_a_recording_when_go_back_is_pressed_then_it_cancels_the_recording(
        self, tmp_path
    ):
        # Go Back must cancel the recording, not leave the remote or close the session.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                outcomes = await _record(pilot, app.screen)
                await pilot.click("#key-home")
                await pilot.pause()

                await pilot.press("escape")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert adapter.sessions[-1].closed is False
                assert app.screen._recording is None
                assert outcomes == [None]  # cancelled: nothing handed back

        asyncio.run(scenario())

    def test_given_no_recording_when_go_back_is_pressed_then_the_remote_closes(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await pilot.press("escape")
                await pilot.pause()

                assert not isinstance(app.screen, RemoteScreen)
                assert adapter.sessions[-1].closed is True

        asyncio.run(scenario())

    def test_given_a_capture_one_recording_when_cancel_is_activated_then_it_returns_empty(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                outcomes = await _record(pilot, app.screen, RecordMode.CAPTURE_ONE)

                await pilot.click("#macros")  # the Cancel control
                await pilot.pause()

                assert outcomes == [None]

        asyncio.run(scenario())

    def test_given_a_capture_one_recording_when_one_key_is_sent_then_it_ends_itself(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                outcomes = await _record(pilot, app.screen, RecordMode.CAPTURE_ONE)

                await pilot.click("#key-home")
                await pilot.pause()

                assert outcomes == [[key_step("HOME")]]
                assert app.screen._recording is None

        asyncio.run(scenario())

    def test_given_an_append_recording_when_stopped_then_its_steps_are_handed_back(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                outcomes = await _record(pilot, app.screen)
                await pilot.click("#key-home")
                await pilot.pause()

                await pilot.click("#macros")  # Stop
                await pilot.pause()

                assert outcomes == [[key_step("HOME")]]

        asyncio.run(scenario())
