import asyncio

import pytest

from tests.fakes import FakeFireTvTransport, firetv_port_open
from universal_remote.adapters.firetv import (
    DIGIT_KEYS,
    DISCOVERY_SERVICE,
    FIRETV_ACTIONS,
    FIRETV_MEDIA_ACTIONS,
    PLATFORM,
    FireTvAdapter,
    FireTvSession,
    register,
)
from universal_remote.adapters.firetv_api import (
    CONTROL_PORT,
    DIAL_PORT,
    KEY_PATH,
    KEYBOARD_PATH,
    MEDIA_PATH,
    PIN_DISPLAY_PATH,
    PIN_VERIFY_PATH,
    WAKE_PATH,
    CommandRejectedError,
)
from universal_remote.devices.models import Device
from universal_remote.discovery import DiscoveredDevice, MdnsHit
from universal_remote.errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
    UnsupportedKeyError,
)
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry

_IP = "10.0.0.5"
_CONTROL = f"https://{_IP}:{CONTROL_PORT}"
_WAKE_URL = f"http://{_IP}:{DIAL_PORT}{WAKE_PATH}"

_SUPPORTED_KEYS = {
    Key.UP,
    Key.DOWN,
    Key.LEFT,
    Key.RIGHT,
    Key.OK,
    Key.BACK,
    Key.HOME,
    Key.MENU,
    Key.PLAY,
    Key.PAUSE,
    Key.REWIND,
    Key.FAST_FORWARD,
    *(Key[f"NUM_{digit}"] for digit in range(10)),
}

# Keys this transport cannot send, so the on-screen remote disables them.
_DROPPED_KEYS = {
    Key.VOL_UP,
    Key.VOL_DOWN,
    Key.MUTE,
    Key.PLAY_PAUSE,
    Key.STOP,
    Key.CH_UP,
    Key.CH_DOWN,
}


def run(coro):
    return asyncio.run(coro)


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip=_IP, credential="AB1CD2E")
    base.update(overrides)
    return Device(**base)


def _adapter(transport: FakeFireTvTransport, **overrides) -> FireTvAdapter:
    options = dict(
        transport_factory=lambda: transport,
        port_open=firetv_port_open,
        wake_timeout=0.0,
    )
    options.update(overrides)
    return FireTvAdapter(**options)


async def _prompt(_message: str) -> str:
    return "1234"


def _urls(transport: FakeFireTvTransport) -> list[str]:
    return [request.url for request in transport.requests]


def _sent(transport: FakeFireTvTransport) -> list[dict | None]:
    return [request.json for request in transport.requests]


async def _session(transport: FakeFireTvTransport) -> FireTvSession:
    """A connected session, with the connect handshake's requests discarded."""
    session = await _adapter(transport).connect(_device())
    transport.requests.clear()
    return session


class TestFireTvRegistration:
    def test_given_the_registry_when_firetv_is_registered_then_the_platform_resolves(
        self,
    ):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM

    def test_given_the_adapter_when_identity_read_then_name_and_platform_are_correct(
        self,
    ):
        adapter = FireTvAdapter()

        assert adapter.display_name == "Fire TV"
        assert adapter.platform == "firetv"

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_dial_port(
        self,
    ):
        # 8009 answers on a stock device, before the remote service is ever woken;
        # the control port (8080) is closed until then, so an idle device would
        # otherwise read unreachable.
        assert FireTvAdapter().reachability_port == 8009


class TestFireTvPairingRequirement:
    def test_given_the_adapter_when_asked_then_it_requires_pairing(self):
        # Unset attribute defaults to requiring pairing, like Apple TV / Android TV.
        assert getattr(FireTvAdapter(), "requires_pairing", True) is True


class TestFireTvCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_sendable_keys_are_declared(
        self,
    ):
        caps = FireTvAdapter().capabilities()

        assert _SUPPORTED_KEYS == caps.keys

    @pytest.mark.parametrize("key", sorted(_DROPPED_KEYS, key=lambda key: key.name))
    def test_given_the_adapter_when_capabilities_read_then_unsendable_keys_are_absent(
        self, key
    ):
        # Volume is reported uncontrollable by the device, play/pause and stop have no
        # action, and a streamer has no tuner for the channel keys.
        assert key not in FireTvAdapter().capabilities().keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(self):
        assert FireTvAdapter().capabilities().text is True


