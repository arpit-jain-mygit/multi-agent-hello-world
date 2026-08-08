#!/usr/bin/env python3
"""
Provider factory hello world — swap the LLM provider per agent, default Anthropic.

Agents call a common Provider interface instead of the Anthropic SDK
directly, so the underlying LLM provider (Anthropic, OpenAI, ...) can be
swapped via the factory without touching agent code. If no provider is
requested, the factory defaults to Anthropic.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

    # optional — only needed if you actually select the OpenAI provider:
    pip install openai
    export OPENAI_API_KEY=your_key_here

Run:
    python3 provider_factory_agents.py            # uses Anthropic (default)
    LLM_PROVIDER=openai python3 provider_factory_agents.py   # uses OpenAI
"""

import os
from abc import ABC, abstractmethod


# ============================================================================
# PROVIDER INTERFACE — every provider must implement call()
# ============================================================================

class Provider(ABC):
    """Common interface every LLM provider must implement."""

    @abstractmethod
    def call(self, system: str, user_message: str) -> str:
        """Send one message to the LLM and return its text reply."""


# ============================================================================
# PROVIDER: Anthropic (the default)
# ============================================================================

class AnthropicProvider(Provider):
    def __init__(self, model: str = "claude-haiku-4-5"):
        # Imported here (not at module level) so the file still works
        # if only the anthropic package is installed, and vice versa
        # for other providers below.
        from anthropic import Anthropic

        self.client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.model = model

    def call(self, system: str, user_message: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return next(block.text for block in response.content if block.type == "text")


# ============================================================================
# PROVIDER: OpenAI (example of a second provider, to prove the factory works)
# ============================================================================

class OpenAIProvider(Provider):
    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self.client = OpenAI()  # reads OPENAI_API_KEY from the environment
        self.model = model

    def call(self, system: str, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content


# ============================================================================
# FACTORY — name -> Provider class. Defaults to "anthropic".
# ============================================================================

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str | None = None) -> Provider:
    """
    Build a Provider by name.

    Resolution order: explicit `name` arg -> LLM_PROVIDER env var -> "anthropic".
    """
    name = (name or os.environ.get("LLM_PROVIDER") or "anthropic").lower()
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name!r}. Available: {list(_PROVIDERS)}")
    return _PROVIDERS[name]()


# ============================================================================
# AGENTS — same hello-world chain as chained_agents.py, but talking to
# whatever provider the factory hands them, instead of an SDK directly.
# ============================================================================

def agent_one(provider: Provider) -> str:
    print("[Agent 1] starting...")
    greeting = provider.call(
        system="You are Agent 1. Respond in exactly one line.",
        user_message="Say hello world and briefly introduce yourself as Agent 1.",
    )
    print(f"[Agent 1] {greeting}")
    return greeting


def agent_two(provider: Provider, greeting: str) -> str:
    print("[Agent 2] starting...")
    reply = provider.call(
        system="You are Agent 2. Respond in exactly one line.",
        user_message=f"Agent 1 just said: \"{greeting}\"\n\nRespond to Agent 1's greeting.",
    )
    print(f"[Agent 2] {reply}")
    return reply


def main() -> None:
    # No provider name passed here -> factory defaults to Anthropic.
    # To try a different provider: LLM_PROVIDER=openai python3 provider_factory_agents.py
    provider = get_provider()
    print(f"[Main] using provider: {type(provider).__name__}\n")

    greeting = agent_one(provider)
    reply = agent_two(provider, greeting)

    print("\n[Main] done.")
    print(f"  Agent 1: {greeting}")
    print(f"  Agent 2: {reply}")


if __name__ == "__main__":
    main()
