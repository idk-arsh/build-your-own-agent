# Chapter 2: tools

**Code:** [`02_tools.py`](02_tools.py), 125 lines, no dependencies.
**Run:** `ANTHROPIC_API_KEY=sk-... python chapters/02_tools.py "what is in the tests directory?"`
**Cost:** a three-call run like the one below is under 5 cents. Details at the bottom.

## What you are building

The chapter 1 loop, plus two things the model can ask for: a directory listing
and the contents of a file. Give it a question about this repository and it will
go and look, then answer. That is a small coding agent, and the loop that drives
it is the same one you already have.

## The point of the chapter

**The model cannot run anything.** Not a function, not a shell command, not a
file read. It produces text, and one kind of text it can produce is a structured
request: "call `read_file` with `path` set to `chapters/01_the_loop.py`". That
request arrives in your program as a block of JSON. Nothing happens unless your
code reads the block and does something.

This is the most misunderstood thing about agents. When a demo shows a model
"browsing the web" or "running code", what you are watching is a program that
received a request, ran it, and appended the result to the list. The model
suggested. The program acted. Every safety property of the system lives in the
program, because the program is the only thing with hands.

Read `run()` with that in mind. The tool call happens on one line:

```python
output = TOOLS[block["name"]](**block["input"])
```

That line is yours. You can log it, refuse it, ask a human first, run it in a
sandbox, rate-limit it, or rewrite the arguments. The model finds out what you
chose when it reads the result.

## A tool is a schema and a function

Look at `TOOL_SCHEMAS`. Each entry has a name, a description, and a JSON schema
for the input. That is everything the model ever learns about the tool. The
description is doing real work: it is the only thing telling the model when to
reach for this tool rather than guessing. Write it for a reader who has never
seen your code.

The functions `list_files` and `read_file` are ordinary Python. The model never
sees them. The connection between the schema and the function is `TOOLS`, a
plain dictionary from name to callable. That is the dispatch table. It exists so
that the loop can stay ignorant of which tools exist.

## The loop grows one branch

Compare `run()` with chapter 1. Three things changed.

1. **The request carries `tools`.** The schemas go in the body next to
   `messages`. The model can now answer with `tool_use` blocks.

2. **The exit is `stop_reason`.** Chapter 1 stopped when the human stopped
   typing. This loop stops when the model stops asking: any `stop_reason` other
   than `tool_use` means it has produced an answer.

3. **Results go back as a `user` message.** For every `tool_use` block, your
   code appends a `tool_result` block carrying the same `id` and the string
   your function returned. All of them go into one user message. If the model
   asked for two things at once, they both come back at once. Split them across
   two messages and the model learns not to ask for things in parallel.

Nothing else moved. The message list, the append, the request: same as before.
The model's turn and the tool result are just two new kinds of entry in the list.

## Your code is the gate

Both tools call `_inside_root()` before touching the disk. A path that resolves
outside the working directory gets a refusal string back, not a file.

This is not paranoia about the model. It is the shape of the whole system. The
model will one day ask for `../../.ssh/id_rsa`, not because it is malicious but
because someone put that string in a file it read, or because it is confused.
The refusal costs three lines and turns a security problem into a log line.

Notice that the refusal is a normal tool result. The model reads "refused: ...",
understands it was told no, and usually tries something else. Chapter 3 is
entirely about that: what to put in a result when things go wrong, so the model
can recover instead of dying.

## Run it

```
$ python chapters/02_tools.py
Let me look at the repository first.
-> list_files({"directory": "chapters"})
-> read_file({"path": "chapters/01_the_loop.py"})
It is a conversation loop over the Messages API. Each turn appends to a list
and re-sends it.
[6 messages | last call: 1840 in, 61 out]
```

Three API calls, six messages. Each `->` line is a request the model made and
your code chose to honour. Try a question that needs a file outside the repo and
watch the refusal come back.

## What it costs

Same prices as chapter 1: $5 per million input tokens, $25 per million output.

Tools cost input tokens twice over. The schemas are sent on every call, and
every file the model reads is re-sent on every later call because it is now
part of the history. Reading `01_the_loop.py` puts about 600 tokens into the
list permanently. The run above sends roughly 4,000 input tokens in total across
three calls and gets back under 200 output tokens plus whatever the model thinks
before each one. Call it 3 to 5 cents.

The lesson to take from the arithmetic: a tool that returns a big result is
expensive forever, not once. Chapter 5 is about that.

## Exercise: add a third tool without touching the loop

Add `search_files(pattern, directory)`: return every line in every file under
`directory` that contains `pattern`, formatted as `path:line: text`. Reuse
`_inside_root()`.

Rules: one new schema in `TOOL_SCHEMAS`, one new function, one new entry in
`TOOLS`. `run()` and `call_model()` must not change. If you find yourself
editing the loop, the tool is doing something the loop should not know about.

Then ask it: "Which chapter files mention stop_reason?" and watch what it does.
It will probably search first and read second. It might read first. The order is
its decision, and the loop does not care.

## Where this goes next

Right now every tool succeeds or refuses politely. Chapter 3 makes them raise,
return garbage, and hang, and teaches the loop to survive all three.
