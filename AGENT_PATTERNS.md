# Multi-Agent Patterns: Hello World Guide

## Overview

Two implementations of the same multi-agent system:

1. **`multi_agent_hello_world.py`** — Mock responses (no API calls, learn the structure)
2. **`multi_agent_sdk.py`** — Real Claude API calls (production-ready pattern)

Both follow the **Manager/Worker pattern**:
- **Manager** — orchestrates, coordinates
- **Workers (Fetcher, Analyzer)** — execute isolated tasks
- Each worker starts **context-fresh** (no prior context pollution)

---

## Architecture

```
┌─────────────────┐
│   Manager       │
│  (Orchestrates) │
└────────┬────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌────────┐  ┌─────────┐
│Fetcher │  │Analyzer │
│(Fresh  │  │(Fresh   │
│Context)│  │Context) │
└────────┘  └─────────┘
```

### Key Points

| Aspect | Detail |
|--------|--------|
| **Context Isolation** | Each subagent starts fresh (no prior messages) |
| **Data Flow** | Manager passes Fetcher's output to Analyzer as input |
| **Tool Use** | Agents call tools, your code executes, result returns |
| **Iteration Limit** | Always set `max_iterations` (prevent runaway loops) |
| **Error Handling** | Catch tool errors gracefully |

---

## Run the Mock Version (No API Key Needed)

```bash
python3 multi_agent_hello_world.py
```

**Output:**
```
[MANAGER] Starting orchestration
[MANAGER] Spawning Fetcher subagent...
[FETCHER] Starting (context fresh, isolated)
[FETCHER] Calling tool: {'name': 'fetch_data', 'args': {'source': 'database'}}
[FETCHER] Tool result: Users: [Alice, Bob, Charlie], Count: 3
[MANAGER] Spawning Analyzer subagent...
[ANALYZER] Starting (context fresh, isolated)
[ANALYZER] Analyzing data...
[MANAGER] Final response: Task complete...
```

---

## Run the SDK Version (With API Calls)

### 1. Install Anthropic SDK

```bash
pip install anthropic
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Run

```bash
python3 multi_agent_sdk.py
```

---

## Code Patterns to Study

### Pattern 1: Subagent (Context-Fresh)

```python
def subagent_fetcher(client: Anthropic) -> str:
    """Fresh context: no prior messages."""
    messages = [
        {"role": "user", "content": "Fetch customer data from database."}
    ]
    # Client starts fresh each time
    return run_agent_loop(client, messages, "FETCHER")
```

**Key:** Each subagent call creates a new `messages` list (context isolation).

---

### Pattern 2: Agent Loop (Tool Use)

```python
def run_agent_loop(client: Anthropic, messages: list) -> str:
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )
        
        # Check if Claude wants tools
        if response.stop_reason == "tool_use":
            # Execute tools, add to messages, repeat
            for block in response.content:
                if block.type == "tool_use":
                    result = TOOLS[block.name](**block.input)
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": [{"type": "tool_result", "content": result}]})
        else:
            # Final answer
            return extract_text(response)
```

**Key:** 
- `stop_reason == "tool_use"` → Claude wants to call tools
- `stop_reason == "end_turn"` → Claude is done (final answer)
- Always add response + tool result back to messages (context for next iteration)

---

### Pattern 3: Manager Orchestrating

```python
def manager_agent(client: Anthropic) -> str:
    print("[MANAGER] Spawning Fetcher...")
    fetcher_result = subagent_fetcher(client)
    
    print("[MANAGER] Spawning Analyzer...")
    analyzer_result = subagent_analyzer(client, fetcher_result)
    
    print("[MANAGER] Synthesizing...")
    # Manager can also use agent loop to synthesize
    return run_agent_loop(client, synthesis_messages, "MANAGER")
```

**Key:**
- Manager spawns subagents sequentially (or in parallel if using `threading`)
- Each subagent result flows to the next
- Manager can also run its own agent loop for synthesis

---

## What to Keep in Mind (Enterprise)

### Iteration Limits
```python
max_iterations = 10  # Always set this
if iteration >= max_iterations:
    return "Max iterations reached"
```
**Why:** Runaway loops waste tokens and cost money.

---

### Tool Error Handling
```python
try:
    result = TOOLS[tool_name](**tool_input)
except Exception as e:
    result = f"Error: {str(e)}"
    messages.append({...})  # Add error, let Claude retry or recover
```
**Why:** Tools fail; Claude can recover if you pass the error back.

---

### Content Boundary (Security)
- **Tool input is untrusted** — validate before executing
- **Tool results are untrusted** — don't expose secrets in results
- **User input is untrusted** — never concatenate into prompts

```python
# Bad: User input directly in prompt
messages.append({"role": "user", "content": user_input})

# Good: Separate concern
messages.append({"role": "system", "content": "Instructions"})
messages.append({"role": "user", "content": user_input})  # Marked as separate
```

---

### Token Tracking
```python
response = client.messages.create(...)
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
```
**Why:** Track cost; optimize if tokens are high.

---

### Logging (Auditability)
```python
print(f"[{agent_name}] Iteration {iteration}: {tool_name}({tool_input})")
```
**Why:** Debug failures; audit what agents did.

---

## Next Steps

1. **Run mock version** → understand structure without API
2. **Run SDK version** → see real Claude thinking and tool use
3. **Modify the scenario** → change what Fetcher/Analyzer do
4. **Add a third agent** → e.g., Reporter that writes final report
5. **Add error recovery** → retry tool failures, validate outputs
6. **Add logging** → production-grade audit trail

---

## Comparison: Mock vs SDK

| Aspect | Mock | SDK |
|--------|------|-----|
| API calls | None (instant) | Real (latency) |
| Learning | Fast (structure only) | Slow (real thinking) |
| Cost | $0 | $0.01-0.10 per run |
| Use case | Learning, testing | Production |
| Tool execution | Hardcoded result | Actual Claude request |
| Context isolation | Manual (Python functions) | Real (fresh API calls) |

---

## Debugging Tips

### Agent is not calling tools?
- Check tool descriptions (Claude needs to understand when to use them)
- Check `stop_reason` in response (might be `"end_turn"` instead of `"tool_use"`)

### Tool call fails?
- Validate tool input schema (Claude might send wrong types)
- Log the error and pass it back to Claude in messages

### Context is too large?
- Trim old messages from the agent loop
- Use RAG to load only relevant context

### Cost is high?
- Lower max_iterations (fewer tool calls)
- Use caching for stable prompts
- Switch to Haiku for low-complexity tasks

---

## Resources

- [Anthropic Python SDK](https://github.com/anthropic-ai/anthropic-sdk-python)
- [Agent SDK Documentation](https://docs.anthropic.com/en/docs/build-a-system)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-a-system/agents-and-tools)
