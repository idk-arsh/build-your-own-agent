# Chapter 3: errors and recovery

**Code:** [`03_errors.py`](03_errors.py), 175 lines, no dependencies.
**Run:** `ANTHROPIC_API_KEY=sk-... python chapters/03_errors.py "how many lines is chapters/02_tools.py?"`
**Cost:** the six-call run below is 2 to 5 cents. Details at the bottom.

## What you are building

The chapter 2 agent, plus a third tool that runs Python, and a loop that cannot
be killed by a tool call. Ask it something that needs a bit of computation and it
will read, list, run code, get things wrong, and fix them. The getting-wrong is
the chapter.

Three things go wrong with tools, and this file survives all three:

1. **The tool raises.** A file is missing, a path is a directory, a snippet
   crashes. Python throws.
2. **The arguments are malformed.** The model invents a parameter name, or
   forgets a required one, or sends a number where a string goes. Python throws
   a `TypeError`, usually before your tool even runs.
3. **The tool hangs.** The model writes a loop that never ends, or asks for
   something that blocks forever. Nothing throws. Nothing happens.

## The point of the chapter

**Error text is context.** When a tool fails, the failure message is not a
problem to hide from the model. It is the most useful thing you can give it.

Look at what the loop does in `run_tool()` when a tool raises:

```python
error = f"{type(exc).__name__}: {exc}"
return {"type": "tool_result", "tool_use_id": block["id"], "content": error, "is_error": True}
```

The exception becomes a string. The string goes back to the model as an ordinary
tool result, with one flag set. The loop goes round again. That is the whole
recovery mechanism, and it works because the model reads
`TypeError: read_file() got an unexpected keyword argument 'file'` and does what
you would do: uses the right name.

Compare that to what most first agents do, which is nothing. The exception
propagates out of the loop, the process dies, and the model never finds out. Or
worse: the code catches the exception, logs it, and appends no `tool_result` at
all. The API rejects that conversation on the next call, because every
`tool_use` block must be answered. A missing result breaks the protocol. An error
result is just more history.

## One function that never raises

`run_tool()` is new. It takes one `tool_use` block and returns one `tool_result`,
and nothing that happens inside it can escape. Read the `try` block:

```python
if name not in TOOLS:
    raise LookupError(f"unknown tool {name!r}. The tools are: {', '.join(TOOLS)}")
output = TOOLS[name](**arguments)
```

Two of the three failure modes live on that second line. If `arguments` has a
key the function does not accept, `**arguments` raises `TypeError` with a message
that names the bad key. If the function runs and fails, it raises whatever it
raises. Both land in the same `except Exception`, and the model gets the class
name and the message.

Notice that it is `except Exception`, not `except BaseException`. A Ctrl-C is not
a tool failure. Let it through.

Notice also what the error message for an unknown tool contains: the list of
tools that do exist. A good error message says what would have worked. The model
will act on that immediately. A bare `KeyError: 'search_files'` makes it guess.

## The timeout lives in the tool

`run_python()` executes model-written code in a subprocess with a `timeout`. When
the time is up, `subprocess.run` kills the child and raises, and the tool turns
that into a `TimeoutError` whose message says how long it waited and asks the
obvious question.

The timeout is in the tool, not in the loop, and that is deliberate. Python
cannot kill a thread. If you wrapped every tool call in a thread and gave up
waiting after ten seconds, the tool would keep running in the background, using
CPU and possibly still writing to disk, while the model was told it had stopped.
A subprocess can actually be killed. So the rule is: put the timeout where the
work can be stopped. For a tool that runs code, that is a subprocess. For a
network call, it is the socket timeout. For a file read, you probably do not
need one.

`run_python` is also the first tool in this book that can do real damage. It
runs whatever the model writes, as you, in this directory, with no sandbox. Every
coding agent you have used does the same thing; the honest ones say so. Do not
point this chapter at a live model in a directory you have not committed. When
you build for real, run it in a container.

## Refusals are errors too

