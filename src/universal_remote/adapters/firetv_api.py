"""The Fire TV remote-control REST API — the transport `firetv.py` drives.

Fire OS exposes the undocumented HTTPS API that Amazon's own remote app uses, which
needs no developer mode and no ADB. Its control port stays closed until a DIAL app
launch starts the remote service, so every entry point wakes the device first and
waits for that port to accept.

Requests carry a fixed protocol API key and the remote app's user agent; the client
token pairing yields is what actually authorises a command. The device presents a
self-signed certificate, so TLS verification is waived per request rather than
process-wide — the waiver rides the request and reaches no other host.

Two failures are distinguished, because only one of them is worth retrying: a
transport failure means the idle remote service has gone away (re-wake and retry),
while a failure status means the device answered and refused.
"""

from __future__ import annotations

import asyncio
import time
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

import aiohttp

from ..errors import UniversalRemoteError

DIAL_PORT = 8009  # DIAL; open on a stock device, and how the remote service is woken
CONTROL_PORT = 8080  # the remote-control API, closed until the service is woken
WAKE_PATH = "/apps/FireTVRemote"

KEY_PATH = "/v1/FireTV"  # also the info route, which reports device capabilities
MEDIA_PATH = "/v1/media"
KEYBOARD_PATH = "/v1/FireTV/keyboard"
PIN_DISPLAY_PATH = "/v1/FireTV/pin/display"
PIN_VERIFY_PATH = "/v1/FireTV/pin/verify"

# A fixed value in the protocol rather than a per-user secret; it carries no
# entitlement on its own, since the client token is what authorises a command.
API_KEY = "0987654321"
USER_AGENT = "okhttp/4.10.0"

# What a keyboard read reports when a text field holds focus; anything else (in
# practice "hidden") means a write would be accepted and then discarded.
KEYBOARD_STATE_TEXT = "text"

WAKE_TIMEOUT = 10.0  # seconds to wait for the control port after a wake
_WAKE_POLL_INTERVAL = 0.25  # seconds between control-port probes
_REQUEST_TIMEOUT = 5.0  # seconds for one control request


class ServiceUnavailableError(UniversalRemoteError):
    """The device's remote-control service could not be reached."""


class CommandRejectedError(UniversalRemoteError):
    """The device answered a request with a failure status."""