class TestFireTvKeyMap:
    def test_given_the_key_map_when_read_then_the_nav_keys_map_to_rest_actions(self):
        assert FIRETV_ACTIONS[Key.UP] == "dpad_up"
        assert FIRETV_ACTIONS[Key.DOWN] == "dpad_down"
        assert FIRETV_ACTIONS[Key.LEFT] == "dpad_left"
        assert FIRETV_ACTIONS[Key.RIGHT] == "dpad_right"
        assert FIRETV_ACTIONS[Key.OK] == "select"
        assert FIRETV_ACTIONS[Key.BACK] == "back"
        assert FIRETV_ACTIONS[Key.HOME] == "home"
        assert FIRETV_ACTIONS[Key.MENU] == "menu"

    def test_given_the_key_map_when_read_then_scrubbing_rides_the_player_dpad(self):
        # The API offers no transport scrub action; in a player the d-pad skips ±10s.
        assert FIRETV_ACTIONS[Key.FAST_FORWARD] == "dpad_right"
        assert FIRETV_ACTIONS[Key.REWIND] == "dpad_left"

    def test_given_the_media_map_when_read_then_play_and_pause_have_their_own_actions(
        self,
    ):
        assert FIRETV_MEDIA_ACTIONS == {Key.PLAY: "play", Key.PAUSE: "pause"}

    def test_given_the_digit_map_when_read_then_each_digit_maps_to_its_character(self):
        assert [DIGIT_KEYS[Key[f"NUM_{digit}"]] for digit in range(10)] == [
            str(digit) for digit in range(10)
        ]


class TestFireTvPairing:
    def test_given_a_device_when_pairing_then_the_service_is_woken_first(self):
        transport = FakeFireTvTransport()

        run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert _urls(transport)[0] == _WAKE_URL

    def test_given_a_device_when_pairing_then_a_pin_is_displayed_then_verified(self):
        transport = FakeFireTvTransport()

        run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert _urls(transport)[1:] == [
            f"{_CONTROL}{PIN_DISPLAY_PATH}",
            f"{_CONTROL}{PIN_VERIFY_PATH}",
        ]

    def test_given_a_prompted_pin_when_verifying_then_it_is_sent_to_the_device(self):
        transport = FakeFireTvTransport()

        run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert transport.requests[-1].json == {"pin": "1234"}

    def test_given_an_accepted_pin_when_pairing_then_the_client_token_is_returned(self):
        transport = FakeFireTvTransport(token="XY7ZQ12")

        credential = run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert credential == "XY7ZQ12"

    def test_given_pairing_when_it_completes_then_the_transport_is_closed(self):
        transport = FakeFireTvTransport()

        run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert transport.closed is True

    def test_given_a_rejected_pin_when_pairing_then_pairing_is_reported_as_failed(self):
        transport = FakeFireTvTransport()
        transport.reject = PIN_VERIFY_PATH

        with pytest.raises(PairingCancelledError):
            run(_adapter(transport).pair(_device(), prompt=_prompt))

    def test_given_a_rejected_pin_when_pairing_then_the_transport_is_still_closed(self):
        transport = FakeFireTvTransport()
        transport.reject = PIN_VERIFY_PATH

        with pytest.raises(PairingCancelledError):
            run(_adapter(transport).pair(_device(), prompt=_prompt))

        assert transport.closed is True

    def test_given_no_prompt_when_pairing_then_pairing_is_reported_as_failed(self):
        # A PIN adapter cannot pair without a way to ask for the PIN, and must not
        # invent a value of its own.
        transport = FakeFireTvTransport()

        with pytest.raises(PairingCancelledError):
            run(_adapter(transport).pair(_device()))

        assert transport.requests == []


