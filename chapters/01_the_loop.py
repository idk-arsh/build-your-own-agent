"""Chapter 1: the loop. Prose in 01_the_loop.md.

An agent is a list of messages and a loop that keeps appending to it. That is
the whole idea. Every later chapter is a refinement of these 50 lines.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Any

BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
MODEL = os.environ.get("MODEL", "claude-opus-5")

Message = dict[str, Any]


def call_model(messages: list[Message]) -> dict[str, Any]:
    """One HTTP request. The model sees exactly the list you send, nothing else."""
    body = {"model": MODEL, "max_tokens": 4096, "messages": messages}
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


def main() -> None:
    messages: list[Message] = []
    print("Type a message. Empty line or Ctrl-D quits.", flush=True)
    for line in sys.stdin:
        text = line.strip()
        if not text:
            break
        messages.append({"role": "user", "content": text})
        reply = call_model(messages)
        # Append the whole content list, not just the text. The model may return
        # more than one block, and it needs to see its own turn intact next time.
        messages.append({"role": "assistant", "content": reply["content"]})
        for block in reply["content"]:
            if block["type"] == "text":
                print(block["text"])
        tokens_in, tokens_out = reply["usage"]["input_tokens"], reply["usage"]["output_tokens"]
        print(f"[{len(messages)} messages | {tokens_in} in, {tokens_out} out]")


if __name__ == "__main__":
    main()