@dataclass(frozen=True)
class Request:
    """One HTTP request to a Fire TV, as the injected transport receives it."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    json: dict[str, Any] | None = None
    verify_tls: bool = True


@dataclass(frozen=True)
class Response:
    """A device reply: its status, and its JSON body when it sent one."""

    status: int
    body: dict[str, Any]

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class Transport(Protocol):
    """Sends one request and can be closed by whoever owns it."""

    async def __call__(self, request: Request) -> Response: ...

    async def close(self) -> None: ...


# The control-port probe seam, injected so waking is testable without a network.
PortProbe = Callable[[str, int, float], Awaitable[bool]]

# A factory so the adapter builds one transport per pairing or session.
TransportFactory = Callable[[], Transport]


async def _read_json(response: aiohttp.ClientResponse) -> dict[str, Any]:
    """Parse a JSON body, tolerating the empty and non-JSON bodies routes return."""
    with suppress(Exception):
        body = await response.json(content_type=None)
        if isinstance(body, dict):
            return body
    return {}


class AiohttpTransport:
    """The default transport: one `aiohttp` session reused across requests.

    Reuse is deliberate — a fresh TLS handshake per keypress would cost more than the
    keypress itself. The owner closes it, the way the Roku adapter owns the session
    it hands its client.
    """

    def __init__(self, timeout: float = _REQUEST_TIMEOUT) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

    async def __call__(self, request: Request) -> Response:
        async with self._session.request(
            request.method,
            request.url,
            headers=request.headers,
            json=request.json,
            ssl=request.verify_tls,  # False accepts the device's self-signed cert
        ) as response:
            return Response(response.status, await _read_json(response))

    async def close(self) -> None:
        await self._session.close()


async def _close(writer: asyncio.StreamWriter) -> None:
    writer.close()
    with suppress(OSError):
        await writer.wait_closed()


async def tcp_port_open(ip: str, port: int, timeout: float) -> bool:
    """True when a TCP connection to `ip:port` opens within `timeout`.

    A local probe rather than the shared reachability one: waking polls this
    repeatedly, so the socket it opens is fully closed before returning.
    """
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout
        )
    except (asyncio.TimeoutError, OSError):
        return False
    await _close(writer)
    return True


class RemoteApi:
    """The remote-control API of one Fire TV: wake, pair, and dispatch."""

    def __init__(
        self,
        host: str,
        transport: Transport,
        *,
        token: str | None = None,
        port_open: PortProbe = tcp_port_open,
        wake_timeout: float = WAKE_TIMEOUT,
        poll_interval: float = _WAKE_POLL_INTERVAL,
    ) -> None:
        self._host = host
        self._transport = transport
        self._token = token
        self._port_open = port_open
        self._wake_timeout = wake_timeout
        self._poll_interval = poll_interval

    async def wake(self) -> None:
        """Start the remote service and wait for its control port to accept.

        Idempotent: launching an already-running app is harmless, and its port
        already accepts. The probe, not the launch status, is what proves the
        service is up, so a launch the device answers oddly is not itself a failure.
        """
        await self._send(Request("POST", f"http://{self._host}:{DIAL_PORT}{WAKE_PATH}"))
        await self._await_control_port()

    async def send_action(self, action: str) -> None:
        """Dispatch a navigation action, with an empty body (see the change design)."""
        await self._command(self._control("POST", f"{KEY_PATH}?action={action}"))

    async def send_media(self, action: str) -> None:
        """Dispatch a transport action, which lives on its own route."""
        await self._command(self._control("POST", f"{MEDIA_PATH}?action={action}"))

    async def keyboard_state(self) -> tuple[str, str]:
        """The focused text field's state and current contents."""
        body = (await self._command(self._control("GET", KEYBOARD_PATH))).body
        return body.get("state", ""), body.get("text", "")

    async def set_keyboard_text(self, text: str) -> None:
        """Replace the focused field's contents; the route has no append mode."""
        await self._command(
            self._control("POST", KEYBOARD_PATH, json={"text": text}),
        )

    async def display_pin(self) -> None:
        """Ask the device to show its pairing PIN on the television."""
        await self._command(self._control("POST", PIN_DISPLAY_PATH))

    async def verify_pin(self, pin: str) -> str:
        """Exchange a PIN for the client token; the device returns it as a description."""
        response = await self._command(
            self._control("POST", PIN_VERIFY_PATH, json={"pin": pin}),
        )
        return response.body.get("description", "")

    async def info(self) -> Response:
        """Read the device's reported capabilities — an authenticated round trip."""
        return await self._command(self._control("GET", KEY_PATH))

    async def _await_control_port(self) -> None:
        deadline = time.monotonic() + self._wake_timeout
        while not await self._port_open(self._host, CONTROL_PORT, self._poll_interval):
            if time.monotonic() >= deadline:
                raise ServiceUnavailableError(
                    f"The Fire TV at {self._host} did not start its remote service"
                )
            await asyncio.sleep(self._poll_interval)

    def _control(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Request:
        return Request(
            method,
            f"https://{self._host}:{CONTROL_PORT}{path}",
            self._headers(),
            json,
            verify_tls=False,  # the device presents a self-signed certificate
        )

    def _headers(self) -> dict[str, str]:
        headers = {"X-Api-Key": API_KEY, "User-Agent": USER_AGENT}
        if self._token:
            headers["X-Client-Token"] = self._token
        return headers

    async def _command(self, request: Request) -> Response:
        """Send a request the device must accept, refusing to infer success."""
        response = await self._send(request)
        if not response.ok:
            raise CommandRejectedError(
                f"The Fire TV refused {request.url} ({response.status})"
            )
        return response

    async def _send(self, request: Request) -> Response:
        try:
            return await self._transport(request)
        except (OSError, asyncio.TimeoutError, aiohttp.ClientError) as exc:
            raise ServiceUnavailableError(
                f"The Fire TV at {self._host} did not answer"
            ) from exc
