import asyncio

from textual.widgets import Input, Label, OptionList, Select, Static

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
from universal_remote.tui.discover_screen import DiscoverScreen


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


async def _open_manual_add(pilot) -> None:
    """Open the manual add form via the discovery screen's "+ Add manually" row.

    The add entry now opens discovery first; with the test registry's adapters
    declaring no discovery, the manual row is the sole (highlighted) row.
    """
    await pilot.press("a")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


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
                assert "1. Living Room" in names

        asyncio.run(scenario())

    def test_given_saved_devices_when_opening_then_rows_are_numbered_and_add_is_bare(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                prompts = [
                    option_list.get_option_at_index(i).prompt
                    for i in range(option_list.option_count)
                ]
                assert prompts == ["1. Living Room", "2. Bedroom", "+ Add"]

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
    def test_given_the_add_row_when_selected_by_enter_then_discovery_opens(
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
                assert isinstance(app.screen, DiscoverScreen)

        asyncio.run(scenario())

    def test_given_the_add_row_when_clicked_then_discovery_opens(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                # the first list row renders at relative y=1 in the OptionList
                await pilot.click("#device-list", offset=(2, 1))
                await pilot.pause()
                assert isinstance(app.screen, DiscoverScreen)

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

    def test_given_manage_devices_when_a_digit_is_pressed_then_the_nth_device_edits(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        second = store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("2")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing.id == second.id

        asyncio.run(scenario())

    def test_given_manage_devices_when_an_out_of_range_digit_is_pressed_then_nothing_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("2")  # only one device; index 2 is the add row
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

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
                await _open_manual_add(pilot)
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

    def test_given_a_manual_device_when_saved_then_a_success_toast_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                app.screen.query_one("#name", Input).value = "Bedroom TV"
                await pilot.click("#save")
                await pilot.pause()
                messages = [n.message for n in app._notifications]
                assert 'Added "Bedroom TV".' in messages

        asyncio.run(scenario())

    def test_given_the_add_flow_when_opened_then_cells_are_ordered_type_name_ip(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                children = app.screen.query_one("#add-device").children
                assert [w.id for w in children] == [
                    "add-title",
                    "platform",
                    "name",
                    "ip",
                    "text-adb-cell",
                    "error",
                    "save",
                ]

        asyncio.run(scenario())

    def test_given_multiple_adapters_when_adding_then_the_dropdown_shows_friendly_labels(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(platform="samsung-tizen", display_name="Samsung Tizen")
        )
        registry.register(FakeAdapter(platform="lg-webos", display_name="LG WebOS"))

        async def scenario():
            app = _app(store, registry=registry)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                selector = app.screen.query_one("#platform", Select)
                labels = [(str(prompt), value) for prompt, value in selector._options]
                assert labels == [
                    ("Samsung Tizen", "samsung-tizen"),
                    ("LG WebOS", "lg-webos"),
                ]
                assert selector.value == "samsung-tizen"

        asyncio.run(scenario())

    def test_given_the_add_flow_when_opened_then_the_add_banner_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
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
                await _open_manual_add(pilot)
                selector = app.screen.query_one("#platform", Select)
                assert selector.value == "samsung-tizen"
                selector.value = "lg-webos"
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].platform == "lg-webos"


class TestDuplicateRejection:
    def test_given_the_add_screen_opens_then_the_error_row_is_hidden(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                assert app.screen.query_one("#error", Label).display is False

        asyncio.run(scenario())

    def test_given_a_conflict_when_saving_then_the_error_row_becomes_visible(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "Living Room"
                await pilot.click("#save")
                await pilot.pause()
                assert app.screen.query_one("#error", Label).display is True

        asyncio.run(scenario())

    def test_given_a_duplicate_name_when_saving_a_new_device_then_it_is_blocked(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "living room"
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                await pilot.click("#save")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                error = str(app.screen.query_one("#error", Label).render())
                assert error == "A device named 'living room' already exists."

        asyncio.run(scenario())

        assert [d.name for d in store.list()] == ["Living Room"]

    def test_given_a_duplicate_ip_when_saving_a_new_device_then_it_is_blocked(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "Bedroom"
                app.screen.query_one("#ip", Input).value = "10.0.0.5"
                await pilot.click("#save")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                error = str(app.screen.query_one("#error", Label).render())
                assert error == "A device with IP 10.0.0.5 already exists."

        asyncio.run(scenario())

        assert [d.name for d in store.list()] == ["Living Room"]

    def test_given_a_unique_name_and_ip_when_saving_then_the_device_persists(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "Bedroom"
                app.screen.query_one("#ip", Input).value = "10.0.0.9"
                await pilot.click("#save")
                await pilot.pause()
                # A successful save closes the manual form back to the discovery
                # screen (which sits between the device list and the add form).
                assert isinstance(app.screen, DiscoverScreen)

        asyncio.run(scenario())

        assert sorted(d.name for d in store.list()) == ["Bedroom", "Living Room"]

    def test_given_an_edited_device_kept_unchanged_when_saved_then_it_persists(
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
                await pilot.click("#save")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

        assert [d.name for d in store.list()] == ["Living Room"]

    def test_given_an_edit_onto_another_devices_name_when_saved_then_it_is_blocked(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        bedroom = store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, bedroom.id)
                await pilot.pause()
                await pilot.press("e")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                app.screen.query_one("#name", Input).value = "Living Room"
                await pilot.click("#save")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                error = str(app.screen.query_one("#error", Label).render())
                assert error == "A device named 'Living Room' already exists."

        asyncio.run(scenario())

        assert sorted(d.name for d in store.list()) == ["Bedroom", "Living Room"]

    def test_given_an_edit_onto_another_devices_ip_when_saved_then_it_is_blocked(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        bedroom = store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                option_list.highlighted = _index_of(option_list, bedroom.id)
                await pilot.pause()
                await pilot.press("e")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                app.screen.query_one("#ip", Input).value = "10.0.0.5"
                await pilot.click("#save")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                error = str(app.screen.query_one("#error", Label).render())
                assert error == "A device with IP 10.0.0.5 already exists."

        asyncio.run(scenario())

        assert sorted(d.ip for d in store.list()) == ["10.0.0.5", "10.0.0.6"]


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

    def test_given_a_selected_device_when_edited_then_no_added_toast_is_shown(
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
                app.screen.query_one("#name", Input).value = "New"
                await pilot.click("#save")
                await pilot.pause()
                messages = [n.message for n in app._notifications]
                assert not any("Added" in m for m in messages)

        asyncio.run(scenario())

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


class TestVimNavigation:
    def test_given_a_device_list_when_j_and_k_pressed_then_the_highlight_moves(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="Living Room", platform="fake-tv", ip="10.0.0.5"))
        store.add(Device(name="Bedroom", platform="fake-tv", ip="10.0.0.6"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                option_list = app.screen.query_one("#device-list", OptionList)
                assert option_list.highlighted == 0
                await pilot.press("j")
                await pilot.pause()
                assert option_list.highlighted == 1
                await pilot.press("k")
                await pilot.pause()
                assert option_list.highlighted == 0

        asyncio.run(scenario())

    def test_given_the_confirm_dialog_when_hjkl_pressed_then_focus_moves(
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
                assert app.focused.id == "cancel"  # destructive action starts here
                await pilot.press("k")
                await pilot.pause()
                assert app.focused.id == "confirm"
                await pilot.press("j")
                await pilot.pause()
                assert app.focused.id == "cancel"
                await pilot.press("h")
                await pilot.pause()
                assert app.focused.id == "confirm"
                await pilot.press("l")
                await pilot.pause()
                assert app.focused.id == "cancel"

        asyncio.run(scenario())

    def test_given_the_name_input_when_vim_letters_typed_then_they_fill_and_focus_stays(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                name = app.screen.query_one("#name", Input)
                name.focus()
                await pilot.pause()
                assert app.focused.id == "name"
                await pilot.press("h", "j", "k", "l")
                await pilot.pause()
                assert name.value == "hjkl"
                assert app.focused.id == "name"

        asyncio.run(scenario())


class TestEditDeviceType:
    def test_given_the_edit_flow_when_opened_then_device_type_is_read_only(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(platform="samsung-tizen", display_name="Samsung Tizen")
        )
        store.add(Device(name="Den", platform="samsung-tizen", ip="10.0.0.5"))

        async def scenario():
            app = _app(store, registry=registry)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("e")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                display = app.screen.query_one("#platform-display", Input)
                assert display.value == "Samsung Tizen"
                assert display.disabled is True
                assert len(app.screen.query("#platform")) == 0

        asyncio.run(scenario())


class TestFormNavigation:
    def test_given_the_device_type_cell_when_arrows_pressed_then_focus_moves_through_cells(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                app.screen.query_one("#platform", Select).focus()
                await pilot.pause()
                assert app.focused.id == "platform"
                for expected in ("name", "ip", "save"):
                    await pilot.press("down")
                    await pilot.pause()
                    assert app.focused.id == expected
                await pilot.press("up")
                await pilot.pause()
                assert app.focused.id == "ip"

        asyncio.run(scenario())

    def test_given_the_device_type_cell_when_enter_pressed_then_the_dropdown_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await _open_manual_add(pilot)
                selector = app.screen.query_one("#platform", Select)
                selector.focus()
                await pilot.pause()
                assert selector.expanded is False
                await pilot.press("enter")
                await pilot.pause()
                assert selector.expanded is True

        asyncio.run(scenario())
