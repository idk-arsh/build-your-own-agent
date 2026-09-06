# Chapter 4: loop control and cost

**Code:** [`04_loop_control.py`](04_loop_control.py), 185 lines, no dependencies.
**Run:** `ANTHROPIC_API_KEY=sk-... python chapters/04_loop_control.py "what does chapters/02_tools.py do?"`
**Cost:** a run that trips the cycle detector, like the one below, is under a cent.
The defaults let a single run spend at most about 60 cents. Details at the bottom.

## What you are building

The chapter 3 agent with three ways to stop that do not depend on the model
deciding it is finished: a cap on the number of API calls, a cap on dollars, and
a detector for the model asking for the same thing with the same arguments over
and over. The tools are chapter 3's two file tools. `run_python` is left out to
keep the file short; nothing here cares which tools exist.

## The point of the chapter

**Why agents loop.** Chapters 1 to 3 built a loop with exactly one exit: the
model stops asking for tools. Everything in it is designed to keep going. Chapter
3 made sure a failing tool could not stop it. So what does stop it?

Nothing, if the model does not. And the model has two blind spots that make
that a real problem.

First, the model does not remember trying. It has the history, and it reads the
history, but every turn is a fresh decision made by a system that has never
lived through the previous turns. If reading a file did not answer the question,
"read the file" still looks like the best next move, because it did last time.
Given a tool result that changes nothing, the model will often ask for it again.
Then again.

Second, the model never sees the bill. `usage` comes back in every reply and
the model is not shown it. Your loop is the only part of the system that knows
what this run has cost so far, so your loop is the only thing that can stop it
for that reason.

Both blind spots are yours to cover. Three lines of budget and a dictionary do
it.

## Three exits

Read `run()`. The `while True` from earlier chapters is now
`for turn in range(1, MAX_TURNS + 1)`. That is the first exit, and the crudest:
after twenty API calls the run ends whatever state it is in. It is the exit you
hope never fires, because it means the other two did not.

The second exit is money. `cost_usd()` turns one reply's `usage` into dollars
using two constants, the list price per million input and output tokens. After
each reply the loop adds that to `spent` and, if the model wants to go on,
checks it against `MAX_USD` before running any tools. Running tools for a turn
you are not going to send is waste.

Two things to know about the dollar cap. It is computed, not measured: the price
constants are copied from the price page and they go stale. When the price
changes, this loop is wrong until you edit two numbers, and it will not tell
you. And it counts input tokens at full price, which is right for this book and
pessimistic for a production system that uses prompt caching. Pessimistic is the
correct direction for a cap.

The third exit is the one that fires because of what the agent did rather than
how long it took. `seen` is a `Counter` keyed on the tool name and its
arguments, with the arguments serialised through `json.dumps(..., sort_keys=True)`
so that `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` count as the same request.
Every tool call increments its key. The first repeat does not run the tool. It
returns a result that says, in plain words, that the model already asked for
this and the answer has not changed, flagged `is_error` exactly as chapter 3
would flag a crash. That message is context. A model that reads it usually does
something else. One that asks a third time has stopped listening, and the run
ends.

This is right for tools that only read. It is wrong for tools that change the
world: read a file, edit it, read it again is not a cycle, it is how editing
works. When you add tools with side effects, either reset `seen` when one runs
or key the detector on the tool result as well as the request. Chapter 7 will
need that.

One detail. When the cycle exit fires, the final `tool_use` block never gets a
`tool_result`. That is fine, because nothing is sent again. If you wanted to
continue the conversation instead of ending it, say to ask a human, you would
have to answer that block first. The protocol rule from chapter 3 still holds.

## Run it

The mock is scripted to ask for the same file three times. This is the
transcript the chapter is named for.

