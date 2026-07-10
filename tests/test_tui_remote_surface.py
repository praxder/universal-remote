import asyncio

from textual.widgets import Button

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.remote_screen import RemoteScreen


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

    def test_given_the_remote_when_keys_pressed_then_dpad_ok_home_and_back_map(
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
                await pilot.press("h")
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(scenario())

        assert adapter.sessions[0].sent_keys == [
            Key.UP,
            Key.LEFT,
            Key.OK,
            Key.HOME,
            Key.BACK,
        ]
