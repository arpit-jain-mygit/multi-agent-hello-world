#!/usr/bin/env python3
"""
Multi-agent system using Claude Agent SDK (real API calls).
Manager orchestrates Fetcher and Analyzer subagents.

Requires: pip install anthropic

Run with: ANTHROPIC_API_KEY=your_key python3 multi_agent_sdk.py
"""

import json
from anthropic import Anthropic


# ============================================================================
# TOOLS (Actual implementations)
# ============================================================================

def fetch_data(source: str) -> str:
    """Fetch data from a source."""
    mock_data = {
        "database": "Users: [Alice, Bob, Charlie], Count: 3",
        "api": "Temperature: 72°F, Humidity: 45%",
        "file": "Q3 Revenue: $1.2M, Growth: 15%",
    }
    return mock_data.get(source, f"No data for source: {source}")


def analyze_data(data: str, metric: str) -> str:
    """Analyze data by metric."""
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

# Tool definitions for Claude
TOOL_DEFINITIONS = [
    {
        "name": "fetch_data",
        "description": "Fetch data from a source (database, api, or file)",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source: database, api, or file",
                }
            },
            "required": ["source"],
        },
    },
    {
        "name": "analyze_data",
        "description": "Analyze data by a given metric",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data to analyze"},
                "metric": {
                    "type": "string",
                    "description": "Metric: count, trend, or summary",
                },
            },
            "required": ["data", "metric"],
        },
    },
]


# ============================================================================
# AGENT LOOP (Handle tool calls)
# ============================================================================

def run_agent_loop(client: Anthropic, messages: list, agent_name: str) -> str:
    """
    Run the agentic loop for one agent.
    - Claude thinks and calls tools
    - We execute tools and return results
    - Repeat until Claude gives final answer
    """
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"[{agent_name}] Iteration {iteration}")

        # Call Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="You are a helpful assistant. Use tools as needed to complete the task.",
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            # Claude called a tool; execute it
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    print(f"[{agent_name}] Claude called: {tool_name}({tool_input})")

                    # Execute tool
                    try:
                        tool_result = TOOLS[tool_name](**tool_input)
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"

                    print(f"[{agent_name}] Tool result: {tool_result}")

                    # Add Claude's response + tool result to messages
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": tool_result,
                                }
                            ],
                        }
                    )
        else:
            # Claude gave final answer (stop_reason == "end_turn")
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break
            print(f"[{agent_name}] Final response: {final_text}")
            return final_text

    return "Max iterations reached"


# ============================================================================
# SUBAGENT: FETCHER
# ============================================================================

def subagent_fetcher(client: Anthropic, source: str, task: str) -> str:
    """
    Fetcher subagent (context-fresh).
    Receives input from manager: source (where), task (why).
    """
    print(f"\n[FETCHER] Starting (fresh context)")
    print(f"[FETCHER] Input from Manager: source={source}, task={task}")

    messages = [
        {
            "role": "user",
            "content": f"Task: {task}\nFetch data from: {source}\nTell me what you found.",
        }
    ]
    return run_agent_loop(client, messages, "FETCHER")


# ============================================================================
# SUBAGENT: ANALYZER
# ============================================================================

def subagent_analyzer(client: Anthropic, data: str, metric: str, task: str) -> str:
    """
    Analyzer subagent (context-fresh, receives data as input).
    Receives input from manager: data (what), metric (which), task (why).
    """
    print(f"\n[ANALYZER] Starting (fresh context)")
    print(f"[ANALYZER] Input from Manager: metric={metric}, task={task}")

    messages = [
        {
            "role": "user",
            "content": f"Task: {task}\nAnalyze this data by {metric}:\n{data}\nReport your findings.",
        }
    ]
    return run_agent_loop(client, messages, "ANALYZER")


# ============================================================================
# MANAGER AGENT
# ============================================================================

def manager_agent(client: Anthropic, user_task: str, data_source: str, analysis_metric: str) -> str:
    """
    Manager orchestrates subagents.
    Receives input and passes it to subagents.

    Args:
        user_task: What the user wants done
        data_source: Where to fetch data from
        analysis_metric: What metric to analyze
    """
    print("\n[MANAGER] Starting orchestration")
    print(f"[MANAGER] User Task: {user_task}")
    print(f"[MANAGER] Data Source: {data_source}")
    print(f"[MANAGER] Analysis Metric: {analysis_metric}")

    # Spawn Fetcher (pass manager input)
    print("\n[MANAGER] Spawning Fetcher with input...")
    fetcher_result = subagent_fetcher(
        client,
        source=data_source,
        task=f"Fetch data for: {user_task}",
    )
    print(f"[MANAGER] Fetcher returned: {fetcher_result[:100]}...")

    # Spawn Analyzer (pass Fetcher's result + manager input)
    print("\n[MANAGER] Spawning Analyzer with input...")
    analyzer_result = subagent_analyzer(
        client,
        data=fetcher_result,
        metric=analysis_metric,
        task=f"Analyze for: {user_task}",
    )
    print(f"[MANAGER] Analyzer returned: {analyzer_result[:100]}...")

    # Manager synthesizes
    print("\n[MANAGER] Synthesizing results...")
    synthesis_messages = [
        {
            "role": "user",
            "content": f"User requested: {user_task}\n\nI coordinated two agents:\n1. Fetcher (from {data_source}): {fetcher_result}\n2. Analyzer ({analysis_metric}): {analyzer_result}\n\nProvide a final summary.",
        }
    ]
    final = run_agent_loop(client, synthesis_messages, "MANAGER")
    return final


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Agent System (Claude Agent SDK with Real API + Manager Input)")
    print("=" * 70)

    # Initialize client (uses ANTHROPIC_API_KEY env var)
    client = Anthropic()

    # Run multi-agent system with manager input
    print("\n### Running with manager input ###")
    result = manager_agent(
        client,
        user_task="Get customer analytics",
        data_source="database",
        analysis_metric="count",
    )

    print("\n" + "=" * 70)
    print("FINAL OUTPUT")
    print("=" * 70)
    print(result)
