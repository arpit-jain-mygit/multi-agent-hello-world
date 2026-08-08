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
    # --------------------------------------------------------------------
    # Flow of this function:
    #   1. Send Claude an instruction to use the get_greetings tool.
    #   2. If Claude responds by requesting the tool (stop_reason == "tool_use"),
    #      run the real Postgres query ourselves and hand the result back to Claude.
    #   3. Claude reads the tool result and produces its final one-line answer.
    #   4. Extract and return that final text to the caller (main()).
    # --------------------------------------------------------------------

    print("[Agent 1: Fetcher] starting...")

    # messages: the running conversation history sent to Claude on every call.
    # Starts with a single user turn instructing Claude what to do.
    messages = [
        {
            "role": "user",
            "content": "Use the get_greetings tool to fetch the greeting messages, "
            "then report what you found in exactly one line.",
        }
    ]

    # One tool-call round trip: call Claude, execute any tool it requests,
    # send the result back, then take Claude's final answer.
    # response: Claude's reply to the first call — either straight to text
    # (if it decides not to use a tool) or a request to call get_greetings.
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You are Agent 1, the Fetcher.",
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )

    # response.stop_reason == "tool_use" means Claude wants to call a tool
    # before it can answer, so we need a second round trip below.
    if response.stop_reason == "tool_use":
        # Record Claude's tool-request turn in the conversation history —
        # required so the next request has full context of what was asked.
        messages.append({"role": "assistant", "content": response.content})

        # tool_results: collects one entry per tool Claude asked to run,
        # to be sent back to Claude as a single user turn.
        tool_results = []

        # response.content is a list of content blocks; we only act on the
        # ones of type "tool_use" (Claude may also emit plain text alongside).
        for block in response.content:
            if block.type == "tool_use":
                # block.name: which tool Claude wants to call (e.g. "get_greetings").
                # block.input: the arguments Claude chose for that tool (e.g. {"limit": 5}).
                print(f"[Agent 1: Fetcher] calling tool: {block.name}({block.input})")

                # result: the real return value from actually running the tool
                # (executes the live Postgres query — this is not simulated).
                result = TOOLS[block.name](**block.input)
                print(f"[Agent 1: Fetcher] tool result: {result}")

                # block.id: the tool_use_id Claude assigned this call; the
                # tool_result we send back must reference it so Claude can
                # match the result to the request it made.
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )

        # Append the tool results as a user turn — this is how tool output
        # gets back into the conversation for Claude to read.
        messages.append({"role": "user", "content": tool_results})

        # Second call: now that Claude has the real tool result in its
        # context, ask it for its final one-line answer.
        # response is reassigned here to hold this second reply.
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are Agent 1, the Fetcher. Respond in exactly one line.",
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

    # final_text: pulls out the plain-text answer from Claude's last response
    # (skipping over any non-text content blocks, though none are expected here).
    final_text = next(block.text for block in response.content if block.type == "text")
    print(f"[Agent 1: Fetcher] {final_text}")

    # Hand the one-line finding back to main(), which will pass it to Agent 2.
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
