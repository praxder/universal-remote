import asyncio
import os

import pytest
from androidtvremote2 import CannotConnect, InvalidAuth

from tests.fakes import FakeAndroidTvRemoteFactory
from universal_remote.adapters.androidtv import (
    ANDROIDTV_KEYS,
    PLATFORM,
    AndroidTvAdapter,
    AndroidTvSession,
    register,
)
from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore
from universal_remote.errors import (
    ConnectionFailedError,
    PairingCancelledError,
    TextUnsupportedError,
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
    Key.MENU,
    Key.VOL_UP,
    Key.VOL_DOWN,
    Key.MUTE,
    Key.CH_UP,
    Key.CH_DOWN,
    Key.PLAY,
    Key.PAUSE,
    Key.PLAY_PAUSE,
    Key.STOP,
    Key.REWIND,
    Key.FAST_FORWARD,
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


def _paired_credential() -> str:
    """A credential as pair() produces it, for driving connect tests directly."""
    factory = FakeAndroidTvRemoteFactory()
    adapter = AndroidTvAdapter(remote_factory=factory)
    return run(adapter.pair(_device(), prompt=_prompt_returning("1a2b3c")))


class TestAndroidTvRegistration:
    def test_given_the_registry_when_androidtv_is_registered_then_the_platform_resolves(
        self,
    ):
        registry = AdapterRegistry()

        register(registry)

        assert registry.resolve(PLATFORM).platform == PLATFORM

    def test_given_the_adapter_when_identity_read_then_name_and_platform_are_correct(
        self,
    ):
        adapter = AndroidTvAdapter()

        assert adapter.display_name == "Android TV"
        assert adapter.platform == "androidtv"

    def test_given_the_adapter_when_reachability_port_read_then_it_is_the_remote_port(
        self,
    ):
        assert AndroidTvAdapter().reachability_port == 6466


class TestAndroidTvCapabilities:
    def test_given_the_adapter_when_capabilities_read_then_the_button_set_is_declared(
        self,
    ):
        caps = AndroidTvAdapter().capabilities()

        assert _CORE_KEYS <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_the_digits_are_declared(
        self,
    ):
        caps = AndroidTvAdapter().capabilities()

        assert {Key[f"NUM_{digit}"] for digit in range(10)} <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_channel_keys_are_declared(
        self,
    ):
        caps = AndroidTvAdapter().capabilities()

        assert {Key.CH_UP, Key.CH_DOWN} <= caps.keys

    def test_given_the_adapter_when_capabilities_read_then_text_is_declared(self):
        caps = AndroidTvAdapter().capabilities()

        assert caps.text is True


class TestAndroidTvPairing:
    def test_given_a_prompt_when_pairing_then_the_code_flow_runs_and_a_credential_returns(
        self,
    ):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)
        seen: list[str] = []

        credential = run(
            adapter.pair(_device(), prompt=_prompt_returning("1a2b3c", seen))
        )

        remote = factory.remotes[-1]
        assert remote.cert_generated is True
        assert remote.pairing_started is True
        assert remote.finished_code == "1a2b3c"
        assert seen and "code" in seen[0].lower()
        assert credential  # opaque, non-empty

    def test_given_pairing_when_it_finishes_then_the_credential_packs_cert_and_key(
        self,
    ):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        credential = run(adapter.pair(_device(), prompt=_prompt_returning("1a2b3c")))

        # The credential replays without a re-prompt: connecting with it succeeds.
        connect_factory = FakeAndroidTvRemoteFactory()
        connect_adapter = AndroidTvAdapter(remote_factory=connect_factory)
        session = run(connect_adapter.connect(_device(credential=credential)))
        assert isinstance(session, AndroidTvSession)

    def test_given_pairing_when_it_finishes_then_the_pairing_connection_is_closed(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        run(adapter.pair(_device(), prompt=_prompt_returning("1a2b3c")))

        assert factory.remotes[-1].disconnected is True

    def test_given_no_prompt_when_pairing_then_pairing_cancelled_is_raised(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        with pytest.raises(PairingCancelledError):
            run(adapter.pair(_device(), prompt=None))

    def test_given_no_prompt_when_pairing_then_the_device_is_not_contacted(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        with pytest.raises(PairingCancelledError):
            run(adapter.pair(_device(), prompt=None))

        assert factory.remotes == []

    def test_given_the_credential_when_persisted_then_it_round_trips_through_the_store(
        self, tmp_path
    ):
        # The design's open question: the JSON-packed, multi-line-PEM credential
        # survives the store's real JSON text serialization intact and reconnects.
        credential = _paired_credential()
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(credential=credential))

        restored = store.list()[0]

        assert restored.credential == credential
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)
        session = run(adapter.connect(restored))
        assert isinstance(session, AndroidTvSession)


class TestAndroidTvConnect:
    def test_given_a_valid_credential_when_connecting_then_a_session_is_returned(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        session = run(adapter.connect(_device(credential=_paired_credential())))

        assert isinstance(session, AndroidTvSession)
        assert factory.remotes[-1].connected is True

    def test_given_the_stored_address_when_connecting_then_the_remote_targets_that_host(
        self,
    ):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)

        run(adapter.connect(_device(ip="10.0.0.9", credential=_paired_credential())))

        assert factory.remotes[-1].host == "10.0.0.9"

    def test_given_a_cannot_connect_error_when_connecting_then_connection_failed(self):
        factory = FakeAndroidTvRemoteFactory(connect_error=CannotConnect("refused"))
        adapter = AndroidTvAdapter(remote_factory=factory)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential=_paired_credential())))

    def test_given_an_invalid_auth_error_when_connecting_then_connection_failed(self):
        factory = FakeAndroidTvRemoteFactory(connect_error=InvalidAuth("need to pair"))
        adapter = AndroidTvAdapter(remote_factory=factory)

        with pytest.raises(ConnectionFailedError):
            run(adapter.connect(_device(credential=_paired_credential())))

    def test_given_a_session_when_closed_then_the_key_material_is_removed_from_disk(
        self,
    ):
        # The design's central promise: no key material outlives the session on disk.
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)
        credential = _paired_credential()

        async def scenario():
            session = await adapter.connect(_device(credential=credential))
            cert_dir = os.path.dirname(factory.remotes[-1].certfile)
            assert os.path.exists(cert_dir)
            await session.close()
            return cert_dir

        cert_dir = run(scenario())
        assert not os.path.exists(cert_dir)
        assert factory.remotes[-1].disconnected is True


