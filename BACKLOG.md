# Backlog — build-your-own-agent

Autonomous sessions pull the topmost `todo` whose deps are `done`. See `CLAUDE.md`.
One chapter per session, minimum. Never half a chapter.

**A chapter is `done` only when:** code runs, prose is written, exercise exists,
CI executes it against the mock transport, and the cost note is accurate.

---

### BYOA-001 — Repo skeleton and mock transport
**M0 · M · done**
- [x] `pyproject.toml`, ruff + mypy config, Python 3.10+
- [x] `tests/mock_transport.py`: a deterministic fake LLM that replays scripted responses including tool-use blocks
- [x] CI runs every `chapters/*.py` against the mock and asserts expected output
- [x] `make run CH=01` convenience target documented in README

Notes: the mock is an HTTP server speaking the Messages API, not a library, so
chapters stay standalone and still run offline via `ANTHROPIC_BASE_URL`. mypy is
configured with `files = ["."]` so `chapters/` is type-checked automatically as
soon as the first chapter lands. The chapter-runner harness is self-tested but has
not yet executed a real chapter — that happens in BYOA-002.

### BYOA-002 — Chapter 1: the loop
**M1 · M · done** — deps: BYOA-001
- [x] `chapters/01_the_loop.py` under 60 lines, runs against a real API key or the mock
- [x] Prose: why an agent is a while-loop; what the message list actually is
- [x] Exercise: make it stop when the model says "done" — no library
- [x] Stated cost to run: real number

Notes: 58 lines, stdlib only (`urllib`). The harness gained a `stdin` field in the
expectation file so interactive chapters can be driven in CI. Cost is computed
from the published price and the token counts the chapter prints, not measured
against a live key (no key available in the session).

### BYOA-003 — Chapter 2: tools
**M1 · M · todo** — deps: BYOA-002
- [ ] Tool schema by hand, dispatch table, results appended as tool-result messages
- [ ] Two real tools: read a file, do arithmetic
- [ ] Prose: the model emits a *request*, your code executes it — the single most misunderstood point
- [ ] Exercise: add a third tool without touching the loop

### BYOA-004 — Chapter 3: errors and recovery
**M1 · M · todo** — deps: BYOA-003
- [ ] Tool raises, returns malformed args, times out — agent survives all three
- [ ] Prose: error text is context; a good error message makes the model self-correct
- [ ] Exercise: make the agent fix its own bad argument

### BYOA-005 — Chapter 4: loop control and cost
**M1 · M · todo** — deps: BYOA-004
- [ ] Turn cap, USD cap, cycle detection on repeated tool+args
- [ ] Prose: why agents loop, with a real transcript of one doing it
- [ ] Exercise: trigger the cycle detector deliberately

### BYOA-006 — Chapter 5: memory
**M2 · M · todo** — deps: BYOA-005
- [ ] Truncation, then summarization; show token growth on a chart in the prose
- [ ] Prose: the arithmetic of why naive history is unaffordable
- [ ] Exercise: implement a memory policy that keeps cost flat over 50 turns

### BYOA-007 — Chapter 6: retrieval from scratch
**M2 · M · todo** — deps: BYOA-006
- [ ] Embeddings via API, cosine similarity in ~15 lines of numpy-free Python
- [ ] Prose: what a vector DB actually does, and when you need one (later than you think)
- [ ] Exercise: beat naive top-k with a chunking change

### BYOA-008 — Chapters 7-8: planning and subagents
**L — split before starting · todo** — deps: BYOA-007

### BYOA-009 — Chapter 9: MCP over stdio, no SDK
**M3 · M · todo** — deps: BYOA-007
- [ ] Speak JSON-RPC to a real MCP server directly; list tools, call one
- [ ] Prose: MCP demystified — it's JSON-RPC over a pipe
- [ ] Exercise: point it at a different MCP server unchanged

### BYOA-010 — Chapters 10-12: streaming, evaluation, web UI
**L — split before starting · todo** — deps: BYOA-009

### BYOA-011 — README and launch assets
**M4 · M · todo** — deps: BYOA-010
- [ ] README: the 40-line agent shown inline, in full, above the fold
- [ ] Chapter index with one-line hooks and difficulty
- [ ] Terminal-recording GIF of chapter 1 running
- [ ] Cross-link to `agent-starter-kit` (the production version) and `tracepoint` (testing it)
