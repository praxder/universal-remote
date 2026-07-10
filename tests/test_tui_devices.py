import asyncio

from textual.widgets import Input, OptionList, Select, Static

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import (
    ADD_TITLE_ART,
    EDIT_TITLE_ART,
    AddDeviceScreen,
    ConfirmDeleteScreen,
    DeviceListScreen,
)


def _registry(*platforms: str):
    registry = AdapterRegistry()
    for platform in platforms or ("fake-tv",):
        registry.register(FakeAdapter(platform=platform))
    return registry


def _app(store, registry=None):
    return UniversalRemoteApp(store=store, registry=registry or _registry())


def _index_of(option_list: OptionList, option_id: str) -> int:
    for index in range(option_list.option_count):
        if option_list.get_option_at_index(index).id == option_id:
            return index
    raise AssertionError(f"option {option_id!r} not found")


class TestDeviceList:
    def test_given_saved_devices_when_opening_manage_devices_then_they_are_listed(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                option_list = app.screen.query_one("#device-list", OptionList)
                names = [
                    option_list.get_option_at_index(i).prompt
                    for i in range(option_list.option_count)
                ]
                assert "Living Room" in names

        asyncio.run(scenario())

    def test_given_no_devices_when_opening_manage_devices_then_only_the_add_row_shows(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                assert option_list.option_count == 1
                assert option_list.get_option_at_index(0).id == "__add__"

        asyncio.run(scenario())

    def test_given_saved_devices_when_opening_then_devices_first_then_add_row_last(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        first = store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        second = store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                ids = [
                    option_list.get_option_at_index(i).id
                    for i in range(option_list.option_count)
                ]
                assert ids == [first.id, second.id, "__add__"]

        asyncio.run(scenario())


class TestSelection:
    def test_given_the_add_row_when_selected_by_enter_then_the_add_flow_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing is None

        asyncio.run(scenario())

    def test_given_the_add_row_when_clicked_then_the_add_flow_opens(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                # the first list row renders at relative y=1 in the OptionList
                await pilot.click("#device-list", offset=(2, 1))
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing is None

        asyncio.run(scenario())

    def test_given_a_device_row_when_selected_by_enter_then_the_edit_flow_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        device = store.add(
            Device(name="Living Room", platform="fake-tv", ip="10.0.0.5")
        )

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, device.id)
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing.id == device.id

        asyncio.run(scenario())

    def test_given_a_device_row_when_clicked_then_the_edit_flow_opens(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")
        device = store.add(
            Device(name="Living Room", platform="fake-tv", ip="10.0.0.5")
        )

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                # the sole device is the first list row, at relative y=1
                await pilot.click("#device-list", offset=(2, 1))
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing.id == device.id

        asyncio.run(scenario())

    def test_given_the_add_row_highlighted_when_edit_or_delete_pressed_then_nothing_happens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("e")  # add row is the only (highlighted) row
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                await pilot.press("backspace")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)
                assert store.list() == []

        asyncio.run(scenario())


class TestAddDevice:
    def test_given_manual_ip_and_name_when_saved_then_the_device_persists(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("a")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                app.screen.query_one("#name", Input).value = "Bedroom TV"
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        saved = store.list()
        assert [d.name for d in saved] == ["Bedroom TV"]
        assert saved[0].ip == "10.0.0.9"
        assert saved[0].platform == "fake-tv"

    def test_given_the_add_flow_when_opened_then_the_add_banner_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("a")
                await pilot.pause()
                banner = app.screen.query_one("#add-title", Static)
                assert str(banner.render()) == ADD_TITLE_ART

        asyncio.run(scenario())

    def test_given_the_edit_flow_when_opened_then_the_edit_banner_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("e")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                banner = app.screen.query_one("#add-title", Static)
                assert str(banner.render()) == EDIT_TITLE_ART

        asyncio.run(scenario())

    def test_given_multiple_adapters_when_adding_then_the_selected_platform_is_saved(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store, registry=_registry("samsung-tizen", "lg-webos"))
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("a")
                await pilot.pause()
                selector = app.screen.query_one("#platform", Select)
                assert selector.value == "samsung-tizen"
                selector.value = "lg-webos"
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].platform == "lg-webos"


class TestEditAndDelete:
    def test_given_a_selected_device_when_edited_then_it_updates_without_adding(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Old", platform="fake-tv", ip="1.1.1.1"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("e")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                app.screen.query_one("#name", Input).value = "New"
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        remaining = store.list()
        assert len(remaining) == 1
        assert remaining[0].name == "New"

    def test_given_two_devices_when_one_is_deleted_then_only_it_is_removed(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Keep", platform="fake-tv", ip="1.1.1.1"))
        drop = store.add(Device(name="Drop", platform="fake-tv", ip="2.2.2.2"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, drop.id)
                await pilot.pause()
                await pilot.press("backspace")
                await pilot.pause()
                assert isinstance(app.screen, ConfirmDeleteScreen)
                await pilot.click("#confirm")
                await pilot.pause()

        asyncio.run(scenario())

        assert [d.name for d in store.list()] == ["Keep"]

    def test_given_a_device_when_delete_is_cancelled_then_it_is_kept(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")
        keep = store.add(Device(name="Keep", platform="fake-tv", ip="1.1.1.1"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, keep.id)
                await pilot.pause()
                await pilot.press("backspace")
                await pilot.pause()
                assert isinstance(app.screen, ConfirmDeleteScreen)
                await pilot.click("#cancel")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

        assert [d.name for d in store.list()] == ["Keep"]

    def test_given_the_confirm_prompt_when_arrow_pressed_then_focus_moves_between_buttons(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        device = store.add(Device(name="Keep", platform="fake-tv", ip="1.1.1.1"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, device.id)
                await pilot.pause()
                await pilot.press("backspace")
                await pilot.pause()
                assert isinstance(app.screen, ConfirmDeleteScreen)
                assert app.focused.id == "cancel"  # destructive action starts on cancel
                await pilot.press("up")
                await pilot.pause()
                assert app.focused.id == "confirm"

        asyncio.run(scenario())
