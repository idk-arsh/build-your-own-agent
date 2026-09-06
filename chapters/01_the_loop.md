# Chapter 1: the loop

**Code:** [`01_the_loop.py`](01_the_loop.py), 58 lines, no dependencies.
**Run:** `ANTHROPIC_API_KEY=sk-... python chapters/01_the_loop.py`
**Cost:** a short conversation is a few cents. Details at the bottom.

## What you are building

A program that holds a conversation with a model. You type, it answers, you type
again, and it remembers what was said. By the end of the chapter you will know
exactly why it remembers, because you will have built the memory yourself, and
it is a Python list.

Nothing in this file is imported from anywhere in this repository. Read it top to
bottom and you have read every line that runs.

## The message list is the agent

Look at `main()`. There is one piece of state:

```python
messages: list[Message] = []
```

Everything else is a loop that appends to it. Your turn goes on as a `user`
message. The model's reply goes on as an `assistant` message. Then the whole list
is sent again.

That last part is the thing people get wrong. The API has no memory. There is no
session, no conversation id, nothing on the server that remembers you. Each
request is complete in itself: here is the model name, here is the full history,
give me the next turn. If you dropped a message from the list, the model would
never know it existed. If you edited one, the model would believe the edited
version.

So "the agent remembers" means "your code kept the list". Chapter 5 is about what
to do when that list gets too long to afford. Everything in between is about what
else you append to it.

## One request

`call_model()` is one HTTP POST. The body has three fields:

| Field | What it is |
|---|---|
| `model` | Which model answers. Read from `MODEL` so you can switch without editing code. |
| `max_tokens` | Hard ceiling on the reply length. The model does not know about it; it just gets cut off. |
| `messages` | The list. Alternating `user` and `assistant`, starting with `user`. |

Three headers: the content type, your key, and an API version date. That is the
entire protocol for this chapter. When you use an SDK later, this is what it is
doing underneath.

## Why the reply is a list too

```python
messages.append({"role": "assistant", "content": reply["content"]})
```

`reply["content"]` is a list of blocks, not a string. In this chapter you will
mostly see one block of type `text`. Some models also return a `thinking` block
first, and from chapter 2 onwards you will see `tool_use` blocks.

The code appends the whole list, unchanged, and only prints the `text` blocks.
Keep it that way. The model needs to see its own previous turn exactly as it
produced it. Flattening it to a string works today and breaks the moment a
non-text block shows up.

## The line that makes it an agent

Right now a human decides whether the loop continues, by typing another line or
not. That makes this a chatbot.

An agent is the same loop where the program decides. In chapter 2 the model will
ask your code to do something, your code will do it and append the result, and
the loop will go round again without anyone typing. The list, the request, and
the append are identical. Only the source of the next `user` message changes.

Hold on to that. When a framework talks about "agent runtimes" and "execution
engines", this loop is what it is wrapping.

## Run it

```
$ python chapters/01_the_loop.py
Type a message. Empty line or Ctrl-D quits.
hello
Hello. What can I do for you?
[2 messages | 9 in, 11 out]
what did I just say?
You said hello.
[4 messages | 31 in, 6 out]
```

Watch the first number in brackets. It grows by two every turn, and the `in`
token count grows with it, because the whole history is sent every time. That
growth is the cost problem chapter 5 solves.

## What it costs

Prices for the default model at the time of writing: $5 per million input
tokens, $25 per million output tokens.

A ten-turn conversation with short messages sends roughly 3,000 input tokens in
total (the history is re-sent each turn, so it adds up) and gets back about
1,000 output tokens. That is about 4 cents. Output tokens include any thinking
the model does before answering, so a question that makes it think costs more
than one that does not.

The token counts are printed after every turn. Do not trust this paragraph;
trust the numbers on your screen and the price page.

## Exercise: let the program decide when to stop

Change the loop so no human is needed. Seed the list with one instruction:

> Count from 1 to 5, one number per reply. When you have said 5, reply with
> exactly the word DONE.

Then, instead of reading from stdin, append `{"role": "user", "content": "next"}`
after every reply and go round again. Stop when a text block contains `DONE`.

Rules: no library, no extra function, the loop body stays under 15 lines.

When it works you have written your first agent: a loop where the program, not
the person, decides to continue. Notice how fragile the stop condition is. The
model could say "DONE" early, or never. Chapter 4 is about that.

## Where this goes next

Chapter 2 gives the model a way to ask for things: tools. The loop does not
change. The list gets two new kinds of entry.
