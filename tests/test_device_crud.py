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


class TestCrudPreservesOrder:
    """Guarantees the "List devices" requirement makes about the stored order."""

    def test_given_saved_devices_when_one_is_added_then_it_is_listed_last(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="A"))
        store.add(_device(name="B"))

        store.add(_device(name="C"))

        assert [d.name for d in store.list()] == ["A", "B", "C"]

    def test_given_a_middle_device_when_edited_then_it_keeps_its_position(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="A"))
        middle = store.add(_device(name="B"))
        store.add(_device(name="C"))

        middle.name = "Renamed"
        store.update(middle)

        assert [d.name for d in store.list()] == ["A", "Renamed", "C"]

    def test_given_three_devices_when_one_is_deleted_then_the_rest_keep_their_order(
        self, tmp_path
    ):
        store = DeviceStore(path=tmp_path / "d.json")
        store.add(_device(name="A"))
        middle = store.add(_device(name="B"))
        store.add(_device(name="C"))

        store.delete(middle.id)

        assert [d.name for d in store.list()] == ["A", "C"]


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
