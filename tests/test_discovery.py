import asyncio

from universal_remote.discovery import (
    DiscoveredDevice,
    browse_mdns,
    discover,
    exclude_saved,
    merge,
    search_ssdp,
)


def run(coro):
    return asyncio.run(coro)


class _FakeInfo:
    """Stands in for `AsyncServiceInfo`: name, parsed addresses, decoded TXT."""

    def __init__(self, name: str, addresses: list[str], properties: dict[str, str]):
        self.name = name
        self._addresses = addresses
        self.decoded_properties = properties

    def parsed_addresses(self) -> list[str]:
        return self._addresses


class _FakeAsyncZeroconf:
    """Stands in for `AsyncZeroconf`: records that it was closed after the run."""

    def __init__(self) -> None:
        self.zeroconf = object()
        self.closed = False

    async def async_close(self) -> None:
        self.closed = True


class _RecordingZcFactory:
    """A `zeroconf_factory` that records each instance it hands out."""

    def __init__(self) -> None:
        self.instances: list[_FakeAsyncZeroconf] = []

    def __call__(self) -> _FakeAsyncZeroconf:
        instance = _FakeAsyncZeroconf()
        self.instances.append(instance)
        return instance


class TestNameFallback:
    def test_given_a_blank_name_when_constructed_then_the_name_falls_back_to_the_ip(
        self,
    ):
        device = DiscoveredDevice(name="  ", platform="roku", ip="10.0.0.5")

        assert device.name == "10.0.0.5"

    def test_given_a_real_name_when_constructed_then_the_name_is_trimmed_and_kept(self):
        device = DiscoveredDevice(
            name="  Living Room  ", platform="roku", ip="10.0.0.5"
        )

        assert device.name == "Living Room"


class TestMerge:
    def test_given_one_ip_as_firetv_and_androidtv_when_merged_then_firetv_wins(self):
        # Arrange: a Fire TV answers both mDNS services on the same IP; Android TV
        # is discovered first, so the priority rule must still keep Fire TV.
        found = [
            DiscoveredDevice(name="Den", platform="androidtv", ip="10.0.0.5"),
            DiscoveredDevice(name="Den", platform="firetv", ip="10.0.0.5"),
        ]

        merged = merge(found)

        assert [(d.platform, d.ip) for d in merged] == [("firetv", "10.0.0.5")]

    def test_given_two_distinct_ips_when_merged_then_both_survive(self):
        found = [
            DiscoveredDevice(name="A", platform="roku", ip="10.0.0.5"),
            DiscoveredDevice(name="B", platform="samsung-tizen", ip="10.0.0.6"),
        ]

        merged = merge(found)

        assert {d.ip for d in merged} == {"10.0.0.5", "10.0.0.6"}


class TestExcludeSaved:
    def test_given_a_saved_ip_when_excluded_then_that_device_is_dropped(self):
        found = [DiscoveredDevice(name="A", platform="roku", ip="10.0.0.5")]

        remaining = exclude_saved(found, saved_ips=[" 10.0.0.5 "])

        assert remaining == []

    def test_given_a_new_ip_when_excluded_then_that_device_is_kept(self):
        found = [DiscoveredDevice(name="A", platform="roku", ip="10.0.0.9")]

        remaining = exclude_saved(found, saved_ips=["10.0.0.5"])

        assert [d.ip for d in remaining] == ["10.0.0.9"]


class TestBrowseMdns:
    def test_given_resolved_services_when_browsing_then_hits_carry_name_ip_and_txt(
        self,
    ):
        # Arrange: the injected resolver returns one service info whose instance
        # name still carries the service-type suffix, so browse must strip it.
        info = _FakeInfo(
            name="Living Room._androidtvremote2._tcp.local.",
            addresses=["10.0.0.5"],
            properties={"bt": "AA:BB"},
        )

        async def fake_resolve(azc, service_type, timeout):
            return [info]

        hits = run(
            browse_mdns(
                "_androidtvremote2._tcp.local.",
                timeout=0.01,
                zeroconf_factory=_RecordingZcFactory(),
                resolve=fake_resolve,
            )
        )

        assert [(h.name, h.ip, h.properties) for h in hits] == [
            ("Living Room", "10.0.0.5", {"bt": "AA:BB"})
        ]

    def test_given_a_run_when_browsing_then_one_shared_zeroconf_is_opened_and_closed(
        self,
    ):
        factory = _RecordingZcFactory()

        async def fake_resolve(azc, service_type, timeout):
            return []

        run(
            browse_mdns(
                "_amzn-wplay._tcp.local.",
                timeout=0.01,
                zeroconf_factory=factory,
                resolve=fake_resolve,
            )
        )

        assert len(factory.instances) == 1
        assert factory.instances[0].closed is True

    def test_given_the_resolver_fails_when_browsing_then_nothing_is_yielded_no_raise(
        self,
    ):
        factory = _RecordingZcFactory()

        async def failing_resolve(azc, service_type, timeout):
            raise OSError("multicast blocked")

        hits = run(
            browse_mdns(
                "_amzn-wplay._tcp.local.",
                timeout=0.01,
                zeroconf_factory=factory,
                resolve=failing_resolve,
            )
        )

        assert hits == []
        # The shared zeroconf is still closed even when the browse fails.
        assert factory.instances[0].closed is True


