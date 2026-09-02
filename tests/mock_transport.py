"""A deterministic fake of the Anthropic Messages API.

Chapters must run standalone — no imports from this repository — so the mock
cannot be a library the chapters call. Instead it is a real HTTP server that
speaks the Messages API, and chapters honour ``ANTHROPIC_BASE_URL``. Point that
at the mock and a chapter runs unchanged, with no API key and no network.

That is why CI can execute every chapter for free, deterministically, and safely
on a fork's pull request.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

Block = dict[str, Any]
Response = dict[str, Any]

__all__ = [
    "MockServer",
    "mock_server",
    "text_response",
    "tool_use_response",
]


def text_response(text: str, *, stop_reason: str = "end_turn") -> Response:
    """A plain assistant turn containing one text block."""
    return {
        "id": "msg_mock_text",
        "type": "message",
        "role": "assistant",
        "model": "mock-model",
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 10, "output_tokens": len(text.split())},
    }


def tool_use_response(
    name: str,
    tool_input: dict[str, Any],
    *,
    tool_use_id: str = "toolu_mock",
    text: str | None = None,
) -> Response:
    """An assistant turn that requests a tool call.

    The model never executes anything itself — it emits this request and your
    code decides what to do with it. Chapter 2 exists to make that concrete.
    """
    content: list[Block] = []
    if text is not None:
        content.append({"type": "text", "text": text})
    content.append({"type": "tool_use", "id": tool_use_id, "name": name, "input": tool_input})
    return {
        "id": "msg_mock_tool",
        "type": "message",
        "role": "assistant",
        "model": "mock-model",
        "content": content,
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 12, "output_tokens": 8},
    }


class MockServer(ThreadingHTTPServer):
    """Replays a fixed script of responses, in order, and records what it was sent."""

    daemon_threads = True

    def __init__(self, script: Sequence[Response]) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.script: list[Response] = list(script)
        self.requests: list[dict[str, Any]] = []
        self._cursor = 0
        self._lock = threading.Lock()

    def next_response(self, request_body: dict[str, Any]) -> Response:
        with self._lock:
            self.requests.append(request_body)
            if self._cursor >= len(self.script):
                # Running past the script is a bug in the test, not in the agent.
                # Say so loudly rather than looping the last response forever.
                raise IndexError(
                    f"mock script exhausted: {len(self.script)} response(s) scripted, "
                    f"request {self._cursor + 1} received"
                )
            response = self.script[self._cursor]
            self._cursor += 1
            return response

    @property
    def base_url(self) -> str:
        host, port = self.server_address[0], self.server_address[1]
        if isinstance(host, bytes):  # pragma: no cover - platform dependent
            host = host.decode()
        return f"http://{host}:{port}"

    @property
    def call_count(self) -> int:
        with self._lock:
            return self._cursor


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        if not self.path.endswith("/v1/messages"):
            self._send_json(404, {"error": {"type": "not_found", "message": self.path}})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = cast(dict[str, Any], json.loads(raw or b"{}"))
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": {"type": "invalid_request_error", "message": str(exc)}})
            return

        server = cast(MockServer, self.server)
        try:
            payload = server.next_response(body)
        except IndexError as exc:
            self._send_json(500, {"error": {"type": "mock_exhausted", "message": str(exc)}})
            return

        self._send_json(200, payload)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        """Silence the default stderr access log; it is noise in test output."""


@contextmanager
def mock_server(script: Sequence[Response]) -> Iterator[MockServer]:
    """Run a mock API for the duration of the block.

    >>> with mock_server([text_response("hi")]) as server:
    ...     base_url = server.base_url
    """
    server = MockServer(script)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
