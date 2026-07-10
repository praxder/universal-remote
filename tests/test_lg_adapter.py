import asyncio

import pytest

from tests.fakes import FakeWebOsClient
from universal_remote.adapters.lg import (
    LG_BUTTONS,
    PLATFORM,
    LgWebOsAdapter,
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


def _capturing_factory(created: list[FakeWebOsClient]):
    def factory(**kwargs):
        client = FakeWebOsClient(**kwargs)
        created.append(client)
        return client

    return factory


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


class TestLgRegistration:
    def test_given_the_registry_when_lg_is_registered_then_the_platform_resolves(self):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM


class TestLgCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_core_button_set_is_declared(
        self,
    ):
        caps = LgWebOsAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_and_power_on_are_declared(
        self,
    ):
        caps = LgWebOsAdapter().capabilities()

        assert caps.text is True
        assert caps.power_on is True


class TestLgPairing:
    def test_given_no_client_key_when_pairing_then_a_client_key_is_returned_via_the_prompt(
        self,
    ):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        client_key = run(adapter.pair(_device()))

        assert client_key == "fresh-client-key"
        assert created[0].prompt_shown is True

    def test_given_a_stored_client_key_when_connecting_then_no_prompt_is_shown(self):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        run(adapter.connect(_device(credential="stored-key")))

        assert created[0].client_key == "stored-key"
        assert created[0].prompt_shown is False


class TestLgKeyMapping:
    def test_given_the_button_map_when_read_then_generic_keys_map_to_lg_button_names(
        self,
    ):
        assert LG_BUTTONS[Key.UP] == "UP"
        assert LG_BUTTONS[Key.OK] == "ENTER"
        assert LG_BUTTONS[Key.BACK] == "BACK"
        assert LG_BUTTONS[Key.HOME] == "HOME"
        assert LG_BUTTONS[Key.VOL_UP] == "VOLUMEUP"
        assert LG_BUTTONS[Key.MUTE] == "MUTE"

    def test_given_a_directional_key_when_sent_then_the_lg_button_is_dispatched(self):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="k"))
            await session.send_key(Key.LEFT)

        run(scenario())

        assert created[0].sent_buttons == ["LEFT"]


class TestLgPower:
    def test_given_the_power_key_when_sent_over_a_session_then_the_tv_is_powered_off(
        self,
    ):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="k"))
            await session.send_key(Key.POWER)

        run(scenario())

        assert created[0].powered_off is True
        assert created[0].sent_buttons == []

    def test_given_a_stored_mac_when_power_on_requested_then_wol_is_sent_best_effort(
        self,
    ):
        sent: list[str] = []
        adapter = LgWebOsAdapter(wol=sent.append)

        result = adapter.power_on(_device(mac="aa:bb:cc:dd:ee:ff"))

        assert sent == ["aa:bb:cc:dd:ee:ff"]
        assert result.packet_sent is True
        assert result.best_effort is True

    def test_given_no_stored_mac_when_power_on_requested_then_no_packet_is_sent(self):
        sent: list[str] = []
        adapter = LgWebOsAdapter(wol=sent.append)

        result = adapter.power_on(_device(mac=None))

        assert sent == []
        assert result.packet_sent is False


class TestLgText:
    def test_given_text_when_sent_then_it_is_dispatched_to_the_tv(self):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="k"))
            await session.send_text("hello")

        run(scenario())

        assert created[0].sent_text == ["hello"]

    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="k"))
            created[0].send_error = RuntimeError("IME rejected the text")
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hello")

        run(scenario())