Chapter 2 returned `refused: ...` as ordinary text when a path escaped the
working directory. That was a small mistake. A model reading a tool result has
to decide whether it is looking at the file it asked for or at a message about
the file. Mostly it gets this right. Sometimes it does not, and then it
summarises the refusal as if it were the contents.

So `_inside_root()` now raises `PermissionError`, and the refusal comes back with
`is_error: true` like everything else. The policy has not changed. The model is
still told no. It is just told in a way it cannot mistake for a yes.

## Run it

The mock is scripted to make all three mistakes in one run, so you can see each
recovery. A real model makes them less often. Not never.

```
$ python chapters/03_errors.py
I will read the file first.
-> read_file({"file": "chapters/03_errors.py"})
   error: TypeError: read_file() got an unexpected keyword argument 'file'
-> read_file({"path": "chapters/03_error.py"})
   error: FileNotFoundError: [Errno 2] No such file or directory: 'chapters/03_error.py'
-> list_files({"directory": "chapters"})
The file is 03_errors.py. Counting its lines.
-> run_python({"code": "count = 0\nwith open('chapters/03_errors.py') as f:\n    line = f.readline()\n    while line:\n        count += 1\nprint(count)"})
   error: TimeoutError: killed after 10 seconds with no result. Does the code terminate?
That loop never advanced. Simpler:
-> run_python({"code": "with open('chapters/03_errors.py') as f:\n    print(sum(1 for _ in f))"})
chapters/03_errors.py is 175 lines long.
[12 messages | last call: 10 in, 5 out]
```

Six calls, twelve messages, three errors, one right answer. Read the three
`error:` lines and then the line after each one. Every recovery is the model
doing exactly what the error text told it. The wrong keyword became the right
keyword. The missing file became a directory listing. The loop that never
advanced became a one-liner. None of that is in the loop code. It is in the
messages.

That run takes ten seconds, and nine and a half of them are the third tool call
waiting to be killed. The test suite sets `TOOL_TIMEOUT=1` for the same script.

## What it costs

Same prices as before: $5 per million input tokens, $25 per million output.

Six calls. The three tool schemas go out on every one of them, about 250 tokens
a time, and the history grows from roughly 300 tokens on the first call to about
700 on the last. Call it 3,000 input tokens in total, plus about 200 output
tokens across the six replies, plus whatever the model thinks. That is a bit
under 2 cents before thinking and under 5 with it.

The number to notice: the three failed calls cost the same as the three
successful ones. A failure is not free because nothing happened. The request
still went out with the full history, and the reply still came back. This run
cost about twice what it would have cost had the model been right first time.
Error recovery is what makes agents work, and it is also where the money goes.
Chapter 4 puts a ceiling on it.

## Exercise: make the agent fix its own bad argument

In the run above the model recovered from a wrong keyword because Python's
`TypeError` happened to name the right one. Now make it harder, and then make
the loop help.

1. In `TOOL_SCHEMAS`, rename `list_files`'s property from `directory` to
   `folder`. Leave the function alone. You have shipped a schema that disagrees
   with the code, which you will one day do by accident.
2. Run it live with a question that needs a listing. The model does what the
   schema says, gets `TypeError: list_files() got an unexpected keyword argument
   'folder'`, and now has to work out what the function actually wants. Count the
   calls it takes to recover. Try three times; it will vary.
3. Now improve the error. In the `except` branch, when the exception is a
   `TypeError`, append the function's real parameter names to the message.
   `inspect.signature(TOOLS[name])` gives you them in one line.
4. Run it again and count again.

Rules: the tools and their schemas do not change (beyond the deliberate break in
step 1). Only the text in the `except` branch changes. One new import.

If the model now recovers in one retry, you have made the error text do the
schema's job, which is the point. When you write real tools, write the error
messages for a reader who has only the message: say what was wrong, and say what
would have been right.

## Where this goes next

Everything in this chapter makes the agent harder to kill. That has a cost. An
agent that survives every error can also fail forever, politely, one retry at a
time, at 5 dollars per million tokens. Chapter 4 gives it a budget and teaches it
to notice when it is going in circles.
