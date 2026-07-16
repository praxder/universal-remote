import asyncio

from textual.widgets import Button, Input, Label, OptionList

from tests.fakes import FakeAdapter, FakeSession
from universal_remote.capabilities import Capabilities
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.keys import Key
from universal_remote.reachability import Reachability
from universal_remote.registry import AdapterRegistry
from universal_remote.tui import remote_flow
from universal_remote.tui.app import UniversalRemoteApp
from universal_remote.tui.menu import MenuScreen
from universal_remote.tui.remote_flow import (
    ConnectingModal,
    PairingScreen,
    UseRemoteScreen,
)
from universal_remote.tui.remote_screen import RemoteScreen


class _NoAttrAdapter:
    """An adapter that declares no `requires_pairing` — the getattr default applies.

    Its pairing blocks on an unset event so a test can assert PairingScreen mounted
    rather than racing past it once pairing completes.
    """

    platform = "fake-tv"
    display_name = "Fake"

    def __init__(self) -> None:
        self._caps = Capabilities(keys=frozenset(Key), text=True)

    def capabilities(self) -> Capabilities:
        return self._caps

    async def pair(self, device, *, prompt=None) -> str:
        await asyncio.Event().wait()  # never resolves; parks the flow in pairing
        return "tok"

    async def connect(self, device) -> FakeSession:
        return FakeSession(self._caps)


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
                assert names == {"[yellow]●[/] 1. Living", "[yellow]●[/] 2. Bedroom"}

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
                assert prompts == ["[yellow]●[/] 1. Living", "[yellow]●[/] 2. Bedroom"]

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


class TestUseRemoteNoPairing:
    def test_given_a_no_pairing_adapter_and_no_credential_when_selected_then_it_connects_directly(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Roku"))  # no credential stored
        adapter = FakeAdapter(platform="fake-tv", requires_pairing=False)

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold the connect mid-flight
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                # goes straight to connecting, never mounting PairingScreen
                assert isinstance(app.screen, ConnectingModal)
                adapter.connect_gate.set()
                await _settle(pilot)
                assert isinstance(app.screen, RemoteScreen)

        asyncio.run(scenario())

        assert adapter.paired_devices == []  # pairing was never run
        assert store.list()[0].credential is None

    def test_given_a_pairing_adapter_and_no_credential_when_selected_then_pairing_runs(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV"))  # no credential stored
        # Default FakeAdapter requires pairing; prompt_message parks it in pairing.
        adapter = FakeAdapter(platform="fake-tv", prompt_message="Enter the PIN")

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)

        asyncio.run(scenario())

    def test_given_an_adapter_declaring_nothing_when_selected_then_pairing_runs(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="TV"))  # no credential stored

        async def scenario():
            app = _app(store, adapter=_NoAttrAdapter())
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, PairingScreen)

        asyncio.run(scenario())


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


class _FakeProbe:
    """A stand-in for `reachability.probe`: canned per-ip results, optional gate.

    Records each (ip, port) call so a test can count re-probes; the gate parks
    the probe so a test can assert the pre-resolution yellow state.
    """

    def __init__(
        self,
        results: dict[str, Reachability],
        gate: asyncio.Event | None = None,
    ) -> None:
        self._results = results
        self._gate = gate
        self.calls: list[tuple[str, int]] = []

    async def __call__(self, ip: str, port: int, timeout: float) -> Reachability:
        self.calls.append((ip, port))
        if self._gate is not None:
            await self._gate.wait()
        return self._results.get(ip, Reachability.UNREACHABLE)


