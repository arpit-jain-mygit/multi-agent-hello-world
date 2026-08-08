#!/usr/bin/env python3
"""
Basic parallel multi-agent hello world — real Claude API calls.

An orchestrator spawns two agents at the same time (not one after another)
and waits for both to finish:
  1. Agent A — says hello in English
  2. Agent B — says hello in French

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 orchestrator_parallel_agents.py
"""

from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

MODEL = "claude-haiku-4-5"


def call_agent(client: Anthropic, system: str, user_message: str) -> str:
    """One real call to Claude acting as a single agent."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return next(block.text for block in response.content if block.type == "text")


def agent_a(client: Anthropic) -> str:
    print("[Agent A] starting...")
    result = call_agent(
        client,
        system="You are Agent A.",
        user_message="Say hello world in English and introduce yourself as Agent A.",
    )
    print("[Agent A] done.")
    return result


def agent_b(client: Anthropic) -> str:
    print("[Agent B] starting...")
    result = call_agent(
        client,
        system="You are Agent B.",
        user_message="Say hello world in French and introduce yourself as Agent B.",
    )
    print("[Agent B] done.")
    return result


def orchestrator() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    print("[Orchestrator] spawning Agent A and Agent B in parallel...\n")
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(agent_a, client)
        future_b = pool.submit(agent_b, client)

        # Both agents are running concurrently now; block until each finishes
        result_a = future_a.result()
        result_b = future_b.result()

    print("\n[Orchestrator] both agents finished. Results:")
    print(f"  Agent A: {result_a}")
    print(f"  Agent B: {result_b}")


if __name__ == "__main__":
    orchestrator()
