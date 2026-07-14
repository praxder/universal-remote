import asyncio

from textual.widgets import Button, Label

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.remote_screen import RemoteScreen, TextField


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


class TestRemoteSurface:
    def test_given_the_remote_when_shown_then_every_key_has_a_button(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                ids = {button.id for button in app.screen.query(Button)}
                expected = {f"key-{key.name.lower()}" for key in Key}
                assert expected <= ids

        asyncio.run(scenario())

    def test_given_a_button_when_clicked_then_the_mapped_key_is_sent(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.click("#key-mute")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.MUTE]

    def test_given_the_remote_when_arrow_keys_pressed_then_dpad_ok_and_back_map(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("up")
                await pilot.press("left")
                await pilot.press("enter")
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.UP,
            Key.LEFT,
            Key.OK,
            Key.BACK,
        ]

    def test_given_the_remote_when_vim_keys_pressed_then_the_dpad_directions_map(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("h")
                await pilot.press("j")
                await pilot.press("k")
                await pilot.press("l")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.LEFT,
            Key.DOWN,
            Key.UP,
            Key.RIGHT,
        ]

    def test_given_the_remote_when_space_pressed_then_home_is_sent(self, tmp_path):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("space")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [Key.HOME]

    def test_given_the_text_field_focused_when_vim_keys_and_space_typed_then_they_fill_not_navigate(
        self, tmp_path
    ):
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                await pilot.press("t")  # enter the text field
                await pilot.pause()
                await pilot.press("h", "j", "k", "l", "space")
                await pilot.pause()
                assert app.screen.query_one("#text", TextField).value == "hjkl "

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == []  # no D-pad, no HOME while typing

    def test_given_a_key_dispatch_fails_when_pressed_then_the_remote_survives(
        self, tmp_path
    ):
        # Arrange: a live remote whose device will fail the next key dispatch.
        store = _store_with_device(tmp_path)
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _goto_remote(app, pilot)
                adapter.sessions[0].dispatch_error = RuntimeError("device dropped")

                # Act: press a key that will raise inside dispatch.
                await pilot.press("up")
                await pilot.pause()

                # Assert: the remote is still up and reports the failure.
                assert isinstance(app.screen, RemoteScreen)
                status = app.screen.query_one("#text-status", Label)
                assert "UP" in str(status.content)

        asyncio.run(scenario())
