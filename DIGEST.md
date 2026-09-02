# Session digest

Newest first. Format in `CLAUDE.md`. The `Watch out` line must be honest.

---

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
