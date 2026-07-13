from universal_remote.devices.models import Device
from universal_remote.devices.store import DeviceStore


def _device(**overrides) -> Device:
    base = dict(name="TV", platform="samsung-tizen", ip="10.0.0.5")
    base.update(overrides)
    return Device(**base)


class TestDeviceCrud:
    def test_given_a_new_device_when_added_then_it_appears_in_the_list(self, tmp_path):
        store = DeviceStore(path=tmp_path / "d.json")

        store.add(_device(name="New"))

        assert [d.name for d in store.list()] == ["New"]

    def test_given_an_existing_device_when_edited_then_the_change_persists(
        self, tmp_path
    ):
        path = tmp_path / "d.json"
        store = DeviceStore(path=path)
        device = store.add(_device(name="Old"))

        device.name = "Renamed"
        store.update(device)

        reloaded = DeviceStore(path=path).list()
        assert reloaded[0].name == "Renamed"

    def test_given_multiple_devices_when_one_is_deleted_then_only_it_is_removed(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="Keep"))
        drop = store.add(_device(name="Drop"))

        store.delete(drop.id)

        assert [d.name for d in store.list()] == ["Keep"]


class TestFindConflict:
    def test_given_a_duplicate_name_when_checked_then_the_name_message_is_returned(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="Living Room", ip="10.0.0.5"))

        message = store.find_conflict(name=" living room ", ip="10.0.0.9")

        assert message == "A device named ' living room ' already exists."

    def test_given_a_duplicate_ip_when_checked_then_the_ip_message_is_returned(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="Living Room", ip="10.0.0.5"))

        message = store.find_conflict(name="Bedroom", ip=" 10.0.0.5 ")

        assert message == "A device with IP  10.0.0.5  already exists."

    def test_given_a_unique_name_and_ip_when_checked_then_none_is_returned(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="Living Room", ip="10.0.0.5"))

        assert store.find_conflict(name="Bedroom", ip="10.0.0.9") is None

    def test_given_both_name_and_ip_collide_when_checked_then_the_name_message_wins(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="Living Room", ip="10.0.0.5"))

        message = store.find_conflict(name="Living Room", ip="10.0.0.5")

        assert message == "A device named 'Living Room' already exists."

    def test_given_the_matching_device_is_excluded_when_checked_then_none_is_returned(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        device = store.add(_device(name="Living Room", ip="10.0.0.5"))

        assert (
            store.find_conflict(name="Living Room", ip="10.0.0.5", exclude_id=device.id)
            is None
        )
