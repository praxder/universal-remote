import json
import stat

from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore


def _device(**overrides) -> Device:
    base = dict(name="Living Room", platform="samsung-tizen", ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


class TestDeviceStorePersistence:
    def test_given_no_store_when_a_device_is_saved_then_file_is_created_with_mode_0600(
        self, tmp_path
    ):
        path = tmp_path / "config" / "devices.json"
        store = DeviceStore(path=path)

        store.save_all([_device()])

        assert path.exists()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_given_a_saved_device_when_reloaded_then_it_is_present(self, tmp_path):
        path = tmp_path / "devices.json"
        DeviceStore(path=path).save_all([_device(name="Bedroom")])

        reloaded = DeviceStore(path=path).list()

        assert [d.name for d in reloaded] == ["Bedroom"]

    def test_given_a_device_with_a_credential_when_round_tripped_then_credential_is_preserved(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        DeviceStore(path=path).save_all([_device(credential="secret-token")])

        reloaded = DeviceStore(path=path).list()

        assert reloaded[0].credential == "secret-token"

    def test_given_no_store_when_listing_then_an_empty_list_is_returned(self, tmp_path):
        store = DeviceStore(path=tmp_path / "missing.json")

        assert store.list() == []

    def test_given_two_saved_devices_when_listing_then_both_are_returned(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        DeviceStore(path=path).save_all([_device(name="A"), _device(name="B")])

        names = {d.name for d in DeviceStore(path=path).list()}

        assert names == {"A", "B"}


class TestReconnectionIdentifier:
    def test_given_a_device_with_an_identifier_when_round_tripped_then_it_is_preserved(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        DeviceStore(path=path).save_all([_device(identifier="atv-id-123")])

        reloaded = DeviceStore(path=path).list()

        assert reloaded[0].identifier == "atv-id-123"

    def test_given_a_device_without_an_identifier_when_loaded_then_it_is_none(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        DeviceStore(path=path).save_all([_device()])

        reloaded = DeviceStore(path=path).list()

        assert reloaded[0].identifier is None

    def test_given_an_entry_with_no_identifier_key_when_loaded_then_it_loads(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        entry = {"name": "Legacy", "platform": "samsung-tizen", "ip": "10.0.0.5"}
        path.write_text(json.dumps({"devices": [entry]}))

        loaded = DeviceStore(path=path).list()

        assert [d.name for d in loaded] == ["Legacy"]
        assert loaded[0].identifier is None


class TestLegacyFieldTolerance:
    def test_given_an_entry_with_legacy_mac_and_model_when_loaded_then_it_loads(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        legacy = {
            "name": "Old TV",
            "platform": "samsung-tizen",
            "ip": "10.0.0.5",
            "mac": "aa:bb:cc:dd:ee:ff",
            "model": "UN55LS03",
        }
        path.write_text(json.dumps({"devices": [legacy]}))

        loaded = DeviceStore(path=path).list()

        assert [d.name for d in loaded] == ["Old TV"]
        assert loaded[0].ip == "10.0.0.5"

    def test_given_a_legacy_entry_when_re_saved_then_mac_and_model_keys_are_absent(
        self, tmp_path
    ):
        path = tmp_path / "devices.json"
        legacy = {
            "name": "Old TV",
            "platform": "samsung-tizen",
            "ip": "10.0.0.5",
            "mac": "aa:bb:cc:dd:ee:ff",
            "model": "UN55LS03",
        }
        path.write_text(json.dumps({"devices": [legacy]}))
        store = DeviceStore(path=path)

        store.save_all(store.list())

        entry = json.loads(path.read_text())["devices"][0]
        assert "mac" not in entry
        assert "model" not in entry
