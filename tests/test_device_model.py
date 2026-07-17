from universal_remote.devices.models import Device


class TestTextViaAdbField:
    def test_given_text_via_adb_enabled_when_round_tripped_then_it_is_preserved(self):
        device = Device(
            name="TV", platform="androidtv", ip="10.0.0.5", text_via_adb=True
        )

        restored = Device.from_dict(device.to_dict())

        assert restored.text_via_adb is True

    def test_given_legacy_json_without_the_field_when_loaded_then_it_defaults_to_false(
        self,
    ):
        legacy = {"name": "TV", "platform": "androidtv", "ip": "10.0.0.5"}

        device = Device.from_dict(legacy)

        assert device.text_via_adb is False
