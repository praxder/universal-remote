import asyncio

import pytest
from adb_shell.exceptions import TcpTimeoutException

from tests.fakes import FAKE_GETEVENT_LP, FakeAdbDevice, FakeAdbSigner, fake_keygen
from universal_remote.adapters.firetv import (
    ADB_PORT,
    DISCOVERY_SERVICE,
    EVDEV_KEYS,
    FIRETV_KEYS,
    PLATFORM,
    FireTvAdapter,
    FireTvSession,
    evdev_press,
    find_key_node,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.discovery import DiscoveredDevice, MdnsHit
from universal_remote.errors import (
    ConnectionFailedError,
    TextUnsupportedError,
    UnsupportedKeyError,
)
from universal_remote.keys import Key
from universal_remote.registry import AdapterRegistry

_SUPPORTED_KEYS = {
    Key.UP,
    Key.DOWN,
    Key.LEFT,
    Key.RIGHT,
    Key.OK,
    Key.BACK,
    Key.HOME,
    Key.MENU,
    Key.VOL_UP,
    Key.VOL_DOWN,
    Key.MUTE,
    Key.PLAY,
    Key.PAUSE,
    Key.PLAY_PAUSE,
    Key.STOP,
    Key.REWIND,
    Key.FAST_FORWARD,
    *(Key[f"NUM_{digit}"] for digit in range(10)),
}


def run(coro):
    return asyncio.run(coro)


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip="10.0.0.5", credential="stored-pem")
    base.update(overrides)
    return Device(**base)


def _capturing_adapter(
    devices: list[FakeAdbDevice],
    *,
    connect_error: Exception | None = None,
    reject_text: bool = False,
    getevent_lp: str = FAKE_GETEVENT_LP,
) -> FireTvAdapter:
    def device_factory(host: str, port: int = ADB_PORT, **_kwargs) -> FakeAdbDevice:
        device = FakeAdbDevice(host=host, port=port, getevent_lp=getevent_lp)
        device.connect_error = connect_error
        device.reject_text = reject_text
        devices.append(device)
        return device

    return FireTvAdapter(
        device_factory=device_factory,
        keygen=fake_keygen,
        signer_factory=FakeAdbSigner,
    )


_NODE = "/dev/input/event4"  # node the fake getevent listing advertises
_NO_DPAD_LISTING = (
    'add device 1: /dev/input/event3\n  name: "mouse"\n    KEY (0001): BTN_MOUSE\n'
)


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

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_adb_port(
        self,
    ):
        assert FireTvAdapter().reachability_port == 5555


class TestFireTvPairingRequirement:
    def test_given_the_adapter_when_asked_then_it_requires_pairing(self):
        # Unset attribute defaults to requiring pairing, like Samsung/LG.
        assert getattr(FireTvAdapter(), "requires_pairing", True) is True


class TestFireTvCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_full_button_set_is_declared(
        self,
    ):
        caps = FireTvAdapter().capabilities()

        assert _SUPPORTED_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_channel_keys_are_absent(
        self,
    ):
        # A Fire TV streamer has no tuner, so channel up/down render disabled.
        caps = FireTvAdapter().capabilities()

        assert Key.CH_UP not in caps.keys
        assert Key.CH_DOWN not in caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(self):
        caps = FireTvAdapter().capabilities()

        assert caps.text is True


class TestFireTvKeyMap:
    def test_given_the_key_map_when_read_then_generic_keys_map_to_adb_key_events(self):
        assert FIRETV_KEYS[Key.OK] == 23
        assert FIRETV_KEYS[Key.BACK] == 4
        assert FIRETV_KEYS[Key.HOME] == 3
        assert FIRETV_KEYS[Key.MENU] == 82
        assert FIRETV_KEYS[Key.MUTE] == 164

    def test_given_the_key_map_when_read_then_transport_keys_map(self):
        assert FIRETV_KEYS[Key.PLAY] == 126
        assert FIRETV_KEYS[Key.PAUSE] == 127
        assert FIRETV_KEYS[Key.PLAY_PAUSE] == 85
        assert FIRETV_KEYS[Key.STOP] == 86
        assert FIRETV_KEYS[Key.REWIND] == 89
        assert FIRETV_KEYS[Key.FAST_FORWARD] == 90

    def test_given_the_key_map_when_read_then_the_number_pad_maps_to_keycode_0_through_9(
        self,
    ):
        assert [FIRETV_KEYS[Key[f"NUM_{digit}"]] for digit in range(10)] == list(
            range(7, 17)
        )