```
$ python chapters/04_loop_control.py
I will read chapter 1.
[turn 1: 12 in, 8 out, $0.0003]
-> read_file({"path": "chapters/01_the_loop.py"})
Let me read it again to be sure.
[turn 2: 12 in, 8 out, $0.0005]
-> read_file({"path": "chapters/01_the_loop.py"})
   repeat: you already called read_file({"path": "chapters/01_the_loop.py"}) and the result has not changed.
I need to check the file once more.
[turn 3: 12 in, 8 out, $0.0008]
-> read_file({"path": "chapters/01_the_loop.py"})
[stopped: cycle, read_file({"path": "chapters/01_the_loop.py"}) requested 3 times]
```

Read the model's three text lines on their own. Each one sounds reasonable.
None of them is wrong, exactly. That is what a loop looks like from the inside:
a sequence of individually sensible decisions that add up to nothing. The loop
cannot be seen from any single turn. It can only be seen by something that
remembers the turns, which is your code.

The second turn got the nudge and the third ignored it, so the run stopped
without spending a fourth call. With the token counts the mock reports that
saved nothing worth mentioning. With real token counts the third call would have
re-sent the whole file, and every call after it would have too.

Here is the dollar cap, with the mock scripted to report a reply of 1,000 input
and 300 output tokens and the cap set to one cent:

```
$ MAX_USD=0.01 python chapters/04_loop_control.py
Let me look at the repository first.
[turn 1: 1000 in, 300 out, $0.0125]
[stopped: $0.0125 spent, cap is $0.01]
```

1,000 input tokens at $5 per million is half a cent, 300 output tokens at $25
per million is three quarters of a cent, and the first reply has already spent
$0.0125 against a cap of $0.01. The tool the model asked for is never run. The
turn cap works the same way with `MAX_TURNS=2`; the test suite runs all three
exits and the normal finish against the mock.

## What it costs

Same prices: $5 per million input tokens, $25 per million output.

The interesting number is the worst case, which is what the caps are for. Say
each turn adds about 500 tokens to the history (a tool call, a file, a reply).
Then turn 1 sends about 500 input tokens, turn 2 about 1,000, and turn 20 about
10,000, because the whole history goes every time. That is 105,000 input tokens
over 20 turns, or 52 cents, plus about 3,000 output tokens, or 8 cents. Roughly
60 cents for a run that hits the turn cap. With `MAX_USD` at 50 cents, the dollar
cap fires first, around turn 19. That is deliberate. The turn cap is a guess
about cost. The dollar cap is the cost.

Now put the cycle transcript against that arithmetic. A model re-reading the
same 600-token file twenty times would spend the whole budget and learn
nothing. The detector ends it on the third request, for under a cent. Of the
three exits it is the only one that saves money rather than merely limiting the
loss.

## Exercise: trigger the cycle detector on purpose

You need a model that repeats itself, and a good model rarely does on a task it
can complete. So give it one it cannot.

1. Make `read_file` return the empty string for every file. Leave the schema
   and the loop alone. The model now asks for a file, gets nothing, and has to
   decide what to do with nothing.
2. Run it live: `python chapters/04_loop_control.py "What does chapters/01_the_loop.py do?"`.
   Watch what it does when the file comes back empty. It may list the directory,
   it may read the file again, it may read a different file. Run it three times
   and count how often the `repeat:` nudge appears and how often the cycle exit
   fires.
3. Raise `MAX_REPEATS` to 5 and run again. Note what the extra turns cost and
   whether the model ever did anything useful with them.
4. Put `MAX_REPEATS` back. Now set `MAX_USD=0.002` (a fifth of a cent) and run
   once more. Which exit fires first, and on which turn?

Rules: one function body changes in step 1, one constant in step 3, one
environment variable in step 4. `run()` does not change.

When you are done, answer this: in a well-configured agent, which of the three
exits should fire most often? The cycle detector, because it fires on evidence
that the run is stuck. The other two fire on time and money running out, which
is evidence only that nothing else noticed.

## Where this goes next

Look at the worst-case arithmetic again. Almost all of the 60 cents is input
tokens, and almost all of the input tokens are the history being sent again and
again. The caps in this chapter stop the bleeding. Chapter 5 slows it down: what
to keep, what to drop, and what to summarise, so that a long run costs a flat
amount per turn instead of a growing one.
