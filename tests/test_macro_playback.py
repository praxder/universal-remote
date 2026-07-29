import asyncio
import time

from tests.fakes import FakeAdapter
from universal_remote.capabilities import Capabilities
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.macros.models import (
    Macro,
    action_step,
    key_step,
    pause_step,
    text_step,
)
from universal_remote.macros.registry import add
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.actions import (
    RUN_MACRO,
    ActionContext,
    MacroPlaybackModal,
    ScriptResultModal,
    run_macro,
)
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.custom_buttons import ButtonScope, set_action
from universal_remote.tui.remote_screen import RemoteScreen

_FIT_SIZE = (80, 45)
_SHORT_SIZE = (80, 24)

_OK_SCRIPT = {
    "type": "run_script",
    "source": "inline",
    "script": "exit 0",
    "show_results": True,
}
_FAILING_SCRIPT = {
    "type": "run_script",
    "source": "inline",
    "script": "exit 3",
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


def _context(app, session) -> ActionContext:
    return ActionContext(
        app=app,
        remote_ip="1.1.1.1",
        session=session,
        macros=app.macros,
        custom_buttons=app.custom_buttons,
        device_id="dev-1",
        platform="fake-tv",
    )


async def _start(app, pilot, adapter, macro):
    """Save `macro` and start playing it, returning the worker holding its result.

    Playback runs in a worker because `push_screen_wait` needs one — the same way a
    custom button reaches it, through `RemoteScreen._run_action`.
    """
    add(app.macros, macro)
    session = adapter.sessions[-1]
    worker = app.run_worker(
        run_macro({"type": RUN_MACRO, "macro_id": macro.id}, _context(app, session)),
        exit_on_error=False,
    )
    await pilot.pause()
    return worker


async def _play(app, pilot, adapter, macro, timeout=5):
    """Play `macro` to completion, returning its result."""
    worker = await _start(app, pilot, adapter, macro)
    for _ in range(200):
        if worker.is_finished:
            break
        await pilot.pause()
    return await asyncio.wait_for(worker.wait(), timeout)


def _record_pushes(app) -> list[str]:
    """Record the type name of every screen pushed from now on.

    A result modal presented mid-playback is popped again when the run ends, so the
    screen stack at the end of a run cannot see it — what was pushed at any point can.
    The patch is an instance attribute and is never restored; it lives only as long as
    this app does, which is the `run_test` scope.
    """
    pushed: list[str] = []
    original = app.push_screen

    def _push(screen, *args, **kwargs):
        pushed.append(type(screen).__name__)
        return original(screen, *args, **kwargs)

    app.push_screen = _push
    return pushed


def _messages(app) -> list[str]:
    return [str(note.message) for note in app._notifications]


def _titles(app) -> list[str]:
    return [str(note.title) for note in app._notifications]


class TestPlaybackModal:
    def test_given_a_macro_when_played_then_the_modal_names_it_and_its_progress(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[pause_step(5000), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                worker = await _start(app, pilot, adapter, macro)

                assert isinstance(app.screen, MacroPlaybackModal)
                title = app.screen.query_one("#macro-playback-title")
                progress = app.screen.query_one("#macro-playback-progress")
                assert "Login" in str(title.content)
                assert str(progress.content) == "Step 1 of 2 (Pause: 5000ms)"

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)

        asyncio.run(scenario())

    def test_given_the_run_advances_when_the_next_step_starts_then_it_is_named(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        # The second step is a long pause so the run sits on it long enough to read the
        # line naming it; a key or text send lands too fast to observe.
        macro = Macro(
            name="Login",
            steps=[key_step("HOME"), pause_step(5000)],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                worker = await _start(app, pilot, adapter, macro)
                progress = app.screen.query_one("#macro-playback-progress")
                for _ in range(50):
                    if "Step 2" in str(progress.content):
                        break
                    await pilot.pause()

                assert str(progress.content) == "Step 2 of 2 (Pause: 5000ms)"

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)

        asyncio.run(scenario())

    def test_given_a_macro_with_no_steps_when_played_then_the_run_completes(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Empty", steps=[], step_pause_ms=0)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                result = await _play(app, pilot, adapter, macro)

                assert result.ok
                assert "0 steps" in result.message

        asyncio.run(scenario())

    def test_given_a_long_step_description_when_played_then_cancel_stays_on_screen(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        # The macro's own gap is waited before the index advances, so a long gap holds
        # the line on step 1 — the step whose description has to fit.
        macro = Macro(
            name="Search",
            steps=[
                text_step("a very long search query the user typed in full"),
                key_step("OK"),
            ],
            step_pause_ms=5000,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_SHORT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                worker = await _start(app, pilot, adapter, macro)

                progress = app.screen.query_one("#macro-playback-progress")
                cancel = app.screen.query_one("#macro-playback-cancel")
                assert progress.size.height > 1  # the description wraps
                assert cancel.region.bottom <= _SHORT_SIZE[1]

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)

        asyncio.run(scenario())

    def test_given_the_last_step_when_it_completes_then_the_modal_dismisses(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[key_step("HOME"), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                await _play(app, pilot, adapter, macro)
                await pilot.pause()

                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

    def test_given_playback_in_progress_when_a_shortcut_is_pressed_then_nothing_is_sent(
        self, tmp_path
    ):
        # The modal freezes the remote: only the macro's own steps reach the device.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Slow", steps=[key_step("HOME"), pause_step(5000)], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)
                session = adapter.sessions[-1]

                # Keys the modal itself has no use for — Enter and Space would press
                # its focused Cancel button, which is the modal acting, not the remote.
                await pilot.press("j")  # the D-pad Down key on the remote
                await pilot.press("1")  # the NUM_1 shortcut
                await pilot.pause()

                assert session.sent_keys == [Key.HOME]  # the macro's step, and no more

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)

        asyncio.run(scenario())


class TestStepLoop:
    def test_given_key_text_and_pause_steps_when_played_then_each_runs_in_order(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Mixed",
            steps=[key_step("HOME"), pause_step(0), text_step("hi"), key_step("OK")],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                result = await _play(app, pilot, adapter, macro)

                session = adapter.sessions[-1]
                assert session.sent_keys == [Key.HOME, Key.OK]
                assert session.sent_text == ["hi"]
                assert result.ok is True

        asyncio.run(scenario())

    def test_given_every_step_succeeds_when_played_then_it_reports_the_count(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[key_step("HOME"), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                result = await _play(app, pilot, adapter, macro)

                assert result.ok is True
                assert "2 steps" in result.message
                assert "Login" in result.message

        asyncio.run(scenario())

    def test_given_a_show_results_script_step_that_succeeds_then_no_modal_interrupts(
        self, tmp_path
    ):
        # The captured Results choice does not apply during playback: a result modal
        # would sit mid-run waiting on the user. Playback continues to the next step.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Scripted",
            steps=[action_step(_OK_SCRIPT), key_step("OK")],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                pushed = _record_pushes(app)

                result = await _play(app, pilot, adapter, macro)
                await pilot.pause()

                assert ScriptResultModal.__name__ not in pushed
                assert adapter.sessions[-1].sent_keys == [Key.OK]  # the later step ran
                assert result.ok is True

        asyncio.run(scenario())

    def test_given_a_show_results_script_step_that_fails_then_it_aborts_without_a_modal(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Scripted",
            steps=[action_step(_FAILING_SCRIPT), key_step("OK")],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                pushed = _record_pushes(app)

                result = await _play(app, pilot, adapter, macro)
                await pilot.pause()

                assert ScriptResultModal.__name__ not in pushed
                assert adapter.sessions[-1].sent_keys == []  # no later step ran
                assert result.ok is False
                assert any("failed at step 1" in m for m in _messages(app))

        asyncio.run(scenario())


class TestAbortOnFailure:
    def test_given_an_unsupported_key_when_reached_then_the_run_aborts(self, tmp_path):
        # Arrange: an adapter without number keys, playing a macro that holds one.
        store = _store_with_device(tmp_path)
        keys = frozenset(key for key in Key if not key.name.startswith("NUM_"))
        adapter = FakeAdapter(
            platform="fake-tv", capabilities=Capabilities(keys=keys, text=True)
        )
        macro = Macro(
            name="Digits",
            steps=[key_step("HOME"), key_step("NUM_1"), key_step("OK")],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                result = await _play(app, pilot, adapter, macro)
                await pilot.pause()

                assert adapter.sessions[-1].sent_keys == [Key.HOME]  # stopped there
                assert result.ok is False
                assert "step 2" in result.message
                assert "Key: NUM_1" in result.message
                assert any("Digits" in m and "step 2" in m for m in _messages(app)), (
                    _messages(app)
                )
                assert "Macro failed" in _titles(app)

        asyncio.run(scenario())

    def test_given_a_failed_send_when_reached_then_the_run_aborts(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Login", steps=[key_step("HOME"), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[-1].dispatch_error = RuntimeError("unreachable")

                result = await _play(app, pilot, adapter, macro)
                await pilot.pause()

                assert adapter.sessions[-1].sent_keys == []
                assert result.ok is False
                assert "step 1" in result.message
                assert "unreachable" in result.message.lower()

        asyncio.run(scenario())

    def test_given_a_failed_text_send_when_reached_then_the_run_aborts(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Sign in", steps=[text_step("hi"), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[-1].text_dispatch_error = RuntimeError("nope")

                result = await _play(app, pilot, adapter, macro)

                assert adapter.sessions[-1].sent_keys == []
                assert result.ok is False
                assert 'Text: "hi"' in result.message

        asyncio.run(scenario())

    def test_given_a_nested_run_macro_step_when_reached_then_it_is_refused(
        self, tmp_path
    ):
        # Only a hand-edited file can hold one; playback refuses it rather than
        # recursing, and a refused step aborts the run like any other failure.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        inner = Macro(name="Inner", steps=[key_step("HOME")])
        outer = Macro(
            name="Outer",
            steps=[
                action_step({"type": RUN_MACRO, "macro_id": inner.id}),
                key_step("OK"),
            ],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, inner)

                result = await _play(app, pilot, adapter, outer)
                await pilot.pause()

                assert adapter.sessions[-1].sent_keys == []  # neither macro ran
                assert result.ok is False
                assert any("nested" in m.lower() for m in _messages(app))
                assert isinstance(app.screen, RemoteScreen)  # dismissed, not recursing

        asyncio.run(scenario())


class TestCancellation:
    def test_given_a_pause_when_cancelled_then_it_stops_without_waiting_it_out(
        self, tmp_path
    ):
        # A five-second pause: cancelling must stop the run there and then, so the
        # later step never runs and the wait resolves promptly.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Slow",
            steps=[key_step("HOME"), pause_step(5000), key_step("OK")],
            step_pause_ms=0,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)

                await pilot.click("#macro-playback-cancel")
                result = await asyncio.wait_for(
                    worker.wait(), 2
                )  # well under the 5s pause
                await pilot.pause()

                assert adapter.sessions[-1].sent_keys == [Key.HOME]
                assert result.ok is False
                assert "cancelled" in result.message.lower()
                assert "step 2" in result.message
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

    def test_given_playback_when_go_back_is_pressed_then_it_stops(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Slow", steps=[pause_step(5000), key_step("OK")], step_pause_ms=0
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)

                await pilot.press("escape")
                result = await asyncio.wait_for(worker.wait(), 2)

                assert adapter.sessions[-1].sent_keys == []
                assert result.ok is False

        asyncio.run(scenario())

    def test_given_a_cancelled_run_when_it_stops_then_no_error_is_raised(
        self, tmp_path
    ):
        # The user chose to stop it, so an error reporting their own choice is noise.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Slow", steps=[pause_step(5000)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)
                await pilot.pause()

                assert [n.severity for n in app._notifications] == []

        asyncio.run(scenario())

    def test_given_a_cancelled_run_when_it_settles_then_it_dismisses_exactly_once(
        self, tmp_path
    ):
        # Cancel and the step loop race: the worker's cancellation lands a tick later,
        # so the loop can reach its own ending first. Only one dismissal may happen.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Slow", steps=[pause_step(5000)])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)
                modal = app.screen

                modal._cancel()
                await pilot.pause()
                modal._cancel()  # a second attempt must change nothing
                await pilot.pause()

                result = await asyncio.wait_for(worker.wait(), 2)
                assert result.ok is False
                # A second dismissal would have popped the remote off the stack too.
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())


class TestPlaybackFromACustomButton:
    def test_given_a_button_assigned_a_macro_when_activated_then_it_plays(
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
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": RUN_MACRO, "macro_id": macro.id},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                await pilot.click("#custom-1")
                for _ in range(50):
                    await pilot.pause()
                    if adapter.sessions[-1].sent_keys:
                        break

                assert adapter.sessions[-1].sent_keys == [Key.HOME]

        asyncio.run(scenario())

    def test_given_a_deleted_macro_when_its_button_is_activated_then_it_is_reported(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": RUN_MACRO, "macro_id": "gone"},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                await pilot.click("#custom-1")
                for _ in range(50):
                    await pilot.pause()
                    if app._notifications:
                        break

                assert adapter.sessions[-1].sent_keys == []
                assert any("no longer exists" in m for m in _messages(app))

        asyncio.run(scenario())

    def test_given_an_aborted_macro_when_run_from_a_button_then_no_script_toast_appears(
        self, tmp_path
    ):
        # `present_result` toasts any not-ok result as "Script failed"; playback already
        # reported the failing step, so the shared path must stay quiet for this type.
        store = _store_with_device(tmp_path)
        device = store.list()[0]
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(name="Login", steps=[key_step("HOME")])

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                add(app.macros, macro)
                adapter.sessions[-1].dispatch_error = RuntimeError("unreachable")
                set_action(
                    app.custom_buttons,
                    1,
                    {"type": RUN_MACRO, "macro_id": macro.id},
                    ButtonScope.DEVICE,
                    device_id=device.id,
                    platform="fake-tv",
                )

                await pilot.click("#custom-1")
                for _ in range(50):
                    await pilot.pause()
                    if app._notifications:
                        break
                await pilot.pause()

                assert "Script failed" not in _titles(app)
                assert _titles(app) == ["Macro failed"]

        asyncio.run(scenario())


class TestDefaultStepPause:
    def test_given_a_long_default_pause_when_played_then_the_first_step_runs_at_once(
        self, tmp_path
    ):
        # The gap separates one send from the next, so there is nothing to wait for
        # before the first step.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Paced", steps=[key_step("HOME"), key_step("OK")], step_pause_ms=5000
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)

                for _ in range(50):
                    await pilot.pause()
                    if adapter.sessions[-1].sent_keys:
                        break

                assert adapter.sessions[-1].sent_keys == [Key.HOME]

                await pilot.click("#macro-playback-cancel")
                await asyncio.wait_for(worker.wait(), 2)

        asyncio.run(scenario())

    def test_given_a_default_pause_when_a_step_ends_then_the_next_waits_it_out(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Paced", steps=[key_step("HOME"), key_step("OK")], step_pause_ms=5000
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)
                worker = await _start(app, pilot, adapter, macro)

                for _ in range(50):
                    await pilot.pause()

                # Still inside the five-second gap, so the second key has not gone.
                assert adapter.sessions[-1].sent_keys == [Key.HOME]

                await pilot.click("#macro-playback-cancel")
                result = await asyncio.wait_for(worker.wait(), 2)

                # Cancelling inside a gap names the step that ran, not the one waiting.
                assert "step 1" in result.message

        asyncio.run(scenario())

    def test_given_a_pause_step_when_played_then_its_wait_adds_to_the_default(
        self, tmp_path
    ):
        # A pause step means "wait longer here": its duration is on top of the default
        # gap, not instead of it. Three keys and one 200ms pause with a 200ms default
        # is two gaps plus the pause — 600ms at the least.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")
        macro = Macro(
            name="Paced",
            steps=[key_step("HOME"), pause_step(200), key_step("OK")],
            step_pause_ms=200,
        )

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=_FIT_SIZE) as pilot:
                await _goto_remote(app, pilot)

                started = time.monotonic()
                result = await _play(app, pilot, adapter, macro)
                elapsed = time.monotonic() - started

                assert result.ok is True
                assert elapsed >= 0.6, elapsed

        asyncio.run(scenario())
