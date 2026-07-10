import asyncio

import pytest

from tests.fakes import FakeSamsungRemote
from universal_remote.adapters.samsung import (
    PLATFORM,
    SAMSUNG_KEYS,
    SamsungTizenAdapter,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.errors import TextUnsupportedError
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
    Key.POWER,
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


class TestSamsungKeyMapping:
    def test_given_the_key_map_when_read_then_generic_keys_map_to_samsung_codes(self):
        assert SAMSUNG_KEYS[Key.UP] == "KEY_UP"
        assert SAMSUNG_KEYS[Key.OK] == "KEY_ENTER"
        assert SAMSUNG_KEYS[Key.BACK] == "KEY_RETURN"
        assert SAMSUNG_KEYS[Key.HOME] == "KEY_HOME"
        assert SAMSUNG_KEYS[Key.POWER] == "KEY_POWER"

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


class TestSamsungPower:
    def test_given_the_power_key_when_sent_over_a_session_then_the_power_code_is_dispatched(
        self,
    ):
        created: list[FakeSamsungRemote] = []
        adapter = SamsungTizenAdapter(remote_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="t"))
            await session.send_key(Key.POWER)

        run(scenario())

        assert "KEY_POWER" in created[0].sent_payloads[0]

    def test_given_a_stored_mac_when_power_on_requested_then_wol_is_sent_best_effort(
        self,
    ):
        sent: list[str] = []
        adapter = SamsungTizenAdapter(wol=sent.append)

        result = adapter.power_on(_device(mac="aa:bb:cc:dd:ee:ff"))

        assert sent == ["aa:bb:cc:dd:ee:ff"]
        assert result.packet_sent is True
        assert result.best_effort is True

    def test_given_no_stored_mac_when_power_on_requested_then_no_packet_is_sent(self):
        sent: list[str] = []
        adapter = SamsungTizenAdapter(wol=sent.append)

        result = adapter.power_on(_device(mac=None))

        assert sent == []
        assert result.packet_sent is False
