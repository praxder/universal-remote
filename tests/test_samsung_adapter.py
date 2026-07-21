import asyncio

import pytest

from tests.fakes import FakeSamsungRemote
from universal_remote.adapters.samsung import (
    DISCOVERY_SERVICE,
    PLATFORM,
    SAMSUNG_KEYS,
    SamsungTizenAdapter,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.discovery import DiscoveredDevice, MdnsHit
from universal_remote.errors import ConnectionFailedError, TextUnsupportedError
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry

_CORE_KEYS = {
    Key.UP,
    Key.DOWN,
    Key.LEFT,
    Key.RIGHT,
    Key.OK,
    Key.BACK,
    Key.HOME,
    Key.VOL_UP,
    Key.VOL_DOWN,
    Key.MUTE,
}


def run(coro):
    return asyncio.run(coro)


def _capturing_factory(created: list[FakeSamsungRemote]):
    def factory(**kwargs):
        remote = FakeSamsungRemote(**kwargs)
        created.append(remote)
        return remote

    return factory


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


class TestSamsungRegistration:
    def test_given_the_registry_when_samsung_is_registered_then_the_platform_resolves(
        self,
    ):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM

    def test_given_the_adapter_when_display_name_read_then_it_is_human_readable(self):
        adapter = SamsungTizenAdapter()

        assert adapter.display_name == "Samsung Tizen"
        assert adapter.platform == PLATFORM

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_control_port(
        self,
    ):
        assert SamsungTizenAdapter().reachability_port == 8002


class TestSamsungCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_core_button_set_is_declared(
        self,
    ):
        caps = SamsungTizenAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys


class TestSamsungPairing:
    def test_given_no_token_when_pairing_then_a_token_is_returned_via_the_popup(self):
        created: list[FakeSamsungRemote] = []
        adapter = SamsungTizenAdapter(remote_factory=_capturing_factory(created))

        token = run(adapter.pair(_device()))

        assert token == "fresh-token"
        assert created[0].popup_shown is True
        assert created[0].port == 8002

    def test_given_a_stored_token_when_connecting_then_no_popup_is_shown(self):
        created: list[FakeSamsungRemote] = []
        adapter = SamsungTizenAdapter(remote_factory=_capturing_factory(created))

        run(adapter.connect(_device(credential="stored-token")))

        assert created[0].token == "stored-token"
        assert created[0].popup_shown is False


class TestSamsungConnectFailure:
    def test_given_connect_refused_when_connecting_then_connection_failed_is_raised(
        self,
    ):
        def factory(**kwargs):
            remote = FakeSamsungRemote(**kwargs)
            remote.open_error = ConnectionRefusedError("refused")
            return remote

        adapter = SamsungTizenAdapter(remote_factory=factory)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential="t")))

    def test_given_connect_times_out_when_connecting_then_it_is_bounded_and_wrapped(
        self,
    ):
        created: list[FakeSamsungRemote] = []

        def factory(**kwargs):
            remote = FakeSamsungRemote(**kwargs)
            remote.open_error = asyncio.TimeoutError()
            created.append(remote)
            return remote

        adapter = SamsungTizenAdapter(remote_factory=factory, connect_timeout=0.01)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential="t")))

        assert created[0].timeout == 0.01


