from universal_remote.devices.models import Device


class TestWithdrawnTextInputField:
    def test_given_a_stored_entry_with_the_withdrawn_flag_when_loaded_then_it_is_ignored(
        self,
    ):
        # Devices saved while the opt-in existed still carry it; it selects nothing now.
        stored = {
            "name": "TV",
            "platform": "androidtv",
            "ip": "10.0.0.5",
            "text_via_adb": True,
        }

        device = Device.from_dict(stored)

        assert not hasattr(device, "text_via_adb")

    def test_given_such_an_entry_when_saved_again_then_the_flag_is_not_written_back(
        self,
    ):
        stored = {
            "name": "TV",
            "platform": "androidtv",
            "ip": "10.0.0.5",
            "text_via_adb": True,
        }

        device = Device.from_dict(stored)

        assert "text_via_adb" not in device.to_dict()
