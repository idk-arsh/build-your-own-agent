# Session digest

Newest first. Format in `CLAUDE.md`. The `Watch out` line must be honest.

---

## 2026-09-06 — BYOA-002 Chapter 1: the loop
**Landed:** The first real chapter. `chapters/01_the_loop.py` is a 58-line
conversation loop over raw HTTP with no dependencies, and CI executes it against
the mock with scripted stdin. The chapter-runner harness is now proven end to end,
which closes the caveat left open in the BYOA-001 digest.

**How:** Raw `urllib` rather than the SDK, on purpose: the chapter is about the
request shape, and an SDK would hide exactly the thing being taught. Model is read
from `MODEL` with `claude-opus-5` as the default. The reply's full content list is
appended back unchanged (thinking and tool blocks included), and only text blocks
are printed. The prose frames chapter 1 as a chatbot and the exercise as the step
that makes it an agent: the program, not the person, decides whether the loop
continues. The harness gained an optional `stdin` field in expectation files.

**Cost:** 3 files added, 2 edited, 1 test now exercises a real chapter, 2 commits
(wip marker plus the feature).

**Next:** BYOA-003 — Chapter 2: tools.

**Watch out:** Two things.
1. No API key was available in this session, so the chapter has not been run
   against the live API. The request shape follows the current Messages API
   reference and the mock speaks the same shape, but the first live run is still
   owed. The cost figure in the prose is arithmetic from list price and typical
   token counts, and the prose says so.
2. The prose is written without em dashes and without the usual filler, per
   Arsh's instruction on 2026-09-06. The README and ROADMAP still have them and
   get a docs pass this session.

## 2026-09-02 — BYOA-001 Repo skeleton and mock transport
**Landed:** The repo now has a working quality gate and can execute chapters
offline. `make check` runs ruff, mypy strict and pytest, all green. 6 tests pass.

**How:** The design problem was that chapters must run standalone (no imports from
this repo, so a reader can read every line that executes), which rules out a mock
library the chapters call. Solved it by making the mock a real HTTP server that
speaks the Messages API; chapters honour `ANTHROPIC_BASE_URL`. So a chapter runs
unchanged against either the real API or the mock, and CI needs no secret — which
also means a fork's pull request can run the full suite. Each chapter will declare
its scripted responses in `tests/expectations/<chapter>.json`, and a chapter
without one fails the suite deliberately, so code cannot drift from prose.

mypy is set to `files = ["."]` rather than an explicit list, so `chapters/` is
covered the moment chapter 1 lands instead of relying on someone remembering.

**Cost:** 8 files added, 6 tests, 1 commit. No runtime dependencies added — the
core stays dependency-free, which is the point of the project.

**Next:** BYOA-002 — Chapter 1: the loop.

**Watch out:** Three things.
1. The chapter-runner harness is self-tested but has **not executed a real
   chapter** — with zero chapters that assertion is vacuously true. It is only
   genuinely proven by BYOA-002. I ticked the box because the mechanism is built
   and tested; treat it as unverified end to end until chapter 1 lands.
2. The pre-commit hook originally called `ruff` from `PATH`, which fails when the
   tooling lives in a venv. Rewritten to prefer `.venv`. Verified it blocks a red
   commit (exit 1, nothing landed).
3. CI is now verified green: 10/10 jobs (lint+types, plus tests on
   ubuntu/macos/windows x py3.10/3.12/3.13). No secret required, so a fork's pull
   request gets real CI feedback.
