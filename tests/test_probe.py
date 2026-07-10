import json

from universal_remote.devices.probe import ProbeResult, probe_device

_INFO = {
    "device": {
        "name": "Samsung Frame",
        "modelName": "UN55LS03",
        "wifiMac": "aa:bb:cc:dd:ee:ff",
    }
}


class TestInfoProbe:
    def test_given_a_reachable_tv_when_probed_then_name_model_and_mac_are_prefilled(
        self,
    ):
        def fetch(url: str) -> bytes:
            assert url == "http://10.0.0.5:8001/api/v2/"
            return json.dumps(_INFO).encode()

        result = probe_device("10.0.0.5", fetch=fetch)

        assert result == ProbeResult(
            name="Samsung Frame", model="UN55LS03", mac="aa:bb:cc:dd:ee:ff"
        )

    def test_given_an_unreachable_ip_when_probed_then_none_is_returned_without_raising(
        self,
    ):
        def fetch(url: str) -> bytes:
            raise OSError("connection refused")

        result = probe_device("10.0.0.9", fetch=fetch)

        assert result is None
