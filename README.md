# Build Your Own Agent

**An AI agent from scratch in 12 chapters. No frameworks. Every chapter is one Python file you can read in full.**

Each chapter is a runnable file under 200 lines, a written explanation of why it
works that way, and an exercise. By the end you will have written, by hand, an
agent with tool use, error recovery, memory, retrieval, planning, subagents, MCP
support, streaming, evaluation and a web UI.

Frameworks hide the part worth understanding. People install one, get a demo
running, and still cannot say why their agent loops forever or spent $4 on one
request. The loop is smaller than it looks. The first working version is 58
lines, and 20 of those are the HTTP request.

> **Status: in progress.** Chapters 1 and 2 are done. Chapters are written in
> order, one at a time. [`ROADMAP.md`](ROADMAP.md) has the plan,
> [`BACKLOG.md`](BACKLOG.md) has what is being worked on now.

## Chapters

| # | Chapter | What you learn | Status |
|---|---|---|---|
| 1 | [The loop](chapters/01_the_loop.md) | An agent is a message list and a loop. The API has no memory; you keep the list. | done |
| 2 | [Tools](chapters/02_tools.md) | The model asks, your code acts. Schemas by hand, a dispatch table, the tool_result round trip. | done |
| 3 | Errors and recovery | Tools that raise, return garbage, or hang. Error text is context the model can act on. | next |
| 4 | Loop control and cost | Turn caps, dollar caps, cycle detection. Why agents repeat themselves. | |
| 5 | Memory | Truncation, then summarisation. The arithmetic of why naive history is unaffordable. | |
| 6 | Retrieval | Embeddings and cosine similarity in plain Python. When you need a vector database (later than you think). | |
| 7 | Planning | Decompose, then execute. Plan-first versus act-as-you-go, and when each wins. | |
| 8 | Subagents | Delegation, context isolation, collecting results. | |
| 9 | MCP | Speak the Model Context Protocol to a real server over stdio. JSON-RPC, no SDK. | |
| 10 | Streaming | Token streaming, partial tool calls, why the UI forces architecture decisions. | |
| 11 | Evaluation | Testing a system that gives different answers each run. Assertions over traces. | |
| 12 | The web UI | FastAPI and one HTML file. Ship it. | |

## Quickstart

```bash
git clone https://github.com/idk-arsh/build-your-own-agent
cd build-your-own-agent
make install
```

Run a chapter against the real API:

```bash
export ANTHROPIC_API_KEY=sk-...
make run CH=01
```

Run the whole test suite. No API key, no network, no cost:

```bash
make test
```

| Command | What it does |
|---|---|
| `make install` | Install the dev tooling (ruff, mypy, pytest). The chapters themselves need nothing. |
| `make run CH=01` | Run chapter 01 against the real API |
| `make test` | Run every chapter against the mock API |
| `make check` | Lint, type-check and test. The full gate. |

The default model is `claude-opus-5`. Set `MODEL` to use a different one. Each
chapter states what it costs to run.

## How the tests work without an API key

Chapters must run standalone, with no imports from this repository, so that you
can read every line that executes. That rules out a mock library the chapters
would call.

Instead, [`tests/mock_transport.py`](tests/mock_transport.py) is a real HTTP
server that speaks the Messages API, and the chapters read `ANTHROPIC_BASE_URL`.
Point that at the mock and a chapter runs unchanged, offline and free.

That is why CI executes every chapter on every push across three operating
systems and three Python versions, and why a pull request from a fork gets the
full suite without any secret.

Each chapter has an expectation file in [`tests/expectations/`](tests/expectations)
declaring the scripted API responses, the stdin to feed it, what it must print,
and which tool results it must send back. A chapter CI cannot run is not
finished. That rule is what keeps the code from drifting away from the prose.

## Design rules

- **Each chapter runs on its own.** No shared library to read first.
- **Under 200 lines.** If it does not fit, the chapter is doing too much.
- **Standard library only.** No agent framework, ever. That is the point.
- **Every chapter runs in CI.** Against the mock, on every push.
- **Prose explains why.** The code shows what.
- **Costs are stated.** Every chapter says what a run costs.

## Contributing

Corrections and clearer explanations are welcome. New chapters are not, until the
twelve are done. Run `make check` before opening a pull request; CI runs the same
thing.

## Licence

MIT
