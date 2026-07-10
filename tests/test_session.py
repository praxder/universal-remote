import asyncio

import pytest

from tests.fakes import FakeAdapter
from universal_remote.capabilities import Capabilities
from universal_remote.errors import SessionClosedError, UnsupportedKeyError
from universal_remote.keys import Key


def run(coro):
    return asyncio.run(coro)


class TestSessionDispatch:
    def test_given_a_supported_key_when_sent_then_it_is_dispatched(self):
        adapter = FakeAdapter(
            capabilities=Capabilities(keys=frozenset({Key.UP}), text=True)
        )

        async def scenario():
            session = await adapter.connect()
            await session.send_key(Key.UP)
            return session

        session = run(scenario())

        assert session.sent_keys == [Key.UP]

    def test_given_an_unsupported_key_when_sent_then_rejected_without_substitute(self):
        adapter = FakeAdapter(capabilities=Capabilities(keys=frozenset({Key.UP})))

        async def scenario():
            session = await adapter.connect()
            with pytest.raises(UnsupportedKeyError):
                await session.send_key(Key.DOWN)
            return session

        session = run(scenario())

        assert session.sent_keys == []

    def test_given_a_closed_session_when_sending_then_it_fails(self):
        adapter = FakeAdapter(capabilities=Capabilities(keys=frozenset({Key.UP})))

        async def scenario():
            session = await adapter.connect()
            await session.close()
            with pytest.raises(SessionClosedError):
                await session.send_key(Key.UP)

        run(scenario())

    def test_given_an_open_session_when_closed_then_underlying_is_released(self):
        adapter = FakeAdapter()

        async def scenario():
            session = await adapter.connect()
            await session.close()
            return session

        session = run(scenario())

        assert session.closed is True
