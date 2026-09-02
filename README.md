# Build Your Own Agent

**Build a production-capable AI agent from scratch in 12 chapters. No frameworks.**

Every chapter is one runnable Python file under 200 lines, an explanation of *why*
it works that way, and an exercise. By chapter 12 you will have written — by hand —
an agent with tool use, memory, planning, retrieval, MCP support and a web UI.

Agent frameworks hide the thing worth understanding. People install one, get a
working demo, and still cannot say why their agent loops forever or burned $4 on a
single request. The loop is smaller than you think: the first working version is
about 40 lines.

> **Status: in progress.** Chapters are being written in order. See
> [`ROADMAP.md`](ROADMAP.md) for the full plan and [`BACKLOG.md`](BACKLOG.md) for
> what is being worked on now.

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

Run the test suite — **no API key needed, no network, free**:

```bash
make test
```

| Command | What it does |
|---|---|
| `make install` | Install dev tooling |
| `make run CH=01` | Run chapter 01 against the real API |
| `make test` | Run every chapter against the mock API |
| `make check` | Lint, type-check and test — the full gate |

## How the tests work without an API key

Chapters must run standalone — no imports from this repo, because you should be
able to read every line that executes. So the mock cannot be a library the
chapters call.

Instead, [`tests/mock_transport.py`](tests/mock_transport.py) is a real HTTP
server that speaks the Messages API, and chapters honour `ANTHROPIC_BASE_URL`.
Point that at the mock and a chapter runs unchanged, offline and free.

That is why CI can execute all 12 chapters on every push, and why a pull request
from a fork can run the full suite without a secret.

Each chapter has an expectation file in `tests/expectations/` declaring the
scripted API responses and what the chapter must print. **A chapter CI cannot run
is not finished** — that rule is what stops the code rotting away from the prose.

## Chapters

1. The loop · 2. Tools · 3. Errors · 4. Loop control · 5. Memory · 6. Retrieval ·
7. Planning · 8. Subagents · 9. MCP · 10. Streaming · 11. Evaluation · 12. Web UI

Full descriptions in [`ROADMAP.md`](ROADMAP.md).

## Licence

MIT
