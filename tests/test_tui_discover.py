import asyncio

from textual.widgets import OptionList

from tests.fakes import FakeDiscoverAdapter
from universal_remote.devices.store import DeviceStore
from universal_remote.discovery import DiscoveredDevice
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import AddDeviceScreen, DeviceListScreen
from universal_remote.tui.discover_screen import ADD_MANUAL_ID, DiscoverScreen


def _registry(*adapters: FakeDiscoverAdapter) -> AdapterRegistry:
    registry = AdapterRegistry()
    for adapter in adapters or (FakeDiscoverAdapter(),):
        registry.register(adapter)
    return registry


def _prompts(option_list: OptionList) -> list[str]:
    return [
        str(option_list.get_option_at_index(i).prompt)
        for i in range(option_list.option_count)
    ]


class TestDiscoveredRows:
    def test_given_a_discovered_device_when_shown_then_its_row_has_name_type_and_ip(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = _registry(
            FakeDiscoverAdapter(
                platform="roku",
                display_name="Roku",
                devices=[
                    DiscoveredDevice(name="Living Room", platform="roku", ip="10.0.0.5")
                ],
            )
        )

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                prompts = _prompts(picker)
                assert "1. Living Room — Roku (10.0.0.5)" in prompts
                assert prompts[-1] == "+ Add manually"

        asyncio.run(scenario())


class TestManualRow:
    def test_given_a_scan_in_flight_when_shown_then_the_manual_row_is_present_last(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        gate = asyncio.Event()  # never set: the scan stays in flight
        registry = _registry(FakeDiscoverAdapter(platform="roku", gate=gate))

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                assert _prompts(picker)[-1] == "+ Add manually"

        asyncio.run(scenario())

    def test_given_a_gated_adapter_when_a_fast_one_answers_then_its_row_streams_in(
        self, tmp_path
    ):
        # One adapter is held mid-scan; a second answers immediately. The fast
        # adapter's row must appear without waiting for the slow scan to finish.
        store = DeviceStore(path=tmp_path / "d.json")
        gate = asyncio.Event()
        registry = _registry(
            FakeDiscoverAdapter(platform="samsung-tizen", gate=gate),
            FakeDiscoverAdapter(
                platform="roku",
                display_name="Roku",
                devices=[DiscoveredDevice(name="Fast", platform="roku", ip="10.0.0.5")],
            ),
        )

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                prompts = _prompts(picker)
                assert any("Fast" in prompt for prompt in prompts)
                # The slow scan has not finished, so the status still shows searching.
                assert app.screen.query_one("#discover-status").display is True

        asyncio.run(scenario())

    def test_given_the_manual_row_when_selected_then_the_manual_add_flow_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        gate = asyncio.Event()  # still scanning when the manual row is selected
        registry = _registry(FakeDiscoverAdapter(platform="roku", gate=gate))

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                picker.highlighted = picker.option_count - 1  # the manual row
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen._existing is None

        asyncio.run(scenario())


class TestSelectDiscovered:
    def test_given_a_discovered_row_when_selected_then_it_is_saved_and_returns_to_list(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = _registry(
            FakeDiscoverAdapter(
                platform="apple-tv",
                display_name="Apple TV",
                devices=[
                    DiscoveredDevice(
                        name="Bedroom",
                        platform="apple-tv",
                        ip="10.0.0.42",
                        identifier="atv-9",
                    )
                ],
            )
        )

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                await pilot.press("d")  # open Manage Devices first
                await pilot.pause()
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                picker.highlighted = 0  # the discovered row
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())

        saved = store.list()
        assert [(d.name, d.platform, d.ip, d.identifier) for d in saved] == [
            ("Bedroom", "apple-tv", "10.0.0.42", "atv-9")
        ]

    def test_given_a_discovered_row_when_saved_then_a_success_toast_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = _registry(
            FakeDiscoverAdapter(
                platform="apple-tv",
                display_name="Apple TV",
                devices=[
                    DiscoveredDevice(
                        name="Bedroom",
                        platform="apple-tv",
                        ip="10.0.0.42",
                        identifier="atv-9",
                    )
                ],
            )
        )

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                picker.highlighted = 0  # the discovered row
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                messages = [n.message for n in app._notifications]
                assert 'Added "Bedroom".' in messages

        asyncio.run(scenario())


class TestDivider:
    def test_given_discovered_devices_when_shown_then_a_divider_sits_above_the_manual_row(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = _registry(
            FakeDiscoverAdapter(
                platform="roku",
                display_name="Roku",
                devices=[
                    DiscoveredDevice(name="Living Room", platform="roku", ip="10.0.0.5")
                ],
            )
        )

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                # the last device (the row just above the manual one) draws the divider
                last_device = picker.get_option_at_index(picker.option_count - 2)
                assert last_device._divider is True

        asyncio.run(scenario())

    def test_given_no_discovered_devices_when_only_manual_row_then_there_is_no_divider(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        registry = _registry(FakeDiscoverAdapter(platform="roku", devices=[]))

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.pause()
                picker = app.screen.query_one("#discover-list", OptionList)
                assert picker.option_count == 1
                manual = picker.get_option_at_index(0)
                assert manual.id == ADD_MANUAL_ID
                assert manual._divider is False

        asyncio.run(scenario())


class TestSearchingIndicator:
    def test_given_a_scan_in_flight_when_shown_then_an_animated_spinner_is_visible(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        gate = asyncio.Event()  # never set: the scan stays in flight
        registry = _registry(FakeDiscoverAdapter(platform="roku", gate=gate))

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                status = app.screen.query_one("#discover-status")
                assert status.display is True
                # an animated loading spinner accompanies the searching text
                assert app.screen.query_one("#discover-status LoadingIndicator")

        asyncio.run(scenario())


class TestDismiss:
    def test_given_a_scan_in_flight_when_escape_pressed_then_it_returns_to_the_list(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        gate = asyncio.Event()  # never set: dismiss happens mid-scan
        registry = _registry(FakeDiscoverAdapter(platform="roku", gate=gate))

        async def scenario():
            app = UniversalRemoteApp(store=store, registry=registry)
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                app.push_screen(DiscoverScreen())
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, DeviceListScreen)

        asyncio.run(scenario())
