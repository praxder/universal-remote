import asyncio

from textual.widgets import Input, Label, Select, Switch

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.devices_screen import (
    AddDeviceScreen,
    AdbTextSetupScreen,
)
from universal_remote.tui.remote_screen import RemoteScreen


def _app(store, *adapters):
    registry = AdapterRegistry()
    for adapter in adapters:
        registry.register(adapter)
    return UniversalRemoteApp(store=store, registry=registry)


def _android(**kwargs) -> FakeAdapter:
    kwargs.setdefault("supports_adb_text", True)
    return FakeAdapter(platform="androidtv", display_name="Android TV", **kwargs)


async def _open_manual_add(pilot) -> None:
    await pilot.press("d")
    await pilot.pause()
    await pilot.press("a")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def _open_edit(pilot) -> None:
    await pilot.press("d")
    await pilot.pause()
    await pilot.press("e")
    await pilot.pause()


class TestToggleVisibility:
    def test_given_android_tv_when_adding_then_the_toggle_is_shown(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store, _android())
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen.query_one("#text-adb-cell").display is True

        asyncio.run(scenario())

    def test_given_a_non_android_device_when_adding_then_the_toggle_is_hidden(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store, FakeAdapter(platform="roku"))
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                assert app.screen.query_one("#text-adb-cell").display is False

        asyncio.run(scenario())

    def test_given_two_types_when_selecting_android_then_the_toggle_appears(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store, FakeAdapter(platform="roku"), _android())
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                select = app.screen.query_one("#platform", Select)
                cell = app.screen.query_one("#text-adb-cell")
                select.value = "roku"
                await pilot.pause()
                assert cell.display is False
                select.value = "androidtv"
                await pilot.pause()
                assert cell.display is True

        asyncio.run(scenario())


class TestSwitchToAdb:
    def test_given_the_toggle_flipped_to_adb_then_the_pairing_modal_opens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")

        async def scenario():
            app = _app(store, _android())
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                app.screen.query_one("#text-adb-switch", Switch).value = True
                await pilot.pause()
                assert isinstance(app.screen, AdbTextSetupScreen)

        asyncio.run(scenario())

    def test_given_pairing_succeeds_and_saved_then_the_device_is_opted_in(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        adapter = _android(adb_pair_result=True)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "TV"
                app.screen.query_one("#ip", Input).value = "10.0.0.5"
                app.screen.query_one("#text-adb-switch", Switch).value = True
                await pilot.pause()
                assert isinstance(app.screen, AdbTextSetupScreen)
                app.screen.query_one("#adb-address", Input).value = "10.0.0.5:42133"
                app.screen.query_one("#adb-code", Input).value = "123456"
                await pilot.click("#adb-setup-submit")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen.query_one("#text-adb-switch", Switch).value is True
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].text_via_adb is True
        assert adapter.adb_pair_calls == [("10.0.0.5:42133", "123456")]

    def test_given_pairing_cancelled_then_the_toggle_reverts_and_no_opt_in(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        adapter = _android()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                app.screen.query_one("#name", Input).value = "TV"
                app.screen.query_one("#ip", Input).value = "10.0.0.5"
                app.screen.query_one("#text-adb-switch", Switch).value = True
                await pilot.pause()
                assert isinstance(app.screen, AdbTextSetupScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen.query_one("#text-adb-switch", Switch).value is False
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].text_via_adb is False
        assert adapter.adb_pair_calls == []

    def test_given_pairing_fails_then_the_setup_screen_stays_with_a_status(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        adapter = _android(adb_pair_result=False)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_manual_add(pilot)
                app.screen.query_one("#text-adb-switch", Switch).value = True
                await pilot.pause()
                app.screen.query_one("#adb-address", Input).value = "10.0.0.5:42133"
                app.screen.query_one("#adb-code", Input).value = "000000"
                await pilot.click("#adb-setup-submit")
                await pilot.pause()
                assert isinstance(app.screen, AdbTextSetupScreen)
                status = str(app.screen.query_one("#adb-setup-status", Label).render())
                assert "fail" in status.lower()

        asyncio.run(scenario())


class TestEditFlip:
    def test_given_an_opted_in_device_when_editing_then_no_modal_and_switch_is_on(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(
            Device(name="TV", platform="androidtv", ip="10.0.0.5", text_via_adb=True)
        )
        adapter = _android()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_edit(pilot)
                assert isinstance(app.screen, AddDeviceScreen)
                assert app.screen.query_one("#text-adb-switch", Switch).value is True
                assert adapter.adb_pair_calls == []

        asyncio.run(scenario())

    def test_given_a_standard_device_when_switched_to_adb_and_saved_then_it_opts_in(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(
            Device(name="TV", platform="androidtv", ip="10.0.0.5", text_via_adb=False)
        )
        adapter = _android(adb_pair_result=True)

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_edit(pilot)
                assert app.screen.query_one("#text-adb-switch", Switch).value is False
                app.screen.query_one("#text-adb-switch", Switch).value = True
                await pilot.pause()
                assert isinstance(app.screen, AdbTextSetupScreen)
                app.screen.query_one("#adb-address", Input).value = "10.0.0.5:42133"
                app.screen.query_one("#adb-code", Input).value = "123456"
                await pilot.click("#adb-setup-submit")
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].text_via_adb is True
        assert adapter.adb_pair_calls == [("10.0.0.5:42133", "123456")]

    def test_given_an_opted_in_device_when_switched_off_and_saved_then_it_opts_out(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(
            Device(name="TV", platform="androidtv", ip="10.0.0.5", text_via_adb=True)
        )
        adapter = _android()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test() as pilot:
                await _open_edit(pilot)
                app.screen.query_one("#text-adb-switch", Switch).value = False
                await pilot.pause()
                assert isinstance(app.screen, AddDeviceScreen)  # no modal on switch-off
                await pilot.click("#save")
                await pilot.pause()

        asyncio.run(scenario())

        assert store.list()[0].text_via_adb is False
        assert adapter.adb_pair_calls == []


class TestDeviceListHasNoTextAction:
    def test_given_the_device_list_when_t_is_pressed_then_nothing_opens(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(Device(name="TV", platform="androidtv", ip="10.0.0.5"))

        async def scenario():
            app = _app(store, _android())
            async with app.run_test() as pilot:
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("t")
                await pilot.pause()
                assert not isinstance(app.screen, AdbTextSetupScreen)

        asyncio.run(scenario())


class TestAdbTextFallbackStatus:
    def test_given_a_send_falls_back_when_submitted_then_the_remote_shows_a_status(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(
            Device(name="TV", platform="androidtv", ip="10.0.0.5", credential="tok")
        )
        adapter = _android()

        async def scenario():
            app = _app(store, adapter)
            async with app.run_test(size=(80, 45)) as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, RemoteScreen)
                app.screen._session.adb_text_unavailable = True
                await pilot.press("t")
                await pilot.pause()
                field = app.screen.query_one("#text-entry-input", Input)
                field.value = "hello"
                await pilot.press("enter")
                await pilot.pause()
                messages = [str(n.message).lower() for n in app._notifications]
                assert any("adb" in message for message in messages)

        asyncio.run(scenario())