class TestAndroidTvKeyMapping:
    def test_given_the_key_map_when_read_then_directional_and_ok_map_to_keycodes(self):
        assert ANDROIDTV_KEYS[Key.UP] == "KEYCODE_DPAD_UP"
        assert ANDROIDTV_KEYS[Key.DOWN] == "KEYCODE_DPAD_DOWN"
        assert ANDROIDTV_KEYS[Key.LEFT] == "KEYCODE_DPAD_LEFT"
        assert ANDROIDTV_KEYS[Key.RIGHT] == "KEYCODE_DPAD_RIGHT"
        assert ANDROIDTV_KEYS[Key.OK] == "KEYCODE_DPAD_CENTER"

    def test_given_the_key_map_when_read_then_nav_volume_and_channel_map(self):
        assert ANDROIDTV_KEYS[Key.BACK] == "KEYCODE_BACK"
        assert ANDROIDTV_KEYS[Key.HOME] == "KEYCODE_HOME"
        assert ANDROIDTV_KEYS[Key.MENU] == "KEYCODE_MENU"
        assert ANDROIDTV_KEYS[Key.VOL_UP] == "KEYCODE_VOLUME_UP"
        assert ANDROIDTV_KEYS[Key.VOL_DOWN] == "KEYCODE_VOLUME_DOWN"
        assert ANDROIDTV_KEYS[Key.MUTE] == "KEYCODE_VOLUME_MUTE"
        assert ANDROIDTV_KEYS[Key.CH_UP] == "KEYCODE_CHANNEL_UP"
        assert ANDROIDTV_KEYS[Key.CH_DOWN] == "KEYCODE_CHANNEL_DOWN"

    def test_given_the_key_map_when_read_then_all_media_transport_keys_map(self):
        assert ANDROIDTV_KEYS[Key.PLAY] == "KEYCODE_MEDIA_PLAY"
        assert ANDROIDTV_KEYS[Key.PAUSE] == "KEYCODE_MEDIA_PAUSE"
        assert ANDROIDTV_KEYS[Key.PLAY_PAUSE] == "KEYCODE_MEDIA_PLAY_PAUSE"
        assert ANDROIDTV_KEYS[Key.STOP] == "KEYCODE_MEDIA_STOP"
        assert ANDROIDTV_KEYS[Key.REWIND] == "KEYCODE_MEDIA_REWIND"
        assert ANDROIDTV_KEYS[Key.FAST_FORWARD] == "KEYCODE_MEDIA_FAST_FORWARD"

    def test_given_the_key_map_when_read_then_the_digits_map(self):
        for digit in range(10):
            assert ANDROIDTV_KEYS[Key[f"NUM_{digit}"]] == f"KEYCODE_{digit}"

    def test_given_a_key_when_sent_then_the_matching_keycode_is_dispatched(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)
        credential = _paired_credential()

        async def scenario():
            session = await adapter.connect(_device(credential=credential))
            await session.send_key(Key.LEFT)
            await session.send_key(Key.OK)

        run(scenario())

        assert factory.remotes[-1].sent_keys == [
            "KEYCODE_DPAD_LEFT",
            "KEYCODE_DPAD_CENTER",
        ]


class TestAndroidTvText:
    def test_given_text_when_sent_then_it_is_dispatched_to_the_device(self):
        factory = FakeAndroidTvRemoteFactory()
        adapter = AndroidTvAdapter(remote_factory=factory)
        credential = _paired_credential()

        async def scenario():
            session = await adapter.connect(_device(credential=credential))
            await session.send_text("hello")

        run(scenario())

        assert factory.remotes[-1].sent_text == ["hello"]

    def test_given_text_send_fails_when_sending_then_text_unsupported_is_reported(self):
        factory = FakeAndroidTvRemoteFactory(reject_text=True)
        adapter = AndroidTvAdapter(remote_factory=factory)
        credential = _paired_credential()

        async def scenario():
            session = await adapter.connect(_device(credential=credential))
            with pytest.raises(TextUnsupportedError):
                await session.send_text("hello")

        run(scenario())
