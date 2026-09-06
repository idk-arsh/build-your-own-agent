"""Executes every chapter against the mock API.

Acceptance rule for the whole repo: a chapter that CI cannot run is not done.
Each ``chapters/NN_name.py`` needs a matching ``tests/expectations/NN_name.json``
declaring the scripted API responses, what to feed the chapter on stdin, and
what it must print. A chapter without one fails here deliberately. That is what
stops chapters rotting.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.mock_transport import Response, mock_server, text_response, tool_use_response

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = REPO_ROOT / "chapters"
EXPECTATIONS_DIR = Path(__file__).resolve().parent / "expectations"

CHAPTERS = sorted(CHAPTERS_DIR.glob("[0-9][0-9]_*.py"))


def _build_script(entries: list[dict[str, Any]]) -> list[Response]:
    script: list[Response] = []
    for entry in entries:
        kind = entry.get("type")
        if kind == "text":
            stop_reason = entry.get("stop_reason", "end_turn")
            script.append(text_response(entry["text"], stop_reason=stop_reason))
        elif kind == "tool_use":
            script.append(
                tool_use_response(
                    entry["name"],
                    entry.get("input", {}),
                    tool_use_id=entry.get("id", "toolu_mock"),
                    text=entry.get("text"),
                )
            )
        else:
            raise ValueError(f"unknown scripted response type: {kind!r}")
    return script


def test_chapters_directory_exists() -> None:
    assert CHAPTERS_DIR.is_dir(), "chapters/ must exist"


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda p: p.stem)
def test_chapter_runs_against_mock(chapter: Path) -> None:
    expectation_file = EXPECTATIONS_DIR / f"{chapter.stem}.json"
    assert expectation_file.is_file(), (
        f"{chapter.name} has no {expectation_file.name}. Every chapter must be "
        f"executable by CI — add the expectation file."
    )

    expectation = json.loads(expectation_file.read_text(encoding="utf-8"))
    script = _build_script(expectation["script"])

    with mock_server(script) as server:
        env = {
            **os.environ,
            "ANTHROPIC_BASE_URL": server.base_url,
            "ANTHROPIC_API_KEY": "mock-key-not-real",
            "PYTHONIOENCODING": "utf-8",
        }
        completed = subprocess.run(
            [sys.executable, str(chapter)],
            input=expectation.get("stdin", ""),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            cwd=REPO_ROOT,
        )
        calls = server.call_count

    assert completed.returncode == 0, (
        f"{chapter.name} exited {completed.returncode}\n"
        f"--- stdout ---\n{completed.stdout}\n--- stderr ---\n{completed.stderr}"
    )

    for fragment in expectation.get("expect_stdout", []):
        assert fragment in completed.stdout, (
            f"{chapter.name} did not print {fragment!r}\n--- stdout ---\n{completed.stdout}"
        )

    if "expect_calls" in expectation:
        assert calls == expectation["expect_calls"], (
            f"{chapter.name} made {calls} API call(s), expected {expectation['expect_calls']}"
        )
