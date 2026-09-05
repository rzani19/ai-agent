# AI Agent Playground

A small local AI agent built with [Ollama](https://ollama.com) and **Qwen3:8B**, exploring the fundamentals of tool calling — how an LLM decides to call a function, executes it, and uses the result to answer.

Built as a hands-on learning project: no framework, just a plain Python agent loop, a tool registry, and persistent conversation memory.

## Features

- **Tool calling** via a simple registry — add a new tool by registering its function + JSON schema, nothing else to wire up.
- **Persistent memory** — conversation history is saved to `conversation_history.json` and reloaded on the next run, so the agent remembers context across restarts.
- **Safe expression evaluation** — `calculate` parses expressions with Python's `ast` module instead of `eval()`, so it can't execute arbitrary code.

## Available Tools

| Tool | Description |
|---|---|
| `get_time` | Returns the current local time. |
| `calculate` | Evaluates a basic arithmetic expression (`+ - * / **`). |

## Setup

Requires [Ollama](https://ollama.com) running locally with the `qwen3:8b` model pulled:

```bash
ollama pull qwen3:8b
```

Install dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Run

```bash
uv run python agent.py
```

Type a message, watch it call tools when needed, and type `exit` to quit. Your conversation is saved automatically and picked up again next time you run it.

## Run Tests

```bash
uv run pytest
```

## Project Structure

```
agent.py                       # agent loop, tool registry, memory persistence
test_agent.py                  # pytest suite
examples/
  structured_output_demo.py    # standalone demo of structured (JSON) output
src/ai_agent/                  # reserved package skeleton for future growth
```
