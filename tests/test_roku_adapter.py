import asyncio

import pytest
from rokuecp import RokuConnectionError
from rokuecp.const import VALID_REMOTE_KEYS

from tests.fakes import FakeClientSession, FakeRoku
from universal_remote.adapters.roku import (
    DISCOVERY_TARGET,
    PLATFORM,
    ROKU_KEYS,
    RokuAdapter,
    RokuSession,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.discovery import DiscoveredDevice, SsdpHit
from universal_remote.errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
    UnsupportedKeyError,
)
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
    Key.CH_UP,
    Key.CH_DOWN,
    Key.PLAY_PAUSE,
    Key.REWIND,
    Key.FAST_FORWARD,
}


def run(coro):
    return asyncio.run(coro)


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


def _capturing_adapter(
    clients: list[FakeRoku],
    sessions: list[FakeClientSession],
    *,
    update_error: Exception | None = None,
    reject_text: bool = False,
) -> RokuAdapter:
    def session_factory() -> FakeClientSession:
        session = FakeClientSession()
        sessions.append(session)
        return session

    def client_factory(**kwargs) -> FakeRoku:
        client = FakeRoku(**kwargs)
        client.update_error = update_error
        client.reject_text = reject_text
        clients.append(client)
        return client

    return RokuAdapter(client_factory=client_factory, session_factory=session_factory)


class TestRokuRegistration:
    def test_given_the_registry_when_roku_is_registered_then_the_platform_resolves(
        self,
    ):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM

    def test_given_the_adapter_when_identity_read_then_name_and_platform_are_correct(
        self,
    ):
        adapter = RokuAdapter()

        assert adapter.display_name == "Roku"
        assert adapter.platform == "roku"

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_ecp_port(
        self,
    ):
        assert RokuAdapter().reachability_port == 8060


class TestRokuNoPairing:
    def test_given_the_adapter_when_asked_then_it_declares_no_pairing(self):
        assert RokuAdapter().requires_pairing is False

    def test_given_the_adapter_when_pairing_attempted_then_it_reports_unavailable(self):
        adapter = RokuAdapter()

        with pytest.raises(PairingCancelledError):
            run(adapter.pair(_device()))


class TestRokuCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_core_button_set_is_declared(
        self,
    ):
        caps = RokuAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_discrete_transport_is_absent(
        self,
    ):
        # ECP has only a single Play/Pause toggle; no discrete play/pause/stop.
        caps = RokuAdapter().capabilities()

        assert Key.PLAY not in caps.keys
        assert Key.PAUSE not in caps.keys
        assert Key.STOP not in caps.keys

    def test_given_the_adapter_when_capabilities_read_then_number_pad_is_absent(self):
        # Roku remotes have no number pad.
        caps = RokuAdapter().capabilities()

        assert not any(Key[f"NUM_{digit}"] in caps.keys for digit in range(10))

    def test_given_the_adapter_when_capabilities_read_then_menu_is_absent(self):
        # ECP has no menu equivalent.
        caps = RokuAdapter().capabilities()

        assert Key.MENU not in caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(self):
        caps = RokuAdapter().capabilities()

        assert caps.text is True


class TestRokuKeyMapping:
    def test_given_the_key_map_when_read_then_generic_keys_map_to_rokuecp_tokens(self):
        assert ROKU_KEYS[Key.UP] == "up"
        assert ROKU_KEYS[Key.OK] == "select"
        assert ROKU_KEYS[Key.BACK] == "back"
        assert ROKU_KEYS[Key.HOME] == "home"
        assert ROKU_KEYS[Key.VOL_UP] == "volume_up"
        assert ROKU_KEYS[Key.MUTE] == "volume_mute"

    def test_given_the_key_map_when_read_then_channel_and_transport_keys_map(self):
        assert ROKU_KEYS[Key.CH_UP] == "channel_up"
        assert ROKU_KEYS[Key.CH_DOWN] == "channel_down"
        assert ROKU_KEYS[Key.REWIND] == "reverse"
        assert ROKU_KEYS[Key.FAST_FORWARD] == "forward"

    def test_given_the_key_map_when_read_then_play_pause_maps_to_the_single_toggle(
        self,
    ):
        assert ROKU_KEYS[Key.PLAY_PAUSE] == "play"

    def test_given_the_key_map_when_read_then_every_token_is_one_rokuecp_accepts(self):
        # remote() lower-cases and looks up VALID_REMOTE_KEYS; a token absent there
        # raises RokuError on hardware while the fake records it happily. Pin the
        # whole map to the library's primary-source vocabulary.
        assert all(token in VALID_REMOTE_KEYS for token in ROKU_KEYS.values())

    def test_given_a_supported_key_when_sent_then_the_rokuecp_token_is_dispatched(self):
        clients: list[FakeRoku] = []
        adapter = _capturing_adapter(clients, [])

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_key(Key.LEFT)

        run(scenario())

        assert clients[0].sent_keys == ["left"]

    def test_given_the_play_pause_key_when_sent_then_the_single_toggle_is_dispatched(
        self,
    ):
        clients: list[FakeRoku] = []
        adapter = _capturing_adapter(clients, [])

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_key(Key.PLAY_PAUSE)

        run(scenario())

        assert clients[0].sent_keys == ["play"]

    def test_given_an_undeclared_key_when_sent_then_it_is_rejected_as_unsupported(self):
        adapter = _capturing_adapter([], [])

        async def scenario():
            session = await adapter.connect(_device())
            with pytest.raises(UnsupportedKeyError):
                await session.send_key(Key.STOP)

        run(scenario())


