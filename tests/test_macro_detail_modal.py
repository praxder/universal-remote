import asyncio

from textual.widgets import Button, Input, Label

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.macros.models import Macro, key_step, pause_step, text_step
from universal_remote.macros.registry import add, get, list_macros
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.actions import MacroPlaybackModal
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import ConfirmDeleteScreen
from universal_remote.tui.macros_screen import (
    MacroDetailModal,
    MacroOptionList,
    MacrosListModal,
    PauseDurationModal,
    RecordingHintModal,
)
from universal_remote.tui.remote_screen import RemoteScreen

_FIT_SIZE = (80, 45)
# The shortest terminal the app supports; a modal must scroll its list rather than
# clip its buttons here.
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


async def _open_detail(app, pilot, macro):
    """Seed `macro`, then reach its detail modal the way the user does."""
    add(app.macros, macro)
    await pilot.click("#macros")
    await pilot.pause()
    await pilot.press("enter")  # open the highlighted macro
    await pilot.pause()
    assert isinstance(app.screen, MacroDetailModal)


def _step_rows(app) -> list[str]:
    steps = app.screen.query_one("#macro-detail-steps", MacroOptionList)
    return [
        str(steps.get_option_at_index(index).prompt)
        for index in range(steps.option_count)
    ]


def _list_rows(app) -> list[str]:
    options = app.screen.query_one(MacroOptionList)
    return [
        str(options.get_option_at_index(index).prompt)
        for index in range(options.option_count)
    ]


def _macro(name="Login") -> Macro:
    return Macro(name=name, steps=[key_step("HOME"), key_step("DOWN"), key_step("OK")])


