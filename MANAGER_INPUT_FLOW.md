# Manager Input Flow: Passing Data to Agents

## Overview

Instead of hardcoded prompts, agents receive dynamic input from the manager. This makes the system flexible and reusable.

```
User/Entry Point
    ↓
Manager (receives: user_task, data_source, analysis_metric)
    ↓
    ├─→ Fetcher (receives: source, task)
    │        ↓
    │    Calls tools, returns data
    │        ↓
    ├─→ Analyzer (receives: data, metric, task)
    │        ↓
    │    Analyzes, returns findings
    │        ↓
    └─→ Manager synthesizes results
            ↓
        Final output
```

---

## Mock Version: Input Flow

### Manager Definition

```python
def manager_agent(user_task: str, data_source: str, analysis_metric: str) -> str:
    """Manager receives 3 inputs and passes them to subagents."""
    print(f"[MANAGER] User Task: {user_task}")
    print(f"[MANAGER] Data Source: {data_source}")
    print(f"[MANAGER] Analysis Metric: {analysis_metric}")

    # Pass input to Fetcher
    fetcher_result = subagent_fetcher(
        source=data_source,
        task=f"Fetch data for: {user_task}",
    )

    # Pass Fetcher's output + manager input to Analyzer
    analyzer_result = subagent_analyzer(
        data=fetcher_result,
        metric=analysis_metric,
        task=f"Analyze for: {user_task}",
    )
    
    return f"Task: {user_task}\n- Fetch: {fetcher_result}\n- Analysis: {analyzer_result}"
```

### Subagent: Fetcher (Receives Input)

```python
def subagent_fetcher(source: str, task: str) -> str:
    """Fetcher receives source and task from manager."""
    print(f"[FETCHER] Input from Manager:")
    print(f"  - Source: {source}")
    print(f"  - Task: {task}")
    
    # Use the manager's input in the agent logic
    tool_call = {"name": "fetch_data", "args": {"source": source}}
    result = TOOLS["fetch_data"](source=source)
    
    return f"Fetched from {source}: {result}"
```

### Subagent: Analyzer (Receives Multiple Inputs)

```python
def subagent_analyzer(data: str, metric: str, task: str) -> str:
    """Analyzer receives fetched data + analysis metric from manager."""
    print(f"[ANALYZER] Input from Manager:")
    print(f"  - Data: {data}")
    print(f"  - Metric: {metric}")
    print(f"  - Task: {task}")
    
    # Use manager's input to guide analysis
    tool_call = {"name": "analyze_data", "args": {"data": data, "metric": metric}}
    result = TOOLS["analyze_data"](data=data, metric=metric)
    
    return f"Analysis ({metric}): {result}"
```

### Main: Calling Manager with Input

```python
if __name__ == "__main__":
    # Example 1
    result1 = manager_agent(
        user_task="Get customer count",
        data_source="database",
        analysis_metric="count",
    )

    # Example 2
    result2 = manager_agent(
        user_task="Monitor sensor data",
        data_source="api",
        analysis_metric="trend",
    )

    # Example 3
    result3 = manager_agent(
        user_task="Get Q3 business summary",
        data_source="file",
        analysis_metric="summary",
    )
```

---

## SDK Version: Input Flow (Real Claude API)

### Manager Definition

```python
def manager_agent(client: Anthropic, user_task: str, data_source: str, analysis_metric: str) -> str:
    """Manager receives input and passes it to subagents via prompts."""
    
    # Pass to Fetcher
    fetcher_result = subagent_fetcher(
        client,
        source=data_source,
        task=f"Fetch data for: {user_task}",
    )
    
    # Pass to Analyzer
    analyzer_result = subagent_analyzer(
        client,
        data=fetcher_result,
        metric=analysis_metric,
        task=f"Analyze for: {user_task}",
    )
    
    # Manager synthesizes
    synthesis_messages = [{
        "role": "user",
        "content": f"User requested: {user_task}\n\nFetcher result: {fetcher_result}\nAnalyzer result: {analyzer_result}\n\nProvide summary."
    }]
    final = run_agent_loop(client, synthesis_messages, "MANAGER")
    return final
```

