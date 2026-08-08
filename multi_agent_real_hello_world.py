#!/usr/bin/env python3
"""
Basic multi-agent hello world — real Claude API calls, no mocks.

Two agents, each a separate call to Claude:
  1. Greeter  — says hello and introduces itself
  2. Responder — reads the Greeter's message and replies

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 multi_agent_real_hello_world.py
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


def main() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    print("[Agent 1: Greeter] calling Claude...")
    greeting = call_agent(
        client,
        system="You are Agent 1, the Greeter. Respond in exactly one line.",
        user_message="Say hello world and briefly introduce yourself as Agent 1.",
    )
    print(f"[Agent 1: Greeter] {greeting}\n")

    print("[Agent 2: Responder] calling Claude...")
    reply = call_agent(
        client,
        system="You are Agent 2, the Responder. Respond in exactly one line.",
        user_message=f"Agent 1 just said: \"{greeting}\"\n\nRespond to Agent 1's greeting.",
    )
    print(f"[Agent 2: Responder] {reply}")


if __name__ == "__main__":
    main()