class TestDetailModalRendersTheDraft:
    def test_given_a_macro_when_opened_then_its_name_and_steps_are_shown(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _open_detail(app, pilot, _macro())

                assert (
                    app.screen.query_one("#macro-detail-name", Input).value == "Login"
                )
                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_mixed_step_types_when_opened_then_each_is_described(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Mixed", steps=[text_step("hi"), pause_step(500)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _open_detail(app, pilot, macro)

                assert _step_rows(app) == ['1. Text: "hi"', "2. Pause: 500ms"]

        asyncio.run(scenario())

    def test_given_edits_when_saved_then_the_name_and_order_are_persisted(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.press("down")  # select step 2
                await pilot.click("#step-up")  # swap it with step 1
                await pilot.pause()
                await pilot.click("#macro-save")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _list_rows(app) == ["Renamed"]
                saved = get(app.macros, macro.id)
                assert saved.name == "Renamed"
                assert [step["key"] for step in saved.steps] == ["DOWN", "HOME", "OK"]
                assert app.preferences.load().macros["items"][macro.id]["name"] == (
                    "Renamed"
                )

        asyncio.run(scenario())

    def test_given_edits_when_closed_then_every_one_is_discarded(self, tmp_path):
        # The modal renders from a draft and never writes, so Close simply drops it.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.press("down")
                await pilot.click("#step-up")
                await pilot.click("#step-remove")
                await pilot.pause()
                await pilot.click("#macro-close")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _list_rows(app) == ["Login"]
                saved = get(app.macros, macro.id)
                assert saved.name == "Login"
                assert [step["key"] for step in saved.steps] == ["HOME", "DOWN", "OK"]

        asyncio.run(scenario())

    def test_given_delete_when_activated_then_it_asks_before_removing_anything(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.click("#macro-delete")
                await pilot.pause()

                assert isinstance(app.screen, ConfirmDeleteScreen)
                message = app.screen.query_one("#confirm-message", Label)
                assert "Login" in str(message.content)
                # Cancel is focused by default, so a stray Enter cannot delete.
                assert app.screen.focused is app.screen.query_one("#cancel", Button)
                assert get(app.macros, macro.id) is not None

        asyncio.run(scenario())

    def test_given_the_prompt_when_confirmed_then_the_macro_is_gone_from_the_list(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())
                await pilot.click("#macro-delete")
                await pilot.pause()

                await pilot.click("#confirm")
                await pilot.pause()

                assert isinstance(app.screen, MacrosListModal)
                assert _list_rows(app) == ["No macros yet"]
                assert list_macros(app.macros) == []
                assert app.preferences.load().macros["items"] == {}

        asyncio.run(scenario())

    def test_given_the_prompt_when_cancelled_then_the_draft_survives_untouched(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)
                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.press("down")
                await pilot.click("#step-up")
                await pilot.click("#macro-delete")
                await pilot.pause()

                await pilot.click("#cancel")
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert (
                    app.screen.query_one("#macro-detail-name", Input).value == "Renamed"
                )
                assert _step_rows(app) == ["1. Key: DOWN", "2. Key: HOME", "3. Key: OK"]
                assert get(app.macros, macro.id).name == "Login"

        asyncio.run(scenario())

    def test_given_an_unsaved_rename_when_delete_then_the_prompt_names_the_new_name(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())
                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"

                await pilot.click("#macro-delete")
                await pilot.pause()

                message = app.screen.query_one("#confirm-message", Label)
                assert "Renamed" in str(message.content)

        asyncio.run(scenario())


class TestDetailModalLayout:
    def test_given_a_tall_terminal_when_open_then_a_blank_row_separates_the_items(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                # The steps label is the one exception: it belongs to the list under it.
                for above, below in (
                    ("#macro-detail-title", "#macro-detail-name"),
                    ("#macro-detail-name", "#macro-detail-steps-label"),
                    ("#macro-detail-steps", "#macro-detail-step-buttons"),
                    ("#macro-detail-step-buttons", "#macro-detail-pause-row"),
                    ("#macro-detail-pause-row", "#macro-detail-buttons"),
                ):
                    gap = app.screen.query_one(below).region.y - (
                        app.screen.query_one(above).region.bottom
                    )
                    assert gap == 1, f"{above} -> {below}"

        asyncio.run(scenario())

    def test_given_the_modal_when_open_then_every_item_shares_one_left_edge(
        self, tmp_path
    ):
        # The name text, the step rows, and both button rows read as one column.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                # Text sits inside a border and padding, so the content edge is what
                # lines up for the labelled items; a button's own box edge is its text's.
                edges = {
                    app.screen.query_one(selector).content_region.x
                    for selector in (
                        "#macro-detail-name",
                        "#macro-detail-steps-label",
                        "#macro-detail-steps",
                        "#macro-detail-pause-label",
                    )
                } | {
                    app.screen.query_one(selector).region.x
                    for selector in ("#step-up", "#macro-save")
                }
                assert len(edges) == 1

        asyncio.run(scenario())

    def test_given_a_short_terminal_when_open_then_the_items_are_not_spaced_apart(
        self, tmp_path
    ):
        # The spacing costs five rows the shortest supported terminal cannot spare.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_SHORT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                title = app.screen.query_one("#macro-detail-title")
                name = app.screen.query_one("#macro-detail-name")
                assert name.region.y == title.region.bottom

        asyncio.run(scenario())

    def test_given_an_open_modal_when_the_terminal_shrinks_then_the_spacing_goes(
        self, tmp_path
    ):
        # The modal is already open, so only a resize can drop the spacing in time.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.resize_terminal(*_SHORT_SIZE)
                await pilot.pause()

                title = app.screen.query_one("#macro-detail-title")
                name = app.screen.query_one("#macro-detail-name")
                assert name.region.y == title.region.bottom

        asyncio.run(scenario())

    def test_given_the_run_control_then_it_reads_as_the_go_action(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                assert app.screen.query_one("#macro-run", Button).variant == "success"

        asyncio.run(scenario())


class TestDetailModalFits:
    def test_given_a_short_terminal_when_open_then_the_steps_scroll_and_buttons_fit(
        self, tmp_path
    ):
        # A long macro on the shortest supported terminal: every control must stay on
        # screen while the step list takes the squeeze.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Long", steps=[key_step("OK") for _ in range(30)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_SHORT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                width, height = _SHORT_SIZE
                for button in app.screen.query(Button):
                    region = button.region
                    assert region.width > 0 and region.height > 0
                    assert region.right <= width
                    assert region.bottom <= height
                # The list is what scrolls, so the buttons never had to — and it still
                # has rows to scroll: a 1fr list squeezed to zero height draws blank
                # while every button assertion above still passes.
                steps = app.screen.query_one("#macro-detail-steps", MacroOptionList)
                assert steps.region.height > 0
                assert steps.max_scroll_y > 0

        asyncio.run(scenario())


class TestRunFromTheDetailModal:
    def test_given_the_run_control_when_activated_then_the_macro_plays(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        # A long first step keeps the playback modal up long enough to be asserted on.
        macro = Macro(
            name="Login", steps=[pause_step(5000), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.click("#macro-run")
                await pilot.pause()

                assert isinstance(app.screen, MacroPlaybackModal)
                title = app.screen.query_one("#macro-playback-title")
                assert "Login" in str(title.content)

        asyncio.run(scenario())

    def test_given_a_cancelled_run_when_it_ends_then_the_remote_is_shown(
        self, tmp_path
    ):
        # Run leaves the macros list behind, unlike Save, Close, and Delete: the user
        # asked for the macro, not for more editing.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[pause_step(5000), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.click("#macro-run")
                await pilot.pause()
                await pilot.click("#macro-playback-cancel")
                await pilot.pause()
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

    def test_given_a_completed_run_when_it_ends_then_the_remote_is_shown(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Login", steps=[key_step("OK")], step_pause_ms=0)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.click("#macro-run")
                for _ in range(200):
                    if isinstance(app.screen, RemoteScreen):
                        break
                    await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert adapter.sessions[-1].sent_keys[-1] is Key.OK

        asyncio.run(scenario())

    def test_given_unsaved_edits_when_run_then_the_saved_macro_plays(self, tmp_path):
        # Run discards edits like Close does: what plays is the macro as saved.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[pause_step(5000), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.click("#macro-run")
                await pilot.pause()

                title = app.screen.query_one("#macro-playback-title")
                assert "Login" in str(title.content)
                assert get(app.macros, macro.id).name == "Login"

        asyncio.run(scenario())


class TestStepControls:
    def test_given_a_step_when_moved_up_then_only_the_draft_changes(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.press("down")  # step 2
                await pilot.click("#step-up")
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: DOWN",
                    "2. Key: HOME",
                    "3. Key: OK",
                ]
                # The stored macro is untouched until the user saves.
                assert [s["key"] for s in get(app.macros, macro.id).steps] == [
                    "HOME",
                    "DOWN",
                    "OK",
                ]

        asyncio.run(scenario())

    def test_given_a_step_when_moved_down_then_it_swaps_with_the_one_below(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-down")  # step 1 moves below step 2
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: DOWN",
                    "2. Key: HOME",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_the_first_step_when_moved_up_then_nothing_changes(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-up")
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_the_last_step_when_moved_down_then_nothing_changes(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())
                await pilot.press("down")
                await pilot.press("down")  # the last step

                await pilot.click("#step-down")
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_a_step_when_removed_then_it_leaves_the_listed_steps(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.press("down")
                await pilot.click("#step-remove")
                await pilot.pause()

                assert _step_rows(app) == ["1. Key: HOME", "2. Key: OK"]

        asyncio.run(scenario())

    def test_given_every_step_removed_then_a_placeholder_row_is_shown(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(
                    app, pilot, Macro(name="One", steps=[key_step("OK")])
                )

                await pilot.click("#step-remove")
                await pilot.pause()

                assert _step_rows(app) == ["No steps"]

        asyncio.run(scenario())


class TestAddStepByRecording:
    def test_given_add_step_when_one_key_is_sent_then_it_returns_with_that_step(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-add")
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)  # dismissed, not covered

                await pilot.press("space")  # one interaction: the Home key
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: HOME",
                    "3. Key: DOWN",
                    "4. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_add_step_when_activated_then_no_recording_hint_is_presented(
        self, tmp_path
    ):
        # The hint gates Create Macro alone: a user adding one step to a macro they are
        # already editing has met the recording state.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-add")
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)
                assert not any(
                    isinstance(screen, RecordingHintModal)
                    for screen in app.screen_stack
                )
                assert app.screen._recording is not None

        asyncio.run(scenario())

    def test_given_unsaved_edits_when_a_step_is_added_then_they_survive(self, tmp_path):
        # The round trip out to the live remote and back carries the same draft, so a
        # rename and a reorder made beforehand are still there.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.press("down")
                await pilot.click("#step-up")  # DOWN, HOME, OK
                await pilot.pause()
                await pilot.click("#step-add")
                await pilot.pause()
                await pilot.press("enter")  # the OK key
                await pilot.pause()

                assert app.screen.query_one("#macro-detail-name", Input).value == (
                    "Renamed"
                )
                assert _step_rows(app) == [
                    "1. Key: DOWN",
                    "2. Key: OK",
                    "3. Key: HOME",
                    "4. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_a_capture_when_cancelled_by_go_back_then_the_draft_is_unchanged(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())
                app.screen.query_one("#macro-detail-name", Input).value = "Renamed"
                await pilot.click("#step-add")
                await pilot.pause()

                await pilot.press("escape")
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert app.screen.query_one("#macro-detail-name", Input).value == (
                    "Renamed"
                )
                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_a_capture_when_cancelled_by_the_control_then_the_draft_is_unchanged(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())
                await pilot.click("#step-add")
                await pilot.pause()

                await pilot.click("#macros")  # the ■ Cancel control
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())


class TestPauseSteps:
    def test_given_a_duration_when_entered_then_a_pause_follows_the_selected_step(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-pause")
                await pilot.pause()
                assert isinstance(app.screen, PauseDurationModal)
                app.screen.query_one("#pause-duration-ms", Input).value = "500"
                await pilot.click("#pause-duration-ok")
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Pause: 500ms",
                    "3. Key: DOWN",
                    "4. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_the_prompt_when_cancelled_then_nothing_is_inserted(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                await pilot.click("#step-pause")
                await pilot.pause()
                await pilot.click("#pause-duration-cancel")
                await pilot.pause()

                assert _step_rows(app) == [
                    "1. Key: HOME",
                    "2. Key: DOWN",
                    "3. Key: OK",
                ]

        asyncio.run(scenario())

    def test_given_an_invalid_duration_when_entered_then_nothing_is_inserted(
        self, tmp_path
    ):
        # Negative, fractional, and non-numeric are all refused.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                for value in ("-5", "12.5", "soon", ""):
                    await pilot.click("#step-pause")
                    await pilot.pause()
                    app.screen.query_one("#pause-duration-ms", Input).value = value
                    await pilot.click("#pause-duration-ok")
                    await pilot.pause()
                    assert _step_rows(app) == [
                        "1. Key: HOME",
                        "2. Key: DOWN",
                        "3. Key: OK",
                    ], f"{value!r} was accepted"

        asyncio.run(scenario())

    def test_given_an_existing_pause_when_opened_then_the_prompt_is_prefilled(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Waits", steps=[pause_step(250)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.press("enter")  # open the highlighted pause step
                await pilot.pause()

                assert isinstance(app.screen, PauseDurationModal)
                assert app.screen.query_one("#pause-duration-ms", Input).value == "250"

        asyncio.run(scenario())

    def test_given_an_existing_pause_when_a_new_value_is_entered_then_it_replaces_it(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Waits", steps=[key_step("OK"), pause_step(250)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                await pilot.press("down")  # the pause step
                await pilot.press("enter")
                await pilot.pause()
                app.screen.query_one("#pause-duration-ms", Input).value = "900"
                await pilot.press("enter")
                await pilot.pause()

                assert _step_rows(app) == ["1. Key: OK", "2. Pause: 900ms"]
                # Still a draft edit: the saved macro keeps its old duration.
                assert get(app.macros, macro.id).steps[1] == pause_step(250)

        asyncio.run(scenario())

    def test_given_an_edited_pause_when_closed_then_reopening_shows_the_old_value(
        self, tmp_path
    ):
        # A draft's step list holds the same step dicts the registry does, so an edit
        # must replace a step rather than write into one. Close then reopen is what
        # would expose that: a mutated dict would show the new duration.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Waits", steps=[pause_step(250)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)
                await pilot.press("enter")  # open the pause step
                await pilot.pause()
                app.screen.query_one("#pause-duration-ms", Input).value = "900"
                await pilot.press("enter")
                await pilot.pause()

                await pilot.click("#macro-close")
                await pilot.pause()
                await pilot.press("enter")  # reopen the macro from the list
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert _step_rows(app) == ["1. Pause: 250ms"]

        asyncio.run(scenario())


class TestDefaultStepPause:
    def test_given_a_macro_when_opened_then_its_default_pause_is_prefilled(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _open_detail(app, pilot, _macro())

                assert app.screen.query_one("#macro-detail-pause", Input).value == "500"

        asyncio.run(scenario())

    def test_given_an_edited_default_pause_when_saved_then_it_is_persisted(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                app.screen.query_one("#macro-detail-pause", Input).value = "1200"
                await pilot.click("#macro-save")
                await pilot.pause()

                assert get(app.macros, macro.id).step_pause_ms == 1200
                stored = app.preferences.load().macros["items"][macro.id]
                assert stored["step_pause_ms"] == 1200

        asyncio.run(scenario())

    def test_given_an_edited_default_pause_when_closed_then_it_is_discarded(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                app.screen.query_one("#macro-detail-pause", Input).value = "1200"
                await pilot.click("#macro-close")
                await pilot.pause()

                assert get(app.macros, macro.id).step_pause_ms == 500

        asyncio.run(scenario())

    def test_given_an_invalid_default_pause_when_saved_then_the_old_value_is_kept(
        self, tmp_path
    ):
        # Same rule as the pause prompt: anything that is not a non-negative whole
        # number of milliseconds changes nothing rather than storing a nonsense pace.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = _macro()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, macro)

                # Cleared to retype, then given something that is not a number at all.
                for value in ("", "abc"):
                    app.screen.query_one("#macro-detail-pause", Input).value = value
                    await pilot.click("#macro-save")
                    await pilot.pause()

                    assert get(app.macros, macro.id).step_pause_ms == 500, (
                        f"{value!r} was accepted"
                    )
                    await pilot.press("enter")  # reopen it for the next value
                    await pilot.pause()

        asyncio.run(scenario())

    def test_given_an_edited_default_pause_when_a_step_is_added_then_it_survives(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                await _open_detail(app, pilot, _macro())

                app.screen.query_one("#macro-detail-pause", Input).value = "0"
                await pilot.click("#step-add")
                await pilot.pause()
                await pilot.press("enter")  # the one captured interaction
                await pilot.pause()

                assert isinstance(app.screen, MacroDetailModal)
                assert app.screen.query_one("#macro-detail-pause", Input).value == "0"

        asyncio.run(scenario())

    def test_given_one_macros_default_pause_when_changed_then_others_keep_theirs(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        edited = Macro(name="Edited", steps=[key_step("OK")])
        other = Macro(name="Other", steps=[key_step("OK")], step_pause_ms=250)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, edited)  # first, so it is the highlighted row
                add(app.macros, other)
                await pilot.click("#macros")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()

                app.screen.query_one("#macro-detail-pause", Input).value = "1200"
                await pilot.click("#macro-save")
                await pilot.pause()

                assert get(app.macros, other.id).step_pause_ms == 250

        asyncio.run(scenario())