class TestFireTvPairing:
    def test_given_a_device_when_pairing_then_the_private_key_pem_is_returned(self):
        adapter = _capturing_adapter([])

        credential = run(adapter.pair(_device()))

        assert credential == "fake-private-pem"

    def test_given_pairing_when_it_connects_then_the_signer_carries_the_public_key(
        self,
    ):
        # A fresh keypair must send its public key so the TV's popup can whitelist it.
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        run(adapter.pair(_device(ip="10.0.0.7")))

        assert devices[0].host == "10.0.0.7"
        assert devices[0].port == ADB_PORT
        signer = devices[0].connects[0]["rsa_keys"][0]
        assert signer.pub == "fake-public-key"

    def test_given_pairing_when_it_completes_then_the_prompt_is_never_used(self):
        adapter = _capturing_adapter([])
        prompts: list[str] = []

        async def prompt(message: str) -> str:
            prompts.append(message)
            return "unused"

        run(adapter.pair(_device(), prompt=prompt))

        assert prompts == []

    def test_given_pairing_when_it_completes_then_the_pairing_connection_is_closed(
        self,
    ):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        run(adapter.pair(_device()))

        assert devices[0].closed is True


class TestFireTvConnect:
    def test_given_a_device_when_connecting_then_a_device_is_built_for_its_ip_and_port(
        self,
    ):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        run(adapter.connect(_device(ip="10.0.0.9")))

        assert devices[0].host == "10.0.0.9"
        assert devices[0].port == ADB_PORT

    def test_given_a_reachable_device_when_connecting_then_a_session_is_returned(self):
        adapter = _capturing_adapter([])

        session = run(adapter.connect(_device()))

        assert isinstance(session, FireTvSession)

    def test_given_connecting_when_the_signer_is_built_then_it_replays_the_stored_pem(
        self,
    ):
        # Replay uses the private key only; the public key is already whitelisted.
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        run(adapter.connect(_device(credential="stored-pem")))

        signer = devices[0].connects[0]["rsa_keys"][0]
        assert signer.priv == "stored-pem"
        assert signer.pub is None

    def test_given_the_handshake_fails_when_connecting_then_connection_failed(self):
        adapter = _capturing_adapter([], connect_error=TcpTimeoutException("timeout"))

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

    def test_given_the_handshake_fails_when_connecting_then_the_device_is_closed(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(
            devices, connect_error=TcpTimeoutException("timeout")
        )

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

        assert devices[0].closed is True

    def test_given_a_malformed_credential_when_connecting_then_connection_failed(self):
        # A missing or garbage stored PEM makes the real signer reject it; that must
        # surface as a failed connection, not a raw parse error.
        def signer_factory(**_kwargs):
            raise ValueError("could not load private key")

        adapter = FireTvAdapter(
            device_factory=lambda host, port=ADB_PORT, **_kw: FakeAdbDevice(host, port),
            keygen=fake_keygen,
            signer_factory=signer_factory,
        )

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device()))

    def test_given_a_session_when_closed_then_the_owned_adb_connection_is_closed(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.close()

        run(scenario())

        assert devices[0].closed is True


class TestFireTvNodeDiscovery:
    def test_given_a_listing_with_a_dpad_node_when_parsed_then_that_node_is_found(self):
        assert find_key_node(FAKE_GETEVENT_LP) == _NODE

    def test_given_a_listing_without_a_dpad_node_when_parsed_then_none_is_found(self):
        assert find_key_node(_NO_DPAD_LISTING) is None

    def test_given_an_empty_listing_when_parsed_then_none_is_found(self):
        assert find_key_node("") is None


class TestFireTvKeyDispatch:
    def test_given_a_fast_key_when_sent_then_a_sendevent_press_is_dispatched(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_key(Key.OK)

        run(scenario())

        assert devices[0].commands == [evdev_press(_NODE, EVDEV_KEYS[Key.OK])]

    @pytest.mark.parametrize(
        ("key", "code"),
        [
            (Key.HOME, 172),
            (Key.MENU, 139),
            (Key.PLAY, 207),
            (Key.PAUSE, 201),
            (Key.PLAY_PAUSE, 164),
            (Key.STOP, 128),
            (Key.REWIND, 168),
            (Key.FAST_FORWARD, 208),
        ],
    )
    def test_given_home_menu_or_media_key_when_sent_then_a_sendevent_press_is_dispatched(
        self, key, code
    ):
        # These once fell back to `input keyevent` (~1.1s); they now ride the sendevent
        # fast path via scancodes confirmed against the device's Generic.kl.
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_key(key)

        run(scenario())

        assert EVDEV_KEYS[key] == code
        assert devices[0].commands == [evdev_press(_NODE, code)]

    def test_given_every_supported_key_when_sent_then_each_uses_its_expected_path(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            for key in _SUPPORTED_KEYS:
                await session.send_key(key)

        run(scenario())

        expected = {
            evdev_press(_NODE, EVDEV_KEYS[key])
            if key in EVDEV_KEYS
            else f"input keyevent {FIRETV_KEYS[key]}"
            for key in _SUPPORTED_KEYS
        }
        assert set(devices[0].commands) == expected

    def test_given_no_input_node_when_a_fast_key_is_sent_then_it_falls_back(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices, getevent_lp=_NO_DPAD_LISTING)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_key(Key.OK)

        run(scenario())

        assert devices[0].commands == [f"input keyevent {FIRETV_KEYS[Key.OK]}"]

    def test_given_an_undeclared_key_when_sent_then_it_is_rejected_as_unsupported(self):
        adapter = _capturing_adapter([])

        async def scenario():
            session = await adapter.connect(_device())
            with pytest.raises(UnsupportedKeyError):
                await session.send_key(Key.CH_UP)

        run(scenario())


class TestFireTvText:
    def test_given_text_when_sent_then_it_is_dispatched_as_an_input_text_command(self):
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_text("hi")

        run(scenario())

        assert devices[0].commands == ["input text hi"]

    def test_given_text_with_shell_specials_when_sent_then_it_is_escaped(self):
        # The text is interpolated into a device-side shell line, so spaces and
        # shell metacharacters must be escaped or "AT&T" is mangled/dropped.
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_text("a b&c")

        run(scenario())

        assert devices[0].commands == ["input text a%sb\\&c"]

    def test_given_text_with_a_literal_percent_s_when_sent_then_it_survives(self):
        # Android's `input text` collapses "%s" to a space; a literal "%s" must be
        # split across two calls so it lands on the device instead of a space.
        devices: list[FakeAdbDevice] = []
        adapter = _capturing_adapter(devices)

        async def scenario():
            session = await adapter.connect(_device())
            await session.send_text("50%s")

        run(scenario())

        assert devices[0].commands == ["input text 50\\%; input text s"]

    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        adapter = _capturing_adapter([], reject_text=True)

        async def scenario():
            session = await adapter.connect(_device())
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hi")

        run(scenario())


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
                    ip="10.0.0.5",
                    properties={"n": "Living Room Fire TV"},
                )
            ]

        adapter = FireTvAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found == [
            DiscoveredDevice(
                name="Living Room Fire TV", platform=PLATFORM, ip="10.0.0.5"
            )
        ]
        assert seen == [DISCOVERY_SERVICE]

    def test_given_no_txt_name_when_discovering_then_the_name_falls_back_to_the_ip(
        self,
    ):
        async def fake_browse(service_type, timeout):
            return [MdnsHit(name="AFTMM", ip="10.0.0.5", properties={})]

        adapter = FireTvAdapter(browse=fake_browse)

        found = run(adapter.discover(timeout=3))

        assert found[0].name == "10.0.0.5"
