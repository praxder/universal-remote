import asyncio
import socket

from universal_remote import reachability
from universal_remote.reachability import Reachability, probe


def run(coro):
    return asyncio.run(coro)


class TestProbeReachable:
    def test_given_a_listening_port_when_probed_then_it_reports_reachable(self):
        # Arrange: a bound, listening socket completes the TCP handshake.
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        try:
            result = run(probe("127.0.0.1", port, timeout=1.0))
        finally:
            listener.close()

        assert result is Reachability.REACHABLE


class TestProbeUnreachable:
    def test_given_a_refused_port_when_probed_then_it_reports_unreachable(self):
        # Arrange: bind then close, so the port is closed and refuses connections.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        result = run(probe("127.0.0.1", port, timeout=1.0))

        assert result is Reachability.UNREACHABLE

    def test_given_a_slow_port_when_the_timeout_elapses_then_it_reports_unreachable(
        self, monkeypatch
    ):
        # Arrange: a connection that never resolves, so only the timeout ends it.
        async def never_connects(*_args, **_kwargs):
            await asyncio.sleep(10)

        monkeypatch.setattr(reachability.asyncio, "open_connection", never_connects)

        result = run(probe("10.0.0.5", 8002, timeout=0.01))

        assert result is Reachability.UNREACHABLE

    def test_given_a_network_error_when_probed_then_it_reports_unreachable(
        self, monkeypatch
    ):
        async def raises_oserror(*_args, **_kwargs):
            raise OSError("network unreachable")

        monkeypatch.setattr(reachability.asyncio, "open_connection", raises_oserror)

        result = run(probe("10.0.0.5", 8002, timeout=1.0))

        assert result is Reachability.UNREACHABLE


class TestPortlessAdapter:
    def test_given_an_adapter_without_a_port_when_read_then_it_is_none(self):
        # An adapter that declares no reachability_port degrades to unknown.
        class _Portless:
            pass

        assert getattr(_Portless(), "reachability_port", None) is None
