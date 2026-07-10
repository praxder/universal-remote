import asyncio

from textual.widgets import Label, OptionList

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.remote_flow import UseRemoteScreen
from universal_remote.tui.remote_screen import RemoteScreen


def _app(store, adapter=None):
    registry = AdapterRegistry()
    registry.register(adapter or FakeAdapter(platform="fake-tv"))
    return UniversalRemoteApp(store=store, registry=registry)


def _dev(**overrides) -> Device:
    base = dict(name="TV", platform="fake-tv", ip="1.1.1.1")
    base.update(overrides)
    return Device(**base)


class TestUseRemoteSelection:
    def test_given_multiple_devices_when_opening_use_remote_then_a_picker_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living"))
        store.add(_dev(name="Bedroom"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                assert isinstance(app.screen, UseRemoteScreen)
                picker = app.screen.query_one("#device-picker", OptionList)
                names = {
                    picker.get_option_at_index(i).prompt
                    for i in range(picker.option_count)
                }
                assert names == {"Living", "Bedroom"}

        asyncio.run(scenario())

    def test_given_no_devices_when_opening_use_remote_then_it_guides_to_add(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                message = str(app.screen.query_one("#no-devices", Label).content)
                assert "add" in message.lower()
                assert not isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())


class TestUseRemoteConnect:
    def test_given_a_stored_credential_when_selected_then_it_connects_without_pairing(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV", credential="tok"))
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert adapter.paired_devices == []
        assert len(adapter.sessions) == 1

    def test_given_no_credential_when_selected_then_pairing_stores_credential_and_opens_remote(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV"))
        adapter = FakeAdapter(platform="fake-tv", pair_token="new-tok")

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert len(adapter.paired_devices) == 1
        assert store.list()[0].credential == "new-tok"

    def test_given_cancelled_pairing_when_selected_then_no_remote_and_no_credential(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV"))
        adapter = FakeAdapter(platform="fake-tv", pair_cancels=True)

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()
                assert not isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert store.list()[0].credential is None


class TestUseRemoteExit:
    def test_given_use_remote_when_escaped_then_it_returns_to_the_menu(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)

        asyncio.run(scenario())
