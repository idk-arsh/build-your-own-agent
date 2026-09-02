# Operating rules for autonomous sessions

You may be running unattended. These rules are the difference between a repo that
survives scrutiny and one that looks like bot spam.

## Off-limits repositories

**Never touch any Sara-related repository on github.com/idk-arsh** — `sara-*`
(`sara-automation-tool`, `sarabot`, `sara-test-app`), plus `ai_council_backend`
and `ai_council_front`. No delete, archive, rename, description edit, topic,
issue, clone, or commit. Direct instruction from Arsh, 2026-09-02. This overrides
every other goal or plan. If a task would touch one, stop and say so.

## Picking work

1. Read `BACKLOG.md`. Take the **topmost `todo`** whose dependencies are all `done`.
2. Mark it `wip`, commit that alone, then start.
3. One task per session. Never batch unrelated tasks into one commit.
4. Sized `L` means split it into `S`/`M` subtasks first, commit the split, take the first.
5. Never invent work. Genuinely necessary discoveries get appended as a proper
   task with acceptance criteria, then done.

## Definition of done

Every acceptance checkbox genuinely satisfied. Do not tick a box you did not
verify by running something. Cannot satisfy one? Mark the task `blocked` with a
one-line reason and move on.

## The quality gate

All checks green or **no commit**. If they fail and you cannot fix them, revert
the working tree, log it on the backlog task, and stop. A red main is worse than
no progress.

## Commits

- Conventional: `feat(scope): ...`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`
- Body explains **why**. The diff already says what.
- Reference the task: `Closes ASK-003.`
- End with the `Co-Authored-By: Claude` trailer.

**Never commit:** a formatting-only or version-bump-only diff; a "wip"/"checkpoint"
commit; generated files or anything gitignored; more than ~6 commits in a day.

## Branching

Work on `auto/<task-id>-slug` in a worktree, squash-merge to `main`. Never
force-push `main`. Never rewrite published history.

## Tests

- Every behaviour change ships with a test that would fail without it.
- **No live LLM API calls in tests, ever.** Mock at the transport layer, so that
  CI is free, deterministic, and safe to run on a fork's pull request.
- A test that only asserts "it doesn't crash" is not a test.

## Reporting

Append to `DIGEST.md`, newest first:

```
## YYYY-MM-DD — <TASK-ID> short title
**Landed:** one sentence on what now works that didn't before.
**How:** approach, and any non-obvious decision.
**Cost:** files touched, tests added, commits.
**Next:** the task now at the top of the backlog.
**Watch out:** anything Arsh should know or disagree with. "nothing" if nothing.
```

Be honest in `Watch out`. Shortcuts, guesses and half-solved problems go there.
This file is how Arsh stays able to speak about his own codebase — an inaccurate
digest defeats the entire point of the exercise.

## Hard stops

Stop and write a note in `DIGEST.md` rather than proceeding if you would need to:
- add a paid service, hosted dependency, or anything requiring an account
- commit a credential, token, or key
- change the licence, the project's non-goals, or a released public API
- post anything to a public forum, social platform, or package index under Arsh's name