class TestFireTvConnect:
    def test_given_a_saved_device_when_connecting_then_the_service_is_woken_first(self):
        transport = FakeFireTvTransport()

        run(_adapter(transport).connect(_device()))

        assert _urls(transport)[0] == _WAKE_URL

    def test_given_a_saved_device_when_connecting_then_the_stored_token_is_verified(
        self,
    ):
        transport = FakeFireTvTransport()

        run(_adapter(transport).connect(_device(credential="XY7ZQ12")))

        assert _urls(transport)[1] == f"{_CONTROL}{KEY_PATH}"
        assert transport.requests[1].headers["X-Client-Token"] == "XY7ZQ12"

    def test_given_a_reachable_device_when_connecting_then_a_session_is_returned(self):
        session = run(_adapter(FakeFireTvTransport()).connect(_device()))

        assert isinstance(session, FireTvSession)

    def test_given_a_rejected_credential_when_connecting_then_connection_failed(self):
        transport = FakeFireTvTransport()
        transport.reject = KEY_PATH

        with pytest.raises(ConnectionFailedError):
            run(_adapter(transport).connect(_device()))

    def test_given_an_unreachable_device_when_connecting_then_connection_failed(self):
        async def never_open(_ip: str, _port: int, _timeout: float) -> bool:
            return False

        adapter = _adapter(FakeFireTvTransport(), port_open=never_open)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

    def test_given_a_failed_connect_when_it_gives_up_then_the_transport_is_closed(self):
        transport = FakeFireTvTransport()
        transport.reject = KEY_PATH

        with pytest.raises(ConnectionFailedError):
            run(_adapter(transport).connect(_device()))

        assert transport.closed is True

    def test_given_a_session_when_closed_then_the_owned_transport_is_closed(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _adapter(transport).connect(_device())
            await session.close()

        run(scenario())

        assert transport.closed is True


class TestFireTvKeyDispatch:
    def test_given_a_nav_key_when_sent_then_its_action_is_posted_to_the_key_route(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.OK)

        run(scenario())

        assert _urls(transport) == [f"{_CONTROL}{KEY_PATH}?action=select"]

    def test_given_a_nav_key_when_sent_then_the_request_body_is_empty(self):
        # A body of any shape makes the device answer 500 even when it dispatched the
        # key, which destroys error reporting — `keyActionType` included.
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.OK)

        run(scenario())

        assert _sent(transport) == [None]

    def test_given_a_transport_key_when_sent_then_it_is_posted_to_the_media_route(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.PLAY)
            await session.send_key(Key.PAUSE)

        run(scenario())

        assert _urls(transport) == [
            f"{_CONTROL}{MEDIA_PATH}?action=play",
            f"{_CONTROL}{MEDIA_PATH}?action=pause",
        ]

    def test_given_a_scrub_key_when_sent_then_the_player_dpad_action_is_posted(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.FAST_FORWARD)
            await session.send_key(Key.REWIND)

        run(scenario())

        assert _urls(transport) == [
            f"{_CONTROL}{KEY_PATH}?action=dpad_right",
            f"{_CONTROL}{KEY_PATH}?action=dpad_left",
        ]

    def test_given_the_device_rejects_a_key_when_sent_then_the_failure_surfaces(self):
        # A 400 means the device refused the action; reporting success would be a lie.
        transport = FakeFireTvTransport()
        transport.reject = "action=home"

        async def scenario():
            session = await _session(transport)
            with pytest.raises(CommandRejectedError):
                await session.send_key(Key.HOME)

        run(scenario())

    def test_given_an_undeclared_key_when_sent_then_it_is_rejected_as_unsupported(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            with pytest.raises(UnsupportedKeyError):
                await session.send_key(Key.MUTE)

        run(scenario())

        assert transport.requests == []


class TestFireTvSessionRecovery:
    def test_given_the_service_stopped_when_a_key_is_sent_then_it_re_wakes_and_retries(
        self,
    ):
        # The idle remote service can stop, so one failed request is transient.
        transport = FakeFireTvTransport()
        transport.fail_once = "action=home"

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.HOME)

        run(scenario())

        assert _urls(transport) == [
            f"{_CONTROL}{KEY_PATH}?action=home",
            _WAKE_URL,
            f"{_CONTROL}{KEY_PATH}?action=home",
        ]

    def test_given_the_service_stays_gone_when_a_key_is_sent_then_the_error_surfaces(
        self,
    ):
        from universal_remote.adapters.firetv_api import ServiceUnavailableError

        transport = FakeFireTvTransport()
        transport.fail = "action=home"

        async def scenario():
            session = await _session(transport)
            with pytest.raises(ServiceUnavailableError):
                await session.send_key(Key.HOME)

        run(scenario())

    def test_given_a_rejected_key_when_sent_then_it_is_not_retried(self):
        # The device answered, so re-waking would achieve nothing.
        transport = FakeFireTvTransport()
        transport.reject = "action=home"

        async def scenario():
            session = await _session(transport)
            with pytest.raises(CommandRejectedError):
                await session.send_key(Key.HOME)

        run(scenario())

        assert _urls(transport) == [f"{_CONTROL}{KEY_PATH}?action=home"]


