#!/usr/bin/env python3
"""
Two agents with a real Postgres tool — real Claude API calls, no mocks.

Agent 1 (Fetcher) has a `get_greetings` tool that runs a real, parameterized
query against a Postgres table. Agent 2 (Summarizer) receives Agent 1's
findings as one param and summarizes them.

Setup:
    pip install anthropic psycopg2-binary
    export ANTHROPIC_API_KEY=your_key_here
    export POSTGRES_DSN="dbname=postgres user=postgres password=postgres host=localhost port=5432"

    # create the table and sample data:
    psql "$POSTGRES_DSN" -f setup_postgres.sql

Run:
    python3 postgres_tool_agents.py
"""

import json
import os

import psycopg2
from anthropic import Anthropic

MODEL = "claude-haiku-4-5"
POSTGRES_DSN = os.environ.get(
    "POSTGRES_DSN", "dbname=postgres user=postgres password=postgres host=localhost port=5432"
)


# ============================================================================
# TOOL: real Postgres query (fixed SQL, only `limit` is model-controlled,
# and it's passed as a parameterized value — never string-interpolated).
# ============================================================================

def get_greetings(limit: int = 5) -> str:
    conn = psycopg2.connect(POSTGRES_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT message FROM hello_messages LIMIT %s;", (limit,))
            rows = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    return "; ".join(rows) if rows else "No greetings found."


TOOLS = {"get_greetings": get_greetings}

TOOL_DEFINITIONS = [
    {
        "name": "get_greetings",
        "description": "Fetch greeting messages stored in the Postgres hello_messages table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of greeting rows to fetch",
                }
            },
        },
    }
]


# ============================================================================
# AGENT 1: Fetcher — uses the Postgres tool
# ============================================================================

def agent_fetcher(client: Anthropic) -> str:
    print("[Agent 1: Fetcher] starting...")
    messages = [
        {
            "role": "user",
            "content": "Use the get_greetings tool to fetch the greeting messages, "
            "then report what you found in exactly one line.",
        }
    ]

    # One tool-call round trip: call Claude, execute any tool it requests,
    # send the result back, then take Claude's final answer.
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You are Agent 1, the Fetcher.",
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[Agent 1: Fetcher] calling tool: {block.name}({block.input})")
                result = TOOLS[block.name](**block.input)
                print(f"[Agent 1: Fetcher] tool result: {result}")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are Agent 1, the Fetcher. Respond in exactly one line.",
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

    final_text = next(block.text for block in response.content if block.type == "text")
    print(f"[Agent 1: Fetcher] {final_text}")
    return final_text


# ============================================================================
# AGENT 2: Summarizer — receives Agent 1's findings as one param
# ============================================================================

def agent_summarizer(client: Anthropic, findings: str) -> str:
    print("\n[Agent 2: Summarizer] starting...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You are Agent 2, the Summarizer. Respond in exactly one line.",
        messages=[
            {
                "role": "user",
                "content": f"Agent 1 found this from the database: \"{findings}\"\n\n"
                "Summarize it briefly.",
            }
        ],
    )
    final_text = next(block.text for block in response.content if block.type == "text")
    print(f"[Agent 2: Summarizer] {final_text}")
    return final_text


def main() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    findings = agent_fetcher(client)
    summary = agent_summarizer(client, findings)

    print("\nDone.")
    print(f"  Agent 1 findings: {findings}")
    print(f"  Agent 2 summary:  {summary}")


if __name__ == "__main__":
    main()
