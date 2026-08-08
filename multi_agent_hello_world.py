#!/usr/bin/env python3
"""
Multi-agent hello world using Claude Agent SDK.
Manager spawns two subagents: Fetcher and Analyzer.
Each subagent runs in isolation (context-fresh).
Demonstrates: manager pattern, tool use, mock responses.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MockAgentResponse:
    """Mock Claude response for testing without API calls."""
    content: str
    tool_calls: list[dict] = None


# ============================================================================
# TOOLS (Define what agents can do)
# ============================================================================

def fetch_data(source: str) -> str:
    """Mock tool: fetch data from a source."""
    mock_data = {
        "database": "Users: [Alice, Bob, Charlie], Count: 3",
        "api": "Temperature: 72°F, Humidity: 45%",
        "file": "Q3 Revenue: $1.2M, Growth: 15%",
    }
    return mock_data.get(source, f"No data for source: {source}")


def analyze_data(data: str, metric: str) -> str:
    """Mock tool: analyze data by metric."""
    analysis = {
        "count": f"Total items: {len(data.split(','))}",
        "trend": "Upward trend detected" if "15%" in data or "72" in data else "Stable",
        "summary": f"Analysis complete. {data}",
    }
    return analysis.get(metric, f"Cannot analyze {metric}")


TOOLS = {
    "fetch_data": fetch_data,
    "analyze_data": analyze_data,
}


# ============================================================================
# SUBAGENT: FETCHER
# ============================================================================

def subagent_fetcher(source: str, task: str) -> str:
    """
    Fetcher subagent: runs in isolation, fetches data.
    Receives input from manager: source (what to fetch), task (why).
    """
    print("\n[FETCHER] Starting (context fresh, isolated)")
    print(f"[FETCHER] Input from Manager:")
    print(f"  - Source: {source}")
    print(f"  - Task: {task}")

    # Simulate Claude thinking + tool use (uses manager's input)
    print(f"[FETCHER] Thinking: I need to fetch data from {source}...")
    tool_call = {"name": "fetch_data", "args": {"source": source}}
    print(f"[FETCHER] Calling tool: {tool_call}")

    # Execute tool
    result = TOOLS["fetch_data"](source=source)
    print(f"[FETCHER] Tool result: {result}")

    # Simulate Claude final response
    final_response = f"Fetched from {source}: {result}"
    print(f"[FETCHER] Response: {final_response}")
    return final_response


# ============================================================================
# SUBAGENT: ANALYZER
# ============================================================================

def subagent_analyzer(data: str, metric: str, task: str) -> str:
    """
    Analyzer subagent: runs in isolation, analyzes data.
    Receives input from manager: data (what to analyze), metric (which metric), task (why).
    """
    print("\n[ANALYZER] Starting (context fresh, isolated)")
    print(f"[ANALYZER] Input from Manager:")
    print(f"  - Data: {data}")
    print(f"  - Metric: {metric}")
    print(f"  - Task: {task}")

    # Simulate Claude thinking + tool use (uses manager's input)
    print(f"[ANALYZER] Thinking: I need to analyze this data by {metric}...")
    tool_call = {"name": "analyze_data", "args": {"data": data, "metric": metric}}
    print(f"[ANALYZER] Calling tool: {tool_call}")

    # Execute tool
    result = TOOLS["analyze_data"](data=data, metric=metric)
    print(f"[ANALYZER] Tool result: {result}")

    # Simulate Claude final response
    final_response = f"Analysis ({metric}): {result}"
    print(f"[ANALYZER] Response: {final_response}")
    return final_response


# ============================================================================
# MANAGER AGENT
# ============================================================================

def manager_agent(user_task: str, data_source: str, analysis_metric: str) -> str:
    """
    Manager agent: orchestrates subagents.
    Receives input and passes it to subagents.

    Args:
        user_task: What the user wants done
        data_source: Where to fetch data from (database, api, file)
        analysis_metric: What metric to analyze (count, trend, summary)
    """
    print("\n[MANAGER] Starting orchestration")
    print(f"[MANAGER] User Task: {user_task}")
    print(f"[MANAGER] Data Source: {data_source}")
    print(f"[MANAGER] Analysis Metric: {analysis_metric}")

    # Step 1: Spawn Fetcher subagent (pass input from manager)
    print("\n[MANAGER] Spawning Fetcher subagent with input...")
    fetcher_result = subagent_fetcher(
        source=data_source,
        task=f"Fetch data for: {user_task}",
    )
    print(f"[MANAGER] Fetcher returned: {fetcher_result}")

    # Step 2: Spawn Analyzer subagent (pass Fetcher's result + manager's input)
    print("\n[MANAGER] Spawning Analyzer subagent with input...")
    analyzer_result = subagent_analyzer(
        data=fetcher_result,
        metric=analysis_metric,
        task=f"Analyze for: {user_task}",
    )
    print(f"[MANAGER] Analyzer returned: {analyzer_result}")

    # Step 3: Manager synthesizes and responds
    print("\n[MANAGER] Synthesizing results...")
    final = f"Task: {user_task}\n- Fetch ({data_source}): {fetcher_result}\n- Analysis ({analysis_metric}): {analyzer_result}"
    print(f"[MANAGER] Final response: {final}")
    return final


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Agent Hello World (Mock Responses + Manager Input)")
    print("=" * 70)

    # Example 1: Analyze database users by count
    print("\n\n### EXAMPLE 1: Database Users ###")
    result1 = manager_agent(
        user_task="Get customer count",
        data_source="database",
        analysis_metric="count",
    )
    print("\n" + "=" * 70)
    print("RESULT 1")
    print("=" * 70)
    print(result1)

    # Example 2: Analyze API data by trend
    print("\n\n### EXAMPLE 2: API Sensors ###")
    result2 = manager_agent(
        user_task="Monitor sensor data",
        data_source="api",
        analysis_metric="trend",
    )
    print("\n" + "=" * 70)
    print("RESULT 2")
    print("=" * 70)
    print(result2)

    # Example 3: Analyze file data by summary
    print("\n\n### EXAMPLE 3: Q3 Financial Report ###")
    result3 = manager_agent(
        user_task="Get Q3 business summary",
        data_source="file",
        analysis_metric="summary",
    )
    print("\n" + "=" * 70)
    print("RESULT 3")
    print("=" * 70)
    print(result3)