class TestRokuConnect:
    def test_given_a_device_when_connecting_then_a_client_is_built_for_its_ip(self):
        clients: list[FakeRoku] = []
        adapter = _capturing_adapter(clients, [])

        run(adapter.connect(_device(ip="10.0.0.9")))

        assert clients[0].host == "10.0.0.9"

    def test_given_a_reachable_device_when_connecting_then_a_session_is_returned(self):
        clients: list[FakeRoku] = []
        adapter = _capturing_adapter(clients, [])

        session = run(adapter.connect(_device()))

        assert isinstance(session, RokuSession)
        assert clients[0].updated is True

    def test_given_the_client_when_built_then_it_owns_the_injected_session(self):
        clients: list[FakeRoku] = []
        sessions: list[FakeClientSession] = []
        adapter = _capturing_adapter(clients, sessions)

        run(adapter.connect(_device()))

        assert clients[0].session is sessions[0]

    def test_given_the_reachability_check_fails_when_connecting_then_connection_failed(
        self,
    ):
        adapter = _capturing_adapter(
            [], [], update_error=RokuConnectionError("refused")
        )

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

    def test_given_the_reachability_check_fails_when_connecting_then_the_session_is_closed(
        self,
    ):
        sessions: list[FakeClientSession] = []
        adapter = _capturing_adapter(
            [], sessions, update_error=RokuConnectionError("refused")
        )

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

        assert sessions[0].closed is True

    def test_given_a_session_when_closed_then_the_owned_aiohttp_session_is_closed(self):
        sessions: list[FakeClientSession] = []
        adapter = _capturing_adapter([], sessions)

        async def scenario():
            session = await adapter.connect(_device())
            await session.close()

        run(scenario())

        assert sessions[0].closed is True


class TestRokuText:
    def test_given_text_when_sent_then_it_is_dispatched_as_literal_characters(self):
        clients: list[FakeRoku] = []
        adapter = _capturing_adapter(clients, [])

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_text("hi")

        run(scenario())

        assert clients[0].sent_text == ["hi"]

    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        adapter = _capturing_adapter([], [], reject_text=True)

        async def scenario():
            session = await adapter.connect(_device())
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hi")

        run(scenario())


class TestRokuDiscovery:
    def test_given_ssdp_responders_when_discovering_then_the_ecp_name_is_resolved(self):
        seen_targets: list[str] = []
        seen_ips: list[str] = []

        async def fake_search(target, timeout):
            seen_targets.append(target)
            return [SsdpHit(ip="10.0.0.5", location="http://10.0.0.5:8060/")]

        async def fake_resolve_name(ip):
            seen_ips.append(ip)
            return "Living Room Roku"

        adapter = RokuAdapter(search=fake_search, resolve_name=fake_resolve_name)

        found = run(adapter.discover(timeout=3))

        assert found == [
            DiscoveredDevice(name="Living Room Roku", platform=PLATFORM, ip="10.0.0.5")
        ]
        assert seen_targets == [DISCOVERY_TARGET]
        assert seen_ips == ["10.0.0.5"]

    def test_given_name_resolution_fails_when_discovering_then_the_name_is_the_ip(self):
        async def fake_search(target, timeout):
            return [SsdpHit(ip="10.0.0.5", location="http://10.0.0.5:8060/")]

        async def failing_resolve_name(ip):
            raise OSError("device-info unreachable")

        adapter = RokuAdapter(search=fake_search, resolve_name=failing_resolve_name)

        found = run(adapter.discover(timeout=3))

        assert found[0].name == "10.0.0.5"
