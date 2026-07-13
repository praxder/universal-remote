import asyncio

import pytest
from pyatv.const import Protocol

from tests.fakes import FakeAppleTv, FakeAppleTvConfig, FakePairingHandler, FakePyatv
from universal_remote.adapters.appletv import (
    APPLETV_AUDIO_KEYS,
    APPLETV_RC_KEYS,
    PLATFORM,
    AppleTvAdapter,
    AppleTvSession,
    register,
)
from universal_remote.devices.models import Device
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
}


def run(coro):
    return asyncio.run(coro)


def _device(**overrides) -> Device:
    base = dict(name="TV", platform=PLATFORM, ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


def _prompt_returning(value: str, seen: list[str] | None = None):
    async def prompt(message: str) -> str:
        if seen is not None:
            seen.append(message)
        return value

    return prompt


class TestAppleTvRegistration:
    def test_given_the_registry_when_appletv_is_registered_then_the_platform_resolves(
        self,
    ):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM

    def test_given_the_adapter_when_identity_read_then_name_and_platform_are_correct(
        self,
    ):
        adapter = AppleTvAdapter()

        assert adapter.display_name == "Apple TV"
        assert adapter.platform == "apple-tv"


class TestAppleTvCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_core_button_set_is_declared(
        self,
    ):
        caps = AppleTvAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_mute_is_absent(self):
        caps = AppleTvAdapter().capabilities()

        assert Key.MUTE not in caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(self):
        caps = AppleTvAdapter().capabilities()

        assert caps.text is True


class TestAppleTvPairing:
    def test_given_a_prompt_when_pairing_then_pin_flow_runs_and_credential_returns(
        self,
    ):
        fake = FakePyatv(
            config=FakeAppleTvConfig(identifier="atv-77"),
            pairing=FakePairingHandler(credentials="cred-xyz"),
        )
        adapter = AppleTvAdapter(pyatv_api=fake)
        device = _device()
        seen: list[str] = []

        credential = run(adapter.pair(device, prompt=_prompt_returning("1234", seen)))

        assert credential == "cred-xyz"
        assert fake.pairing.began is True
        assert fake.pairing.pin_value == 1234
        assert fake.pairing.finished is True
        assert "PIN" in seen[0]

    def test_given_a_prompt_when_pairing_then_the_device_identifier_is_recorded(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-77"))
        adapter = AppleTvAdapter(pyatv_api=fake)
        device = _device()

        run(adapter.pair(device, prompt=_prompt_returning("1234")))

        assert device.identifier == "atv-77"

    def test_given_pairing_when_it_finishes_then_the_pairing_handler_is_closed(self):
        fake = FakePyatv()
        adapter = AppleTvAdapter(pyatv_api=fake)

        run(adapter.pair(_device(), prompt=_prompt_returning("1234")))

        assert fake.pairing.closed is True

    def test_given_no_prompt_when_pairing_then_pairing_cancelled_is_raised(self):
        adapter = AppleTvAdapter(pyatv_api=FakePyatv())

        with pytest.raises(PairingCancelledError):
            run(adapter.pair(_device(), prompt=None))


class TestAppleTvConnect:
    def test_given_a_stored_device_when_connecting_then_its_ip_is_scanned(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        run(adapter.connect(_device(identifier="atv-1", credential="cred")))

        assert fake.scanned_hosts == [["10.0.0.5"]]

    def test_given_an_identifier_mismatch_when_connecting_then_connection_failed(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-actual"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(identifier="atv-stored", credential="cred")))

    def test_given_the_device_is_not_found_when_connecting_then_connection_failed(self):
        adapter = AppleTvAdapter(pyatv_api=FakePyatv(scan_empty=True))

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(identifier="atv-1", credential="cred")))

    def test_given_a_transport_error_when_connecting_then_connection_failed(self):
        fake = FakePyatv(
            config=FakeAppleTvConfig(identifier="atv-1"),
            connect_error=RuntimeError("refused"),
        )
        adapter = AppleTvAdapter(pyatv_api=fake)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(identifier="atv-1", credential="cred")))

    def test_given_a_matching_identity_when_connecting_then_a_session_is_returned(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        session = run(adapter.connect(_device(identifier="atv-1", credential="cred")))

        assert isinstance(session, AppleTvSession)

    def test_given_a_matching_identity_when_connecting_then_the_credential_is_applied(
        self,
    ):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        run(adapter.connect(_device(identifier="atv-1", credential="cred")))

        assert fake.config.applied_credentials[Protocol.Companion] == "cred"


class TestAppleTvKeyMapping:
    def test_given_the_key_maps_when_read_then_generic_keys_map_to_pyatv_methods(self):
        assert APPLETV_RC_KEYS[Key.UP] == "up"
        assert APPLETV_RC_KEYS[Key.OK] == "select"
        assert APPLETV_RC_KEYS[Key.BACK] == "menu"
        assert APPLETV_RC_KEYS[Key.HOME] == "home"
        assert APPLETV_AUDIO_KEYS[Key.VOL_UP] == "volume_up"
        assert APPLETV_AUDIO_KEYS[Key.VOL_DOWN] == "volume_down"

    def test_given_a_directional_key_when_sent_then_remote_control_is_dispatched(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            await session.send_key(Key.LEFT)

        run(scenario())

        assert fake.atv.remote_control.calls == ["left"]

    def test_given_the_ok_key_when_sent_then_select_is_dispatched(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            await session.send_key(Key.OK)

        run(scenario())

        assert fake.atv.remote_control.calls == ["select"]

    def test_given_a_volume_key_when_sent_then_audio_is_dispatched_not_remote_control(
        self,
    ):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            await session.send_key(Key.VOL_UP)

        run(scenario())

        assert fake.atv.audio.calls == ["volume_up"]
        assert fake.atv.remote_control.calls == []

    def test_given_the_mute_key_when_sent_then_it_is_rejected_as_unsupported(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            with pytest.raises(UnsupportedKeyError):
                await session.send_key(Key.MUTE)

        run(scenario())


class TestAppleTvText:
    def test_given_text_when_sent_then_it_is_dispatched_to_the_device(self):
        fake = FakePyatv(config=FakeAppleTvConfig(identifier="atv-1"))
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            await session.send_text("hello")

        run(scenario())

        assert fake.atv.keyboard.text == ["hello"]

    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        fake = FakePyatv(
            config=FakeAppleTvConfig(identifier="atv-1"),
            atv=FakeAppleTv(reject_text=True),
        )
        adapter = AppleTvAdapter(pyatv_api=fake)

        async def scenario():
            session = await adapter.connect(_device(identifier="atv-1", credential="c"))
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hello")

        run(scenario())
