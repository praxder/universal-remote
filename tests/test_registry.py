import pytest

from universal_remote.errors import UnsupportedPlatformError
from universal_remote.registry import AdapterRegistry


class _StubAdapter:
    platform = "stub-tv"


class TestAdapterRegistry:
    def test_given_a_registered_adapter_when_resolving_its_platform_then_it_is_returned(
        self,
    ):
        registry = AdapterRegistry()
        adapter = _StubAdapter()
        registry.register(adapter)

        assert registry.resolve("stub-tv") is adapter

    def test_given_an_unregistered_platform_when_resolving_then_unsupported_is_reported(
        self,
    ):
        registry = AdapterRegistry()

        with pytest.raises(UnsupportedPlatformError):
            registry.resolve("no-such-tv")

    def test_given_an_unregistered_platform_when_checking_support_then_false(self):
        registry = AdapterRegistry()

        assert registry.is_supported("no-such-tv") is False

    def test_given_a_registered_platform_when_checking_support_then_true(self):
        registry = AdapterRegistry()
        registry.register(_StubAdapter())

        assert registry.is_supported("stub-tv") is True
