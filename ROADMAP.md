# Build Your Own Agent

**Build a production-capable AI agent from scratch in 12 chapters. No frameworks.**

Every chapter is a runnable Python file under 200 lines, a written explanation of
*why*, and an exercise. By chapter 12 the reader has written, by hand, an agent
with tool use, memory, planning, retrieval, MCP support, and a web UI.

## Why this exists

Agent frameworks hide the thing worth understanding. People `pip install` a
framework, get a working demo, and still cannot answer why their agent loops
forever or burns $4 on one request. The fastest way to actually understand agents
is to write the loop yourself, and the loop is smaller than people think. The
first working version is 58 lines.

Precedent: `nanochat` proved that a well-written from-scratch teaching repo
outperforms most tools on reach. The from-scratch genre works because forking is
the usage: you fork it to work through it.

## Chapters

1. **The loop.** 58 lines: message list, API call, print. Why an agent is a while-loop.
2. **Tools.** Tool schemas, dispatch, feeding results back. Why the model can't call anything itself.
3. **Errors.** Tool failures, malformed args, retries. The agent that recovers vs. the one that dies.
4. **Loop control.** Turn limits, cost limits, cycle detection. Why your agent repeats itself.
5. **Memory.** Short-term truncation, summarization, why naive history growth bankrupts you.
6. **Retrieval.** Embeddings and cosine similarity from scratch, no vector DB.
7. **Planning.** Decomposition, plan-then-execute vs. ReAct, when each wins.
8. **Subagents.** Delegation, context isolation, result aggregation.
9. **MCP.** Speaking the Model Context Protocol directly over stdio. No SDK.
10. **Streaming.** Token streaming, partial tool calls, why UX forces architecture.
11. **Evaluation.** Testing a non-deterministic system. Assertions over traces.
12. **The web UI.** FastAPI + a single HTML file. Ship it.

## Design rules

- **Chapter N runs standalone.** No shared library the reader must read first.
- **Under 200 lines per chapter.** If it doesn't fit, the chapter is doing too much.
- **Standard library only.** `urllib` for HTTP. No framework, ever. That is the whole point.
- **Every chapter runs.** CI executes all 12 against a mock transport on every push.
- **Prose explains why.** Code shows what. A chapter without prose is not done.
- **Costs are stated.** Every chapter says what it costs to run against a real API.

## Non-goals

- Not a framework. If it becomes importable infrastructure, it has failed.
- Not provider-agnostic abstraction. Uses one provider clearly, notes the differences.
- Not exhaustive. 12 chapters that get read beat 40 that don't.
