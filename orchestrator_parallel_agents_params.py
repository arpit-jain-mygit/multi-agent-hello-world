#!/usr/bin/env python3
"""
Parallel multi-agent hello world with orchestrator-supplied params.

Same as orchestrator_parallel_agents.py, but instead of each agent having
its own hardcoded prompt, the orchestrator passes one parameter to each
agent (the language to greet in) when it spawns them.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 orchestrator_parallel_agents_params.py
"""

from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

MODEL = "claude-haiku-4-5"


def call_agent(client: Anthropic, system: str, user_message: str) -> str:
    """One real call to Claude acting as a single agent."""
    # Fresh messages list every call — each agent instance gets its own
    # isolated context. Only the language param travels between agents
    # (via the orchestrator), never conversation history.
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return next(block.text for block in response.content if block.type == "text")


def agent(client: Anthropic, name: str, language: str) -> str:
    """A single agent whose greeting language is decided by the orchestrator."""
    print(f"[{name}] starting (language={language})...")
    result = call_agent(
        client,
        system=f"You are {name}. Respond in exactly one line.",
        user_message=f"Say hello world in {language} and introduce yourself as {name}.",
    )
    print(f"[{name}] done.")
    return result


def orchestrator() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    # The orchestrator decides each agent's parameter
    agent_a_language = "Hindi"
    agent_b_language = "Hindi"

    print("[Orchestrator] spawning Agent A and Agent B in parallel...\n")
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(agent, client, "Agent A", agent_a_language)
        future_b = pool.submit(agent, client, "Agent B", agent_b_language)

        # Both agents are running concurrently now; block until each finishes
        result_a = future_a.result()
        result_b = future_b.result()

    print("\n[Orchestrator] both agents finished. Results:")
    print(f"  Agent A ({agent_a_language}): {result_a}")
    print(f"  Agent B ({agent_b_language}): {result_b}")


if __name__ == "__main__":
    orchestrator()