class TestSamsungKeyMapping:
    def test_given_the_key_map_when_read_then_generic_keys_map_to_samsung_codes(self):
        assert SAMSUNG_KEYS[Key.UP] == "KEY_UP"
        assert SAMSUNG_KEYS[Key.OK] == "KEY_ENTER"
        assert SAMSUNG_KEYS[Key.BACK] == "KEY_RETURN"
        assert SAMSUNG_KEYS[Key.HOME] == "KEY_HOME"

    def test_given_the_key_map_when_read_then_menu_and_channel_keys_map(self):
        assert SAMSUNG_KEYS[Key.MENU] == "KEY_MENU"
        assert SAMSUNG_KEYS[Key.CH_UP] == "KEY_CHUP"
        assert SAMSUNG_KEYS[Key.CH_DOWN] == "KEY_CHDOWN"

    def test_given_the_key_map_when_read_then_media_keys_map_without_play_pause(self):
        assert SAMSUNG_KEYS[Key.PLAY] == "KEY_PLAY"
        assert SAMSUNG_KEYS[Key.PAUSE] == "KEY_PAUSE"
        assert SAMSUNG_KEYS[Key.REWIND] == "KEY_REWIND"
        assert SAMSUNG_KEYS[Key.FAST_FORWARD] == "KEY_FF"
        assert SAMSUNG_KEYS[Key.STOP] == "KEY_STOP"
        assert Key.PLAY_PAUSE not in SAMSUNG_KEYS

    def test_given_the_key_map_when_read_then_the_digit_keys_map_to_key_digits(self):
        for digit in range(10):
            assert SAMSUNG_KEYS[Key[f"NUM_{digit}"]] == f"KEY_{digit}"

    def test_given_a_directional_key_when_sent_then_the_samsung_code_is_dispatched(
        self,
    ):
        created: list[FakeSamsungRemote] = []
        adapter = SamsungTizenAdapter(remote_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="t"))
            await session.send_key(Key.LEFT)

        run(scenario())

        assert len(created[0].sent_payloads) == 1
        assert "KEY_LEFT" in created[0].sent_payloads[0]


class TestSamsungText:
    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        created: list[FakeSamsungRemote] = []
        adapter = SamsungTizenAdapter(remote_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="t"))
            created[0].send_error = RuntimeError("IME unavailable on this firmware")
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hello")

        run(scenario())


class TestSamsungDiscovery:
    def test_given_a_samsung_airplay_hit_when_discovering_then_it_is_reported(self):
        # A Samsung TV answers _airplay._tcp and tags its manufacturer as Samsung;
        # it is reported under the samsung-tizen platform with its instance name/IP.
        seen: list[str] = []

        async def fake_browse(service_type, timeout):
            seen.append(service_type)
            return [
                MdnsHit(
                    name="Living Room TV",
                    ip="10.0.0.5",
                    properties={"manufacturer": "Samsung Electronics"},
                )
            ]

        adapter = SamsungTizenAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found == [
            DiscoveredDevice(name="Living Room TV", platform=PLATFORM, ip="10.0.0.5")
        ]
        assert seen == [DISCOVERY_SERVICE]

    def test_given_a_non_samsung_airplay_hit_when_discovering_then_it_is_filtered_out(
        self,
    ):
        # Apple TVs and LG answer the same _airplay._tcp browse; only Samsung
        # responders are kept, so the manufacturer TXT filter drops the rest.
        async def fake_browse(service_type, timeout):
            return [
                MdnsHit(
                    name="Apple TV", ip="10.0.0.6", properties={"manufacturer": "Apple"}
                ),
                MdnsHit(
                    name="LG TV", ip="10.0.0.7", properties={"manufacturer": "LGE"}
                ),
                MdnsHit(name="No Maker", ip="10.0.0.8", properties={}),
                # A valueless manufacturer TXT decodes to None; it must be dropped,
                # not crash the whole scan.
                MdnsHit(name="Empty", ip="10.0.0.9", properties={"manufacturer": None}),
            ]

        adapter = SamsungTizenAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found == []

    def test_given_a_samsung_hit_with_a_blank_name_when_discovering_then_ip_is_used(
        self,
    ):
        # A Samsung hit (manufacturer still tags it) with no instance name falls
        # back to its IP via DiscoveredDevice.
        async def fake_browse(service_type, timeout):
            return [
                MdnsHit(
                    name="",
                    ip="10.0.0.5",
                    properties={"manufacturer": "Samsung"},
                )
            ]

        adapter = SamsungTizenAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found[0].name == "10.0.0.5"
        assert found[0].platform == "samsung-tizen"
