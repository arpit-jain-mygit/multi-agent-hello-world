#!/usr/bin/env python3
"""
Chained multi-agent hello world — real Claude API calls, no mocks.

Unlike orchestrator_parallel_agents.py (an orchestrator calls both agents)
or multi_agent_real_hello_world.py (main calls both agents in sequence),
here Agent 1 calls Agent 2 directly and passes it one parameter — main()
only ever talks to Agent 1.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 chained_agents.py
"""

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


def agent_two(client: Anthropic, language: str) -> str:
    """Second agent in the chain. Only ever invoked by Agent 1."""
    print(f"[Agent 2] called by Agent 1 with param: language={language}")
    result = call_agent(
        client,
        system="You are Agent 2. Respond in exactly one line.",
        user_message=f"Say hello world in {language} and introduce yourself as Agent 2.",
    )
    print("[Agent 2] done.")
    return result


def agent_one(client: Anthropic) -> tuple[str, str]:
    """First agent in the chain. Calls Agent 2 directly, passing it one param."""
    print("[Agent 1] starting...")
    greeting = call_agent(
        client,
        system="You are Agent 1. Respond in exactly one line.",
        user_message="Say hello world in English and introduce yourself as Agent 1.",
    )
    print(f"[Agent 1] {greeting}")

    language = "German"
    print(f"[Agent 1] calling Agent 2 directly, passing language={language}...")
    reply = agent_two(client, language)

    print("[Agent 1] received Agent 2's response.")
    return greeting, reply


def main() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    print("[Main] starting chain: Agent 1 -> Agent 2\n")
    greeting, reply = agent_one(client)

    print("\n[Main] chain complete. Results:")
    print(f"  Agent 1: {greeting}")
    print(f"  Agent 2: {reply}")


if __name__ == "__main__":
    main()