class TestSearchSsdp:
    def test_given_a_responder_when_searching_then_the_hit_carries_ip_and_location(
        self,
    ):
        # Arrange: a fake SSDP search that answers a single responder for the target.
        seen_targets: list[str] = []

        async def fake_search(async_callback, search_target, timeout):
            seen_targets.append(search_target)
            await async_callback(
                {
                    "_remote_addr": ("10.0.0.7", 1900),
                    "location": "http://10.0.0.7:7676/desc.xml",
                }
            )

        hits = run(search_ssdp("roku:ecp", timeout=0.01, search=fake_search))

        assert [(h.ip, h.location) for h in hits] == [
            ("10.0.0.7", "http://10.0.0.7:7676/desc.xml")
        ]
        assert seen_targets == ["roku:ecp"]

    def test_given_the_search_fails_when_searching_then_nothing_is_yielded_no_raise(
        self,
    ):
        async def failing_search(async_callback, search_target, timeout):
            raise OSError("no route to multicast group")

        hits = run(
            search_ssdp(
                "urn:samsung.com:device:RemoteControlReceiver:1",
                timeout=0.01,
                search=failing_search,
            )
        )

        assert hits == []

    def test_given_a_responder_then_an_error_when_searching_then_the_hit_survives(self):
        # A mid-search failure keeps whatever was already collected (best-effort).
        async def flaky_search(async_callback, search_target, timeout):
            await async_callback(
                {"_remote_addr": ("10.0.0.8", 1900), "location": "http://10.0.0.8/d"}
            )
            raise TimeoutError()

        hits = run(search_ssdp("roku:ecp", timeout=0.01, search=flaky_search))

        assert [h.ip for h in hits] == ["10.0.0.8"]


class _FakeDiscoverAdapter:
    """An adapter double whose `discover` returns canned devices, raises, or hangs.

    `delay` models a scan that legitimately uses most of its window (browse sleeps,
    then resolves) so the orchestrator's backstop must exceed the scan timeout.
    """

    def __init__(self, devices=None, error=None, hangs=False, delay=0.0):
        self._devices = devices or []
        self._error = error
        self._hangs = hangs
        self._delay = delay

    async def discover(self, timeout):
        if self._hangs:
            await asyncio.sleep(3600)
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return self._devices


class _NonDiscoverAdapter:
    """An adapter with no discovery capability, read via `hasattr` and skipped."""


class TestDiscover:
    def test_given_adapters_when_discovering_then_results_merge_and_exclude_saved(self):
        # Arrange: one adapter reports a Fire TV and an Android TV on the same IP
        # (must collapse to Fire TV); another reports a distinct device and one
        # whose IP is already saved (must be excluded).
        mdns = _FakeDiscoverAdapter(
            devices=[
                DiscoveredDevice(name="Den", platform="androidtv", ip="10.0.0.5"),
                DiscoveredDevice(name="Den", platform="firetv", ip="10.0.0.5"),
            ]
        )
        ssdp = _FakeDiscoverAdapter(
            devices=[
                DiscoveredDevice(name="Roku", platform="roku", ip="10.0.0.6"),
                DiscoveredDevice(name="Saved", platform="samsung-tizen", ip="10.0.0.7"),
            ]
        )

        found = run(discover([mdns, ssdp], saved_ips=["10.0.0.7"], timeout=0.05))

        assert sorted((d.platform, d.ip) for d in found) == [
            ("firetv", "10.0.0.5"),
            ("roku", "10.0.0.6"),
        ]

    def test_given_a_failing_or_hanging_adapter_when_discovering_then_others_survive(
        self,
    ):
        good = _FakeDiscoverAdapter(
            devices=[DiscoveredDevice(name="Roku", platform="roku", ip="10.0.0.6")]
        )
        failing = _FakeDiscoverAdapter(error=RuntimeError("scan failed"))
        hanging = _FakeDiscoverAdapter(hangs=True)

        found = run(discover([failing, hanging, good], saved_ips=[], timeout=0.05))

        assert [(d.platform, d.ip) for d in found] == [("roku", "10.0.0.6")]

    def test_given_an_adapter_without_discover_when_discovering_then_it_is_skipped(
        self,
    ):
        good = _FakeDiscoverAdapter(
            devices=[DiscoveredDevice(name="Roku", platform="roku", ip="10.0.0.6")]
        )

        found = run(discover([_NonDiscoverAdapter(), good], saved_ips=[], timeout=0.05))

        assert [d.ip for d in found] == ["10.0.0.6"]

    def test_given_a_scan_that_uses_its_full_window_when_discovering_then_it_survives(
        self,
    ):
        # A real scan runs for ~timeout (browse sleeps the whole window, then
        # resolves), so the isolation backstop must exceed the scan window — else a
        # valid scan is cancelled at completion and its results are lost.
        slow_but_valid = _FakeDiscoverAdapter(
            devices=[DiscoveredDevice(name="Roku", platform="roku", ip="10.0.0.6")],
            delay=0.3,
        )

        found = run(discover([slow_but_valid], saved_ips=[], timeout=0.2))

        assert [d.ip for d in found] == ["10.0.0.6"]
