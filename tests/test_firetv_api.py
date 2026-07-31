import asyncio

import pytest

from tests.fakes import FakeFireTvTransport, firetv_port_open
from universal_remote.adapters.firetv_api import (
    API_KEY,
    CONTROL_PORT,
    DIAL_PORT,
    USER_AGENT,
    WAKE_PATH,
    CommandRejectedError,
    RemoteApi,
    ServiceUnavailableError,
)

_HOST = "10.0.0.5"


def run(coro):
    return asyncio.run(coro)


def _api(
    transport: FakeFireTvTransport,
    *,
    token: str | None = None,
    port_open=firetv_port_open,
    wake_timeout: float = 1.0,
    poll_interval: float = 0.0,
) -> RemoteApi:
    return RemoteApi(
        _HOST,
        transport,
        token=token,
        port_open=port_open,
        wake_timeout=wake_timeout,
        poll_interval=poll_interval,
    )


def _refusing_probe(accept_after: int) -> tuple[list[int], object]:
    """A control-port probe that refuses until `accept_after` probes have been made."""
    probes: list[int] = []

    async def port_open(_ip: str, port: int, _timeout: float) -> bool:
        probes.append(port)
        return len(probes) > accept_after

    return probes, port_open


class TestFireTvRequestConstruction:
    def test_given_a_command_when_sent_then_the_protocol_api_key_and_user_agent_ride_it(
        self,
    ):
        transport = FakeFireTvTransport()

        run(_api(transport).send_action("home"))

        headers = transport.requests[0].headers
        assert headers["X-Api-Key"] == API_KEY
        assert headers["User-Agent"] == USER_AGENT

    def test_given_a_held_token_when_a_command_is_sent_then_it_rides_as_a_header(self):
        transport = FakeFireTvTransport()

        run(_api(transport, token="AB1CD2E").send_action("home"))

        assert transport.requests[0].headers["X-Client-Token"] == "AB1CD2E"

    def test_given_no_token_when_a_command_is_sent_then_no_client_token_is_claimed(
        self,
    ):
        # Pairing runs before a token exists; sending an empty one would be a lie.
        transport = FakeFireTvTransport()

        run(_api(transport).display_pin("Universal Remote"))

        assert "X-Client-Token" not in transport.requests[0].headers

    def test_given_a_command_when_sent_then_it_goes_to_the_control_port_over_https(
        self,
    ):
        transport = FakeFireTvTransport()

        run(_api(transport).send_action("home"))

        assert transport.requests[0].url == (
            f"https://{_HOST}:{CONTROL_PORT}/v1/FireTV?action=home"
        )

    def test_given_a_command_when_sent_then_tls_verification_is_waived_on_that_request(
        self,
    ):
        # The device presents a self-signed certificate. The waiver rides the request
        # itself, so it cannot reach any host but the one the request addresses.
        transport = FakeFireTvTransport()

        run(_api(transport).send_action("home"))

        assert transport.requests[0].verify_tls is False

    def test_given_a_key_action_when_sent_then_the_request_body_is_empty(self):
        # A JSON body makes the device answer 500 even for a key it dispatched, which
        # destroys error reporting; an empty body answers 200/400 truthfully.
        transport = FakeFireTvTransport()

        run(_api(transport).send_action("home"))

        assert transport.requests[0].json is None


class TestFireTvWake:
    def test_given_an_idle_device_when_woken_then_the_dial_app_is_launched(self):
        transport = FakeFireTvTransport()

        run(_api(transport).wake())

        assert transport.requests[0].url == f"http://{_HOST}:{DIAL_PORT}{WAKE_PATH}"
        assert transport.requests[0].method == "POST"

    def test_given_a_closed_control_port_when_woken_then_it_is_polled_until_it_accepts(
        self,
    ):
        probes, port_open = _refusing_probe(accept_after=2)

        run(_api(FakeFireTvTransport(), port_open=port_open).wake())

        assert probes == [CONTROL_PORT, CONTROL_PORT, CONTROL_PORT]

    def test_given_an_already_running_service_when_woken_then_the_wake_succeeds(self):
        # Launching a running app is harmless, and its port already accepts.
        probes, port_open = _refusing_probe(accept_after=0)

        run(_api(FakeFireTvTransport(), port_open=port_open).wake())

        assert probes == [CONTROL_PORT]

    def test_given_a_port_that_never_accepts_when_woken_then_the_wake_fails(self):
        async def never_open(_ip: str, _port: int, _timeout: float) -> bool:
            return False

        api = _api(FakeFireTvTransport(), port_open=never_open, wake_timeout=0.0)

        with pytest.raises(ServiceUnavailableError):
            run(api.wake())

    def test_given_an_unreachable_device_when_woken_then_the_wake_fails(self):
        transport = FakeFireTvTransport()
        transport.fail_once = WAKE_PATH

        with pytest.raises(ServiceUnavailableError):
            run(_api(transport).wake())


class TestFireTvPinDisplay:
    def test_given_a_pin_request_when_sent_then_the_client_name_is_supplied(self):
        # The route answers "Bad arguments supplied" without a friendly name, and the
        # name is what the television labels the pairing request with.
        transport = FakeFireTvTransport()

        run(_api(transport).display_pin("Universal Remote"))

        assert transport.requests[0].json == {"friendlyName": "Universal Remote"}


class TestFireTvCommandOutcome:
    def test_given_the_device_rejects_a_command_then_it_is_reported_as_rejected(self):
        transport = FakeFireTvTransport()
        transport.reject = "/v1/FireTV"

        with pytest.raises(CommandRejectedError):
            run(_api(transport).send_action("nonsense"))

    def test_given_a_rejection_carries_a_reason_when_raised_then_it_names_that_reason(
        self,
    ):
        # The device explains itself in `description`; dropping it leaves a bare status
        # that says nothing about what the device actually objected to.
        transport = FakeFireTvTransport()
        transport.reject = "/v1/FireTV"
        transport.reject_reason = "Bad arguments supplied. Please check inputs."

        with pytest.raises(CommandRejectedError, match="Bad arguments supplied"):
            run(_api(transport).send_action("home"))

    def test_given_the_service_has_stopped_when_a_command_is_sent_then_it_is_unavailable(
        self,
    ):
        # A stopped service is transient, so it must be distinguishable from a
        # rejection: only the transient one is worth re-waking and retrying.
        transport = FakeFireTvTransport()
        transport.fail_once = "/v1/FireTV"

        with pytest.raises(ServiceUnavailableError):
            run(_api(transport).send_action("home"))

    def test_given_a_pin_verify_when_accepted_then_the_token_is_read_from_description(
        self,
    ):
        transport = FakeFireTvTransport(token="XY7ZQ12")

        assert run(_api(transport).verify_pin("1234")) == "XY7ZQ12"

    def test_given_a_keyboard_read_when_a_field_is_focused_then_its_state_and_text(
        self,
    ):
        transport = FakeFireTvTransport(keyboard={"state": "text", "text": "cat"})

        assert run(_api(transport).keyboard_state()) == ("text", "cat")