class TestFireTvText:
    def test_given_text_when_sent_then_the_focused_field_is_read_before_writing(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_text("hi")

        run(scenario())

        assert [(request.method, request.url) for request in transport.requests] == [
            ("GET", f"{_CONTROL}{KEYBOARD_PATH}"),
            ("POST", f"{_CONTROL}{KEYBOARD_PATH}"),
        ]

    def test_given_a_focused_field_when_text_is_sent_then_it_is_set_unescaped(self):
        # The route takes the characters as they are — no shell escaping, unlike the
        # ADB path this replaced.
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_text("a b&c 50%s")

        run(scenario())

        assert transport.requests[-1].json == {"text": "a b&c 50%s"}

    def test_given_non_ascii_text_when_sent_then_it_is_transmitted_unchanged(self):
        transport = FakeFireTvTransport()

        async def scenario():
            session = await _session(transport)
            await session.send_text("café ☕")

        run(scenario())

        assert transport.requests[-1].json == {"text": "café ☕"}

    def test_given_no_focused_field_when_text_is_sent_then_text_unsupported_is_reported(
        self,
    ):
        transport = FakeFireTvTransport(keyboard={"state": "hidden"})

        async def scenario():
            session = await _session(transport)
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hi")

        run(scenario())

        # A write with nothing focused returns a hollow 200 and types nothing, so it
        # must not be attempted at all.
        assert [request.method for request in transport.requests] == ["GET"]


class TestFireTvDigits:
    def test_given_a_digit_key_when_sent_then_the_field_is_read_and_written_back(self):
        # The keyboard route replaces the field rather than appending to it, so a
        # digit is the current contents plus that digit.
        transport = FakeFireTvTransport(keyboard={"state": "text", "text": "5"})

        async def scenario():
            session = await _session(transport)
            await session.send_key(Key.NUM_3)

        run(scenario())

        assert _urls(transport) == [
            f"{_CONTROL}{KEYBOARD_PATH}",
            f"{_CONTROL}{KEYBOARD_PATH}",
        ]
        assert transport.requests[-1].json == {"text": "53"}

    def test_given_no_focused_field_when_a_digit_is_sent_then_text_unsupported(self):
        # Digits have no keycode path, so they are only sendable into a text field.
        transport = FakeFireTvTransport(keyboard={"state": "hidden"})

        async def scenario():
            session = await _session(transport)
            with pytest.raises(TextUnsupportedError):
                await session.send_key(Key.NUM_3)

        run(scenario())

        assert [request.method for request in transport.requests] == ["GET"]


class TestFireTvDiscovery:
    def test_given_mdns_hits_when_discovering_then_the_txt_name_is_used(self):
        # The Amazon service's instance name is a device code; the friendly name
        # lives in the TXT "n" key, so discovery must read it from there.
        seen: list[str] = []

        async def fake_browse(service_type, timeout):
            seen.append(service_type)
            return [
                MdnsHit(
                    name="AFTMM",
                    ip=_IP,
                    properties={"n": "Living Room Fire TV"},
                )
            ]

        adapter = FireTvAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found == [
            DiscoveredDevice(name="Living Room Fire TV", platform=PLATFORM, ip=_IP)
        ]
        assert seen == [DISCOVERY_SERVICE]

    def test_given_no_txt_name_when_discovering_then_the_name_falls_back_to_the_ip(
        self,
    ):
        async def fake_browse(service_type, timeout):
            return [MdnsHit(name="AFTMM", ip=_IP, properties={})]

        adapter = FireTvAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found[0].name == _IP
