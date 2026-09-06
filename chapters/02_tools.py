"""Chapter 2: tools. Prose in 02_tools.md.

The model cannot run anything. It can only ask. Your code reads the request,
decides whether to honour it, runs it, and appends the result to the list.
Then the loop from chapter 1 goes round again.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
MODEL = os.environ.get("MODEL", "claude-opus-5")
ROOT = Path.cwd().resolve()

Message = dict[str, Any]

# --- Tools -----------------------------------------------------------------
# A tool is two things: a schema the model reads, and a function your code runs.
# The model never sees the function. Your code never shows the model anything
# but the schema and the string you return.

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
]


def _inside_root(relative: str) -> Path | None:
    """Resolve a model-supplied path and refuse anything outside the working directory."""
    target = (ROOT / relative).resolve()
    return target if target == ROOT or ROOT in target.parents else None


def list_files(directory: str) -> str:
    path = _inside_root(directory)
    if path is None or not path.is_dir():
        return f"refused: {directory!r} is not a directory inside the working directory"
    return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir()))


def read_file(path: str) -> str:
    target = _inside_root(path)
    if target is None or not target.is_file():
        return f"refused: {path!r} is not a file inside the working directory"
    return target.read_text(encoding="utf-8")


# The dispatch table. Adding a tool means one schema above and one entry here.
# The loop below does not change. That is the exercise.
TOOLS: dict[str, Callable[..., str]] = {"list_files": list_files, "read_file": read_file}

# --- The loop, now with a second kind of turn ------------------------------


def call_model(messages: list[Message]) -> dict[str, Any]:
    body = {"model": MODEL, "max_tokens": 4096, "tools": TOOL_SCHEMAS, "messages": messages}
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


def run(task: str) -> None:
    messages: list[Message] = [{"role": "user", "content": task}]
    while True:
        reply = call_model(messages)
        messages.append({"role": "assistant", "content": reply["content"]})
        for block in reply["content"]:
            if block["type"] == "text":
                print(block["text"])

        if reply["stop_reason"] != "tool_use":
            break  # The model is done asking. This is the only exit.

        # Every tool_use block gets exactly one tool_result, all in ONE user
        # message. Splitting them across messages breaks parallel tool calls.
        results: list[Message] = []
        for block in reply["content"]:
            if block["type"] != "tool_use":
                continue
            print(f"-> {block['name']}({json.dumps(block['input'])})")
            output = TOOLS[block["name"]](**block["input"])
            results.append({"type": "tool_result", "tool_use_id": block["id"], "content": output})
        messages.append({"role": "user", "content": results})

    tokens_in, tokens_out = reply["usage"]["input_tokens"], reply["usage"]["output_tokens"]
    print(f"[{len(messages)} messages | last call: {tokens_in} in, {tokens_out} out]")


if __name__ == "__main__":
    default = (
        "What does chapters/01_the_loop.py do? Look at the repo first. Answer in two sentences."
    )
    run(sys.argv[1] if len(sys.argv) > 1 else default)
