import asyncio

import pytest

from tests.fakes import FakeAdapter
from universal_remote.errors import PairingCancelledError


def run(coro):
    return asyncio.run(coro)


class TestPairingLifecycle:
    def test_given_successful_pairing_when_completed_then_a_persistable_credential_is_returned(
        self,
    ):
        adapter = FakeAdapter(pair_token="token-123")

        credential = run(adapter.pair(device=object()))

        assert credential == "token-123"

    def test_given_cancelled_pairing_when_run_then_it_reports_cancelled_and_persists_nothing(
        self,
    ):
        adapter = FakeAdapter(pair_cancels=True)

        async def scenario():
            with pytest.raises(PairingCancelledError):
                await adapter.pair(device=object())

        run(scenario())

        assert adapter.paired_devices == []
