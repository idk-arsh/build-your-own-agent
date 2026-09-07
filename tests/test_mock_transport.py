"""Tests for the mock itself.

The mock is test infrastructure every chapter depends on, so a bug here would
silently invalidate the whole suite. It gets tested like production code.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from tests.mock_transport import mock_server, text_response, tool_use_response


def _post(base_url: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        parsed: dict[str, Any] = json.loads(response.read())
        return parsed


def test_replays_scripted_responses_in_order() -> None:
    script = [text_response("first"), text_response("second")]
    with mock_server(script) as server:
        assert _post(server.base_url, {"messages": []})["content"][0]["text"] == "first"
        assert _post(server.base_url, {"messages": []})["content"][0]["text"] == "second"
        assert server.call_count == 2


def test_records_request_bodies() -> None:
    with mock_server([text_response("ok")]) as server:
        _post(server.base_url, {"model": "x", "messages": [{"role": "user", "content": "hello"}]})
        assert server.requests[0]["messages"][0]["content"] == "hello"


def test_tool_use_response_shape() -> None:
    script = [tool_use_response("read_file", {"path": "a.txt"}, text="let me look")]
    with mock_server(script) as server:
        payload = _post(server.base_url, {"messages": []})

    assert payload["stop_reason"] == "tool_use"
    blocks = payload["content"]
    assert blocks[0]["type"] == "text"
    assert blocks[1] == {
        "type": "tool_use",
        "id": "toolu_mock",
        "name": "read_file",
        "input": {"path": "a.txt"},
    }


def test_scripted_usage_overrides_the_default_token_counts() -> None:
    expensive = {"input_tokens": 1000, "output_tokens": 300}
    script = [text_response("pricey", usage=expensive), tool_use_response("t", {}, usage=expensive)]
    with mock_server(script) as server:
        assert _post(server.base_url, {"messages": []})["usage"] == expensive
        assert _post(server.base_url, {"messages": []})["usage"] == expensive


def test_default_usage_is_present_when_not_scripted() -> None:
    with mock_server([text_response("two words")]) as server:
        usage = _post(server.base_url, {"messages": []})["usage"]
    assert usage == {"input_tokens": 10, "output_tokens": 2}


def _error_body(exc: urllib.error.HTTPError) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads(exc.read())
    return parsed


def test_exhausted_script_is_a_loud_error_not_a_silent_loop() -> None:
    with mock_server([text_response("only one")]) as server:
        _post(server.base_url, {"messages": []})
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            _post(server.base_url, {"messages": []})
        assert excinfo.value.code == 500
        assert _error_body(excinfo.value)["error"]["type"] == "api_error"


def test_unknown_path_is_404() -> None:
    with mock_server([text_response("x")]) as server:
        request = urllib.request.Request(f"{server.base_url}/v1/nope", data=b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request, timeout=5)
        assert excinfo.value.code == 404
        assert _error_body(excinfo.value)["error"]["type"] == "not_found_error"


def test_errors_use_the_documented_envelope() -> None:
    """Errors look like the real API's: {"type": "error", "error": {type, message}, request_id}.

    A chapter that learns to read errors against the mock must not learn a
    shape the live API does not send.
    """
    with mock_server([text_response("x")]) as server:
        request = urllib.request.Request(
            f"{server.base_url}/v1/messages", data=b"not json", method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request, timeout=5)
    assert excinfo.value.code == 400
    body = _error_body(excinfo.value)
    assert body["type"] == "error"
    assert body["error"]["type"] == "invalid_request_error"
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]
    assert body["request_id"].startswith("req_")


def test_error_responses_read_the_request_body_first() -> None:
    """Regression for the intermittent ConnectionAbortedError on Windows.

    Answering before the request body is consumed leaves unread bytes on the
    socket; when the handler then closes it, the client sees a reset instead
    of our response. It reproduced in roughly 1 in 20 requests with a 64 KB
    body, so 100 requests catch a regression with high probability.
    """
    body = b"{" + b" " * 65536 + b"}"
    with mock_server([text_response("x")]) as server:
        for _ in range(100):
            request = urllib.request.Request(f"{server.base_url}/v1/nope", data=body, method="POST")
            with pytest.raises(urllib.error.HTTPError) as excinfo:
                urllib.request.urlopen(request, timeout=5)
            assert excinfo.value.code == 404
