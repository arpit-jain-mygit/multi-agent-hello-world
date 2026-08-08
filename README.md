# Multi-Agent Hello World

Small examples of the manager/worker multi-agent pattern with Claude, from mocked responses up to real API calls.

## Files

- **`multi_agent_hello_world.py`** — Mock responses, no API calls. Learn the manager/worker structure without spending tokens.
- **`multi_agent_sdk.py`** — Real Claude API calls with a manual tool-use agent loop (Manager → Fetcher/Analyzer workers).
- **`multi_agent_real_hello_world.py`** — The simplest possible real multi-agent example: two chained Claude API calls (Greeter → Responder), no tools.
- **`AGENT_PATTERNS.md`** — Overview of the manager/worker pattern used across these examples.
- **`MANAGER_INPUT_FLOW.md`** — How dynamic input flows from the manager down to worker agents.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
# Simplest real example
./.venv/bin/python multi_agent_real_hello_world.py

# Manager/worker pattern with real API calls
./.venv/bin/python multi_agent_sdk.py

# Manager/worker pattern with mocked responses (no API key needed)
python3 multi_agent_hello_world.py
```
