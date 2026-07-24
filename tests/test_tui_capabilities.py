import asyncio

from textual.widgets import Button, Input

from tests.fakes import FakeAdapter
from universal_remote.capabilities import Capabilities
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.remote_screen import RemoteScreen, TextEntryModal


def _app(store, adapter):
    registry = AdapterRegistry()
    registry.register(adapter)
    return UniversalRemoteApp(store=store, registry=registry)


def _store(tmp_path):
    store = DeviceStore(path=tmp_path / "d.json")
    store.add(Device(name="TV", platform="fake-tv", ip="1.1.1.1", credential="tok"))
    return store


async def _goto_remote(app, pilot):
    await pilot.press("r")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(app.screen, RemoteScreen)


class TestCapabilityDisabling:
    def test_given_an_unsupported_key_when_the_remote_shows_then_its_button_is_disabled(
        self, tmp_path
    ):
        caps = Capabilities(keys=frozenset(Key) - {Key.MUTE}, text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                assert app.screen.query_one("#key-mute", Button).disabled is True
                assert app.screen.query_one("#key-up", Button).disabled is False

        asyncio.run(scenario())

    def test_given_a_disabled_button_when_the_remote_shows_then_it_is_visibly_dimmed(
        self, tmp_path
    ):
        # Borderless buttons weaken Textual's default disabled cue, so the compact
        # style dims disabled text explicitly. Guard it so a future restyle cannot
        # silently drop the affordance.
        caps = Capabilities(keys=frozenset(Key) - {Key.MUTE}, text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                dimmed = app.screen.query_one("#key-mute", Button)
                full = app.screen.query_one("#key-up", Button)
                assert dimmed.styles.text_opacity == 0.4
                assert full.styles.text_opacity == 1.0

        asyncio.run(scenario())

    def test_given_play_pause_unsupported_when_the_remote_shows_then_only_it_is_disabled(
        self, tmp_path
    ):
        # LG/Samsung declare separate PLAY and PAUSE but no combined toggle.
        caps = Capabilities(keys=frozenset(Key) - {Key.PLAY_PAUSE}, text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                assert app.screen.query_one("#key-play_pause", Button).disabled is True
                assert app.screen.query_one("#key-play", Button).disabled is False
                assert app.screen.query_one("#key-pause", Button).disabled is False

        asyncio.run(scenario())

    def test_given_no_number_support_when_the_remote_shows_then_the_whole_pad_is_disabled(
        self, tmp_path
    ):
        # Apple TV declares no number keys, so the entire pad renders disabled.
        digits = {Key[f"NUM_{d}"] for d in range(10)}
        caps = Capabilities(keys=frozenset(Key) - digits, text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                for digit in range(10):
                    button = app.screen.query_one(f"#key-num_{digit}", Button)
                    assert button.disabled is True

        asyncio.run(scenario())

    def test_given_text_unsupported_when_text_activated_then_a_message_shows_and_no_input_opens(
        self, tmp_path
    ):
        caps = Capabilities(keys=frozenset(Key), text=False)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)
        captured: dict = {}

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")
                await pilot.pause()
                captured["screen"] = type(app.screen).__name__
                captured["messages"] = [
                    str(n.message).lower() for n in app._notifications
                ]

        asyncio.run(scenario())

        # No editable input opened (still on the remote), and a message explains it.
        assert captured["screen"] == "RemoteScreen"
        assert any("not supported" in message for message in captured["messages"])


class TestTextEntryModal:
    def test_given_text_activated_when_composed_and_entered_then_the_buffer_is_sent(
        self, tmp_path
    ):
        caps = Capabilities(keys=frozenset(Key), text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")
                await pilot.pause()
                assert isinstance(app.screen, TextEntryModal)
                assert app.focused is app.screen.query_one("#text-entry-input", Input)
                await pilot.press("h", "i")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                # Submitting sends once and returns to the remote.
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_text == ["hi"]

    def test_given_the_text_modal_when_escape_pressed_then_it_dismisses_without_back_or_close(
        self, tmp_path
    ):
        caps = Capabilities(keys=frozenset(Key), text=True)
        adapter = FakeAdapter(platform="fake-tv", capabilities=caps)

        async def scenario():
            app = _app(_store(tmp_path), adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")
                await pilot.pause()
                await pilot.press("a", "b")
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                # Escape closes the modal only; the live remote stays open.
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        session = adapter.sessions[0]
        assert Key.BACK not in session.sent_keys
        assert session.sent_text == []
        assert session.closed is False  # the remote session was not torn down