class TestUseRemoteReachability:
    def test_given_probes_pending_when_opening_then_every_row_starts_yellow(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1"))
        store.add(_dev(name="Bedroom", ip="2.2.2.2"))
        gate = asyncio.Event()  # keeps probes in flight so nothing resolves yet
        probe = _FakeProbe({}, gate=gate)
        monkeypatch.setattr(remote_flow, "probe", probe)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                picker = app.screen.query_one("#device-picker", OptionList)
                prompts = [
                    picker.get_option_at_index(i).prompt
                    for i in range(picker.option_count)
                ]
                assert prompts == [
                    "[yellow]●[/] 1. Living",
                    "[yellow]●[/] 2. Bedroom",
                ]
                assert len(probe.calls) == 2  # probes started but parked on the gate
                gate.set()  # release so teardown is clean

        asyncio.run(scenario())

    def test_given_probes_resolve_when_open_then_bubbles_turn_green_and_red(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1"))
        store.add(_dev(name="Bedroom", ip="2.2.2.2"))
        gate = asyncio.Event()  # hold probes so the cursor can be moved first
        probe = _FakeProbe(
            {"1.1.1.1": Reachability.REACHABLE, "2.2.2.2": Reachability.UNREACHABLE},
            gate=gate,
        )
        monkeypatch.setattr(remote_flow, "probe", probe)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause()
                picker = app.screen.query_one("#device-picker", OptionList)
                picker.highlighted = 1  # move the cursor off row 0 before resolving
                gate.set()  # now let the probes resolve and update rows in place
                await _settle(pilot)
                prompts = [
                    picker.get_option_at_index(i).prompt
                    for i in range(picker.option_count)
                ]
                assert prompts == ["[green]●[/] 1. Living", "[red]●[/] 2. Bedroom"]
                assert picker.highlighted == 1  # in-place update preserved the cursor

        asyncio.run(scenario())

    def test_given_a_portless_adapter_when_open_then_the_row_stays_yellow(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1"))
        probe = _FakeProbe({"1.1.1.1": Reachability.REACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        adapter = FakeAdapter(platform="fake-tv")  # declares no reachability_port

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await _settle(pilot)
                picker = app.screen.query_one("#device-picker", OptionList)
                assert picker.get_option_at_index(0).prompt == "[yellow]●[/] 1. Living"
                assert probe.calls == []  # portless: never probed

        asyncio.run(scenario())

    def test_given_a_red_device_when_selected_then_the_connect_flow_still_begins(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1", credential="tok"))
        probe = _FakeProbe({"1.1.1.1": Reachability.UNREACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold connect so the modal stays up
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await _settle(pilot)
                picker = app.screen.query_one("#device-picker", OptionList)
                assert picker.get_option_at_index(0).prompt == "[red]●[/] 1. Living"
                await pilot.press("enter")
                await _settle(pilot)
                assert isinstance(app.screen, ConnectingModal)

        asyncio.run(scenario())

    def test_given_the_screen_stays_open_when_the_interval_fires_then_it_reprobes(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1"))
        probe = _FakeProbe({"1.1.1.1": Reachability.REACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        monkeypatch.setattr(UseRemoteScreen, "POLL_INTERVAL", 0.05)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                for _ in range(6):
                    await pilot.pause(0.05)
                assert len(probe.calls) >= 2  # initial cycle plus at least one re-probe

        asyncio.run(scenario())

    def test_given_the_screen_is_left_when_time_passes_then_no_more_probes(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1"))
        probe = _FakeProbe({"1.1.1.1": Reachability.REACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        monkeypatch.setattr(UseRemoteScreen, "POLL_INTERVAL", 0.05)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause(0.05)
                await pilot.press("escape")  # leave the Use Remote picker
                await pilot.pause()
                assert isinstance(app.screen, MenuScreen)
                count_after_leaving = len(probe.calls)
                for _ in range(6):
                    await pilot.pause(0.05)
                assert len(probe.calls) == count_after_leaving  # no further probes

        asyncio.run(scenario())

    def test_given_a_screen_is_pushed_on_top_when_time_passes_then_probing_pauses(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1", credential="tok"))
        probe = _FakeProbe({"1.1.1.1": Reachability.REACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        monkeypatch.setattr(UseRemoteScreen, "POLL_INTERVAL", 0.05)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # keep ConnectingModal on top
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause(0.05)
                await pilot.press("enter")  # select: pushes ConnectingModal on top
                await _settle(pilot)
                assert isinstance(app.screen, ConnectingModal)
                paused_at = len(probe.calls)
                for _ in range(6):
                    await pilot.pause(0.05)
                assert len(probe.calls) == paused_at  # covered picker does not probe

        asyncio.run(scenario())

    def test_given_the_top_screen_is_dismissed_when_time_passes_then_probing_resumes(
        self, tmp_path, monkeypatch
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_dev(name="Living", ip="1.1.1.1", credential="tok"))
        probe = _FakeProbe({"1.1.1.1": Reachability.REACHABLE})
        monkeypatch.setattr(remote_flow, "probe", probe)
        monkeypatch.setattr(UseRemoteScreen, "POLL_INTERVAL", 0.05)
        adapter = FakeAdapter(platform="fake-tv", reachability_port=9999)

        async def scenario():
            adapter.connect_gate = asyncio.Event()  # hold connect so the modal stays up
            app = _app(store, adapter=adapter)
            async with app.run_test() as pilot:
                await pilot.press("r")
                await pilot.pause(0.05)
                await pilot.press("enter")  # push ConnectingModal on top
                await _settle(pilot)
                assert isinstance(app.screen, ConnectingModal)
                await pilot.press("escape")  # dismiss: picker is visible again
                await _settle(pilot)
                assert isinstance(app.screen, UseRemoteScreen)
                resumed_at = len(probe.calls)
                for _ in range(6):
                    await pilot.pause(0.05)
                assert len(probe.calls) > resumed_at  # probing resumed on return

        asyncio.run(scenario())