### Subagent: Fetcher (Claude API)

```python
def subagent_fetcher(client: Anthropic, source: str, task: str) -> str:
    """Fetcher receives source and task from manager, passes to Claude."""
    print(f"[FETCHER] Input from Manager: source={source}, task={task}")
    
    messages = [{
        "role": "user",
        "content": f"Task: {task}\nFetch data from: {source}\nTell me what you found.",
    }]
    
    # Claude sees the manager's input in the prompt
    return run_agent_loop(client, messages, "FETCHER")
```

### Subagent: Analyzer (Claude API)

```python
def subagent_analyzer(client: Anthropic, data: str, metric: str, task: str) -> str:
    """Analyzer receives data + metric from manager, passes to Claude."""
    print(f"[ANALYZER] Input from Manager: metric={metric}, task={task}")
    
    messages = [{
        "role": "user",
        "content": f"Task: {task}\nAnalyze this data by {metric}:\n{data}\nReport your findings.",
    }]
    
    # Claude sees the manager's input in the prompt
    return run_agent_loop(client, messages, "ANALYZER")
```

### Main: Calling Manager with Input

```python
if __name__ == "__main__":
    client = Anthropic()
    
    result = manager_agent(
        client,
        user_task="Get customer analytics",
        data_source="database",
        analysis_metric="count",
    )
    
    print(result)
```

---

## Input Flow: Key Patterns

### Pattern 1: Manager Receives User Input

```python
# Entry point: user provides input
user_task = "Get customer count"
data_source = "database"
analysis_metric = "count"

# Manager receives this input
result = manager_agent(user_task, data_source, analysis_metric)
```

**Key:** Input flows from user → manager → subagents.

---

### Pattern 2: Manager Passes Input to Subagents

```python
# Manager receives input
def manager_agent(user_task: str, data_source: str, analysis_metric: str):
    
    # Pass to Fetcher
    fetcher_result = subagent_fetcher(
        source=data_source,              # From manager input
        task=f"Fetch data for: {user_task}",  # From manager input
    )
    
    # Pass to Analyzer
    analyzer_result = subagent_analyzer(
        data=fetcher_result,              # From Fetcher
        metric=analysis_metric,           # From manager input
        task=f"Analyze for: {user_task}",  # From manager input
    )
```

**Key:** Manager is a relay; it receives input and passes it downstream.

---

### Pattern 3: Subagent Uses Manager Input

**Mock version:** Use input directly in logic
```python
def subagent_fetcher(source: str, task: str) -> str:
    # Use manager's input directly
    result = TOOLS["fetch_data"](source=source)
    return f"Fetched from {source}: {result}"
```

**SDK version:** Pass input via prompt to Claude
```python
def subagent_fetcher(client: Anthropic, source: str, task: str) -> str:
    messages = [{
        "role": "user",
        "content": f"Task: {task}\nFetch data from: {source}\n..."
    }]
    # Claude sees the input in the prompt
    return run_agent_loop(client, messages, "FETCHER")
```

**Key:** Subagent receives input and uses it to guide behavior (either directly or via prompt to Claude).

---

## Data Flow Example

### Example 1: Customer Count

```
User Input:
  - user_task: "Get customer count"
  - data_source: "database"
  - analysis_metric: "count"
        ↓
Manager receives input, spawns:
  - Fetcher(source="database", task="Fetch data for: Get customer count")
        ↓
Fetcher calls: fetch_data(source="database")
Fetcher returns: "Fetched from database: Users: [Alice, Bob, Charlie], Count: 3"
        ↓
Manager spawns:
  - Analyzer(data="Fetched from database: ...", metric="count", task="Analyze for: Get customer count")
        ↓
Analyzer calls: analyze_data(data="Fetched from database: ...", metric="count")
Analyzer returns: "Analysis (count): Total items: 4"
        ↓
Manager synthesizes:
  "Task: Get customer count
   - Fetch (database): Fetched from database: Users: [Alice, Bob, Charlie], Count: 3
   - Analysis (count): Analysis (count): Total items: 4"
```

