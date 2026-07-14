import asyncio

from textual.widgets import Button, Input, Label, OptionList

from tests.fakes import FakeAdapter
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.registry import AdapterRegistry
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.remote_flow import (
    ConnectingModal,
    PairingScreen,
    UseRemoteScreen,
)
from universal_remote.tui.remote_screen import RemoteScreen


def _app(store, adapter=None):
    registry = AdapterRegistry()
    registry.register(adapter or FakeAdapter(platform="fake-tv"))
    return UniversalRemoteApp(store=store, registry=registry)


def _dev(**overrides) -> Device:
    base = dict(name="TV", platform="fake-tv", ip="1.1.1.1")
    base.update(overrides)
    return Device(**base)


async def _settle(pilot, times: int = 6) -> None:
    # Reaching the remote now hops through a dismiss/callback per screen, so let
    # the loop cycle enough times for those to complete.
    for _ in range(times):
        await pilot.pause()


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
                assert names == {"1. Living", "2. Bedroom"}

        asyncio.run(scenario())

    def test_given_saved_devices_when_opening_use_remote_then_rows_are_numbered(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living"))
        store.add(_dev(name="Bedroom", ip="2.2.2.2"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                picker = app.screen.query_one("#device-picker", OptionList)
                prompts = [
                    picker.get_option_at_index(i).prompt
                    for i in range(picker.option_count)
                ]
                assert prompts == ["1. Living", "2. Bedroom"]

        asyncio.run(scenario())

    def test_given_use_remote_when_a_digit_is_pressed_then_the_nth_device_is_acted_on(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", credential="tok"))  # #1 would connect
        store.add(_dev(name="Bedroom", ip="2.2.2.2"))  # #2 has no credential
        adapter = FakeAdapter(platform="fake-tv", prompt_message="Enter the PIN")

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("2")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)
                assert app.screen._device.name == "Bedroom"

        asyncio.run(scenario())

    def test_given_use_remote_when_an_out_of_range_digit_is_pressed_then_nothing_happens(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", credential="tok"))
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("2")  # only one device
                await _settle(pilot)
                assert isinstance(app.screen, UseRemoteScreen)

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


class TestUseRemoteVimNavigation:
    def test_given_the_picker_when_j_and_k_pressed_then_the_highlight_moves(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living"))
        store.add(_dev(name="Bedroom", ip="2.2.2.2"))

        async def scenario():
            app = _app(store)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                picker = app.screen.query_one("#device-picker", OptionList)
                assert picker.highlighted == 0
                await pilot.press("j")
                await pilot.pause()
                assert picker.highlighted == 1
                await pilot.press("k")
                await pilot.pause()
                assert picker.highlighted == 0

        asyncio.run(scenario())


class TestUseRemoteConnect:
    def test_given_a_stored_credential_when_selected_then_it_connects_without_pairing(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV", credential="tok"))
        adapter = FakeAdapter(platform="fake-tv")

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold the connect mid-flight
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                # selection routes through the connecting modal, not a raw connect
                assert isinstance(app.screen, ConnectingModal)
                adapter.connect_gate.set()
                await _settle(pilot)
                assert isinstance(app.screen, RemoteScreen)
                # the modal dismissed itself; nothing orphaned below
                assert isinstance(app.screen_stack[-2], UseRemoteScreen)

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
            adapter.connect_gate = asyncio.Event()  # hold the connect mid-flight
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                # after pairing, the flow hands off to the connecting modal
                assert isinstance(app.screen, ConnectingModal)
                adapter.connect_gate.set()
                await _settle(pilot)
                assert isinstance(app.screen, RemoteScreen)
                # pairing and the modal both dismissed; nothing orphaned below
                assert isinstance(app.screen_stack[-2], UseRemoteScreen)

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
                await _settle(pilot)
                assert isinstance(app.screen, UseRemoteScreen)

        asyncio.run(scenario())

        assert store.list()[0].credential is None


class TestPairingPinEntry:
    def test_given_an_adapter_prompts_when_pairing_then_a_pin_entry_state_is_shown(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="ATV"))
        adapter = FakeAdapter(
            platform="fake-tv", prompt_message="Enter the PIN shown on your Apple TV"
        )

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)
                guidance = str(app.screen.query_one("#pairing-guidance", Label).content)
                assert "PIN" in guidance
                assert app.screen.query_one("#pin-entry").display is True

        asyncio.run(scenario())

    def test_given_a_pin_is_submitted_when_pairing_then_credential_and_identifier_stored(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="ATV"))
        adapter = FakeAdapter(
            platform="fake-tv",
            pair_token="atv-cred",
            prompt_message="Enter the PIN",
            pair_identifier="atv-id-9",
        )

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold the connect mid-flight
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)
                app.screen.query_one("#pin-input", Input).value = "1234"
                app.screen.query_one("#submit", Button).press()
                await _settle(pilot)
                assert isinstance(app.screen, ConnectingModal)
                adapter.connect_gate.set()
                await _settle(pilot)
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert adapter.entered_values == ["1234"]
        saved = store.list()[0]
        assert saved.credential == "atv-cred"
        assert saved.identifier == "atv-id-9"

    def test_given_a_pin_when_submitted_via_enter_then_pairing_completes(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="ATV"))
        adapter = FakeAdapter(
            platform="fake-tv", pair_token="atv-cred", prompt_message="Enter the PIN"
        )

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold the connect mid-flight
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)
                app.screen.query_one("#pin-input", Input).value = "4321"
                await pilot.press("enter")  # submit the PIN from the focused input
                await _settle(pilot)
                assert isinstance(app.screen, ConnectingModal)
                adapter.connect_gate.set()
                await _settle(pilot)
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert adapter.entered_values == ["4321"]
        assert store.list()[0].credential == "atv-cred"

    def test_given_a_pin_prompt_when_cancelled_then_no_remote_and_no_credential(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="ATV"))
        adapter = FakeAdapter(
            platform="fake-tv",
            prompt_message="Enter the PIN",
            pair_identifier="atv-id-9",
        )

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)
                await pilot.press("escape")
                await _settle(pilot)
                assert isinstance(app.screen, UseRemoteScreen)

        asyncio.run(scenario())

        saved = store.list()[0]
        assert saved.credential is None
        assert saved.identifier is None


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
