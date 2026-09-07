"""Chapter 3: errors and recovery. Prose in 03_errors.md.

Tools fail three ways: they raise, they get arguments they cannot accept, and
they hang. The loop survives all three the same way: it catches the failure,
turns it into text, and hands that text back to the model as a tool_result
marked is_error. Error text is context. The model reads it and tries again.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
MODEL = os.environ.get("MODEL", "claude-opus-5")
ROOT = Path.cwd().resolve()
TOOL_TIMEOUT = float(os.environ.get("TOOL_TIMEOUT", "10"))  # seconds

Message = dict[str, Any]

# --- Tools -----------------------------------------------------------------
# Chapter 2 wrote a polite refusal string for every failure it could think of.
# This chapter stops doing that. The tools raise, and the loop catches. Python's
# own exception messages are usually the best error text you will get.

TOOL_SCHEMAS = [
    {
        "name": "list_files",
        "description": "List the files in a directory, relative to the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {"directory": {"type": "string", "description": "Directory path"}},
            "required": ["directory"],
        },
    },
    {
        "name": "read_file",
        "description": "Return the contents of a text file, relative to the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Run a Python snippet in a fresh interpreter with the working directory as cwd. "
            f"Returns stdout. Killed after {TOOL_TIMEOUT:g} seconds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python source"}},
            "required": ["code"],
        },
    },
]


def _inside_root(relative: str) -> None:
    """Refuse anything outside the working directory. A policy decision, but still an error."""
    target = (ROOT / relative).resolve()
    if target != ROOT and ROOT not in target.parents:
        raise PermissionError(f"{relative!r} is outside the working directory")


def list_files(directory: str) -> str:
    _inside_root(directory)
    return "\n".join(
        sorted(p.name + ("/" if p.is_dir() else "") for p in Path(directory).iterdir())
    )


def read_file(path: str) -> str:
    _inside_root(path)
    with open(path, encoding="utf-8") as handle:  # A missing file raises. That message is useful.
        return handle.read()


def run_python(code: str) -> str:
    """Run model-written code. It is a subprocess because that is the only thing you can kill."""
    try:
        done = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT,
            cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"killed after {TOOL_TIMEOUT:g} seconds with no result. Does the code terminate?"
        ) from None
    if done.returncode != 0:
        raise RuntimeError(f"exit status {done.returncode}\n{done.stderr.strip()}")
    return done.stdout


TOOLS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "run_python": run_python,
}

# --- The loop, now unable to die on a bad tool call ------------------------


def call_model(messages: list[Message]) -> dict[str, Any]:
    body = {"model": MODEL, "max_tokens": 16000, "tools": TOOL_SCHEMAS, "messages": messages}
    request = urllib.request.Request(
        f"{BASE_URL}/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request) as response:
        reply: dict[str, Any] = json.load(response)
    return reply


def run_tool(block: Message) -> Message:
    """Run one tool_use request and return its tool_result. This function never raises.

    Whatever goes wrong, the model gets a tool_result back. A missing result
    breaks the conversation; an error result is just more context.
    """
    name, arguments = block["name"], block["input"]
    print(f"-> {name}({json.dumps(arguments)})")
    try:
        if name not in TOOLS:
            raise LookupError(f"unknown tool {name!r}. The tools are: {', '.join(TOOLS)}")
        output = TOOLS[name](**arguments)  # Bad argument names or types raise TypeError here.
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        print(f"   error: {error}")
        return {
            "type": "tool_result",
            "tool_use_id": block["id"],
            "content": error,
            "is_error": True,
        }
    return {"type": "tool_result", "tool_use_id": block["id"], "content": output}


def run(task: str) -> None:
    messages: list[Message] = [{"role": "user", "content": task}]
    while True:
        reply = call_model(messages)
        messages.append({"role": "assistant", "content": reply["content"]})
        for block in reply["content"]:
            if block["type"] == "text":
                print(block["text"])

        if reply["stop_reason"] != "tool_use":
            break

        results = [run_tool(block) for block in reply["content"] if block["type"] == "tool_use"]
        messages.append({"role": "user", "content": results})

    tokens_in, tokens_out = reply["usage"]["input_tokens"], reply["usage"]["output_tokens"]
    print(f"[{len(messages)} messages | last call: {tokens_in} in, {tokens_out} out]")


if __name__ == "__main__":
    default = "How many lines long is chapters/03_errors.py? Count with Python, do not guess."
    run(sys.argv[1] if len(sys.argv) > 1 else default)
