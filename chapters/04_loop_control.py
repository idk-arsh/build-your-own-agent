"""Chapter 4: loop control and cost. Prose in 04_loop_control.md.

Chapter 3 made the loop hard to kill. This chapter makes it stop. Three exits
that are not "the model said it was done": a cap on turns, a cap on dollars
computed from the usage numbers the API returns, and a detector for the model
asking for the same thing with the same arguments over and over.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
MODEL = os.environ.get("MODEL", "claude-opus-5")
ROOT = Path.cwd().resolve()

# The three limits. Every one of them is a guess about how much you are willing
# to lose to a run that is not going anywhere. Set them low and raise them when
# a real task hits one for a good reason.
MAX_TURNS = int(os.environ.get("MAX_TURNS", "20"))  # API calls per run
MAX_USD = float(os.environ.get("MAX_USD", "0.50"))  # dollars per run
MAX_REPEATS = 2  # identical tool calls tolerated before the run is declared a cycle

# List price for the default model at the time of writing, dollars per million
# tokens. Check the price page; this number goes stale and the loop trusts it.
PRICE_IN, PRICE_OUT = 5.00, 25.00

Message = dict[str, Any]

# --- Tools (chapter 3's file tools, unchanged) -----------------------------

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


def _inside_root(relative: str) -> None:
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
    with open(path, encoding="utf-8") as handle:
        return handle.read()


TOOLS: dict[str, Callable[..., str]] = {"list_files": list_files, "read_file": read_file}

# --- The loop, with three ways out ----------------------------------------


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
    """Chapter 3's never-raising tool runner."""
    name, arguments = block["name"], block["input"]
    try:
        if name not in TOOLS:
            raise LookupError(f"unknown tool {name!r}. The tools are: {', '.join(TOOLS)}")
        output = TOOLS[name](**arguments)
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


def cost_usd(usage: dict[str, int]) -> float:
    """What one reply cost, from the token counts the API returned with it."""
    return (usage["input_tokens"] * PRICE_IN + usage["output_tokens"] * PRICE_OUT) / 1_000_000


def run(task: str) -> None:
    messages: list[Message] = [{"role": "user", "content": task}]
    spent = 0.0
    seen: Counter[tuple[str, str]] = Counter()  # (tool name, canonical arguments) -> times asked

    for turn in range(1, MAX_TURNS + 1):
        reply = call_model(messages)
        spent += cost_usd(reply["usage"])
        messages.append({"role": "assistant", "content": reply["content"]})
        for block in reply["content"]:
            if block["type"] == "text":
                print(block["text"])
        usage = reply["usage"]
        print(
            f"[turn {turn}: {usage['input_tokens']} in, {usage['output_tokens']} out, ${spent:.4f}]"
        )

        if reply["stop_reason"] != "tool_use":
            print(f"[done: {turn} turns, ${spent:.4f}]")  # Exit 0: the model finished.
            return
        if spent >= MAX_USD:
            print(f"[stopped: ${spent:.4f} spent, cap is ${MAX_USD:.2f}]")  # Exit 1: money.
            return

        results: list[Message] = []
        for block in reply["content"]:
            if block["type"] != "tool_use":
                continue
            call = f"{block['name']}({json.dumps(block['input'])})"
            print(f"-> {call}")
            # Same tool, same arguments, sorted so key order does not hide a repeat.
            key = (block["name"], json.dumps(block["input"], sort_keys=True))
            seen[key] += 1
            if seen[key] > MAX_REPEATS:
                print(f"[stopped: cycle, {call} requested {seen[key]} times]")  # Exit 2: a loop.
                return
            if seen[key] > 1:
                # First repeat: tell the model, do not re-run the tool. Chapter 3's
                # lesson applies to the loop itself. This message is context too.
                note = f"repeat: you already called {call} and the result has not changed."
                print(f"   {note}")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": note,
                        "is_error": True,
                    }
                )
                continue
            results.append(run_tool(block))
        messages.append({"role": "user", "content": results})

    print(f"[stopped: turn cap of {MAX_TURNS} reached, ${spent:.4f} spent]")  # Exit 3: time.


if __name__ == "__main__":
    default = (
        "What does chapters/01_the_loop.py do? Look at the repo first. Answer in two sentences."
    )
    run(sys.argv[1] if len(sys.argv) > 1 else default)