### Example 2: Sensor Trend Analysis

```
User Input:
  - user_task: "Monitor sensor data"
  - data_source: "api"
  - analysis_metric: "trend"
        ↓
[Fetcher] → fetch_data(source="api")
           → "Temperature: 72°F, Humidity: 45%"
        ↓
[Analyzer] → analyze_data(metric="trend")
           → "Upward trend detected"
        ↓
Final: "Task: Monitor sensor data
        - Fetch (api): Temperature: 72°F, Humidity: 45%
        - Analysis (trend): Upward trend detected"
```

---

## Key Differences: Before vs After

### Before (Hardcoded)
```python
def subagent_fetcher(goal: str) -> str:
    # Hardcoded source
    result = fetch_data(source="database")  # ← Always database
    return result
```

**Problem:** Fetcher can only fetch from database; not flexible.

---

### After (Manager Input)
```python
def subagent_fetcher(source: str, task: str) -> str:
    # Use manager's input
    result = fetch_data(source=source)  # ← Any source
    return f"Fetched from {source}: {result}"
```

**Benefit:** Fetcher is flexible; manager controls behavior.

---

## Enterprise Considerations

### Input Validation
```python
def manager_agent(user_task: str, data_source: str, analysis_metric: str) -> str:
    # Validate inputs
    if data_source not in ["database", "api", "file"]:
        raise ValueError(f"Invalid source: {data_source}")
    
    if analysis_metric not in ["count", "trend", "summary"]:
        raise ValueError(f"Invalid metric: {analysis_metric}")
    
    # Proceed with validated input
    ...
```

**Why:** Prevent bad input from breaking agents; fail fast.

---

### Audit Trail
```python
print(f"[MANAGER] Received:")
print(f"  - Task: {user_task}")
print(f"  - Source: {data_source}")
print(f"  - Metric: {analysis_metric}")
print(f"[MANAGER] Passed to Fetcher: source={data_source}")
print(f"[MANAGER] Passed to Analyzer: metric={analysis_metric}")
```

**Why:** Log every input/output for debugging and compliance.

---

### Content Boundary
```python
# Always assume user_task is untrusted input
def manager_agent(user_task: str, ...):
    # Don't pass directly to Claude; wrap it
    messages = [{
        "role": "system",
        "content": "You are a helpful assistant."
    }, {
        "role": "user",
        "content": f"User requested: {user_task}"  # Marked as user input
    }]
    # Claude knows this is user data, not an instruction
```

**Why:** Prevent prompt injection; separate trusted instructions from untrusted data.

---

## Testing Input Variations

### Mock Version: Easy to Test
```python
# Test 1: Database + Count
result1 = manager_agent("Get count", "database", "count")
assert "database" in result1

# Test 2: API + Trend
result2 = manager_agent("Monitor", "api", "trend")
assert "api" in result2

# Test 3: File + Summary
result3 = manager_agent("Report", "file", "summary")
assert "file" in result3
```

**Benefit:** Mock version is deterministic; easy to test input/output.

---

### SDK Version: Needs API Key
```python
# Requires ANTHROPIC_API_KEY
client = Anthropic()

result = manager_agent(
    client,
    user_task="Get customer count",
    data_source="database",
    analysis_metric="count",
)

print(result)
```

**Benefit:** Real Claude thinking; harder to test (requires API), but more realistic.

---

## Summary

| Aspect | Mock | SDK |
|--------|------|-----|
| **Input Method** | Direct parameters | Direct parameters + prompt injection |
| **Execution** | Local, instant | Remote, via Claude API |
| **Testing** | Easy (deterministic) | Hard (needs API) |
| **Realism** | Medium (shows patterns) | High (real Claude) |
| **Use Case** | Learning, unit tests | Production, integration tests |

**Next:** Run examples, modify inputs, see how agents adapt to different tasks.
