import asyncio

import pytest

from tests.fakes import FakeWebOsClient
from universal_remote.adapters.lg import (
    DISCOVERY_TARGET,
    LG_BUTTONS,
    PLATFORM,
    LgWebOsAdapter,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.discovery import DiscoveredDevice, SsdpHit
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

    def test_given_the_adapter_when_display_name_read_then_it_is_human_readable(self):
        adapter = LgWebOsAdapter()

        assert adapter.display_name == "LG WebOS"
        assert adapter.platform == PLATFORM

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_webos_port(
        self,
    ):
        assert LgWebOsAdapter().reachability_port == 3000


class TestLgCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_core_button_set_is_declared(
        self,
    ):
        caps = LgWebOsAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(
        self,
    ):
        caps = LgWebOsAdapter().capabilities()

        assert caps.text is True


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


class TestLgConnectFailure:
    def test_given_connect_raises_a_transport_error_when_connecting_then_connection_failed_is_raised(
        self,
    ):
        def factory(**kwargs):
            client = FakeWebOsClient(**kwargs)
            client.connect_error = RuntimeError("connection refused")
            return client

        adapter = LgWebOsAdapter(client_factory=factory)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential="k")))

    def test_given_connect_hangs_when_connecting_then_it_fails_within_the_timeout(self):
        def factory(**kwargs):
            client = FakeWebOsClient(**kwargs)
            client.connect_hangs = True
            return client

        adapter = LgWebOsAdapter(client_factory=factory, connect_timeout=0.01)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential="k")))


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

    def test_given_the_button_map_when_read_then_menu_and_channel_keys_map(self):
        assert LG_BUTTONS[Key.MENU] == "MENU"
        assert LG_BUTTONS[Key.CH_UP] == "CHANNELUP"
        assert LG_BUTTONS[Key.CH_DOWN] == "CHANNELDOWN"

    def test_given_the_button_map_when_read_then_media_keys_map_without_play_pause(
        self,
    ):
        assert LG_BUTTONS[Key.PLAY] == "PLAY"
        assert LG_BUTTONS[Key.PAUSE] == "PAUSE"
        assert LG_BUTTONS[Key.REWIND] == "REWIND"
        assert LG_BUTTONS[Key.FAST_FORWARD] == "FASTFORWARD"
        assert LG_BUTTONS[Key.STOP] == "STOP"
        assert Key.PLAY_PAUSE not in LG_BUTTONS

    def test_given_the_button_map_when_read_then_the_digit_keys_map_to_bare_digits(
        self,
    ):
        for digit in range(10):
            assert LG_BUTTONS[Key[f"NUM_{digit}"]] == str(digit)

    def test_given_a_directional_key_when_sent_then_the_lg_button_is_dispatched(self):
        created: list[FakeWebOsClient] = []
        adapter = LgWebOsAdapter(client_factory=_capturing_factory(created))

        async def scenario():
            session = await adapter.connect(_device(credential="k"))
            await session.send_key(Key.LEFT)

        run(scenario())

        assert created[0].sent_buttons == ["LEFT"]


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


class TestLgDiscovery:
    def test_given_ssdp_responders_when_discovering_then_the_upnp_name_is_resolved(
        self,
    ):
        seen_targets: list[str] = []
        seen_locations: list[str] = []

        async def fake_search(target, timeout):
            seen_targets.append(target)
            return [SsdpHit(ip="10.0.0.5", location="http://10.0.0.5:1741/desc.xml")]

        async def fake_resolve_name(location):
            seen_locations.append(location)
            return "Kitchen LG"

        adapter = LgWebOsAdapter(search=fake_search, resolve_name=fake_resolve_name)

        found = run(adapter.discover(timeout=3))

        assert found == [
            DiscoveredDevice(name="Kitchen LG", platform=PLATFORM, ip="10.0.0.5")
        ]
        assert seen_targets == [DISCOVERY_TARGET]
        assert seen_locations == ["http://10.0.0.5:1741/desc.xml"]

    def test_given_the_platform_when_discovering_then_it_is_the_registered_identifier(
        self,
    ):
        async def fake_search(target, timeout):
            return [SsdpHit(ip="10.0.0.5", location="http://10.0.0.5/d")]

        async def fake_resolve_name(location):
            return "Kitchen"

        adapter = LgWebOsAdapter(search=fake_search, resolve_name=fake_resolve_name)

        found = run(adapter.discover(timeout=3))

        assert found[0].platform == "lg-webos"
