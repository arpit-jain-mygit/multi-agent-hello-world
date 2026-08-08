#!/usr/bin/env python3
"""
Prompt caching hello world — real Claude API calls, reports cache hit/miss.

Sends the SAME large system prompt on two calls:
  Call 1 -> first time seeing this prefix  -> cache MISS (writes the cache)
  Call 2 -> identical prefix, sent again   -> cache HIT  (reads the cache)

Note on model choice: the minimum cacheable prefix length depends on the
model. claude-haiku-4-5 needs roughly 4096 tokens before caching activates
at all — a short, real "hello world" system prompt would silently never
cache on Haiku (no error, just cache_creation_input_tokens staying 0
forever). SYSTEM_PROMPT below is padded well past that threshold so
caching actually happens; in a real app this filler would instead be your
large, stable context (docs, instructions, examples, etc.).

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 prompt_caching_hello_world.py
"""

from anthropic import Anthropic

MODEL = "claude-haiku-4-5"

# Padded past Haiku's ~4096-token minimum cacheable prefix so caching
# actually activates (see note above). The repeated sentence is filler —
# only its length matters here, not its content.
SYSTEM_PROMPT = (
    "You are a hello-world assistant. Always respond in exactly one line.\n"
    + ("This sentence exists only to pad the prompt past the minimum cacheable length. " * 400)
)


def describe_cache(usage) -> str:
    """Turn a response's usage stats into a plain-English cache status."""
    if usage.cache_read_input_tokens > 0:
        return f"CACHE HIT (read {usage.cache_read_input_tokens} tokens from cache)"
    if usage.cache_creation_input_tokens > 0:
        return f"CACHE MISS (wrote {usage.cache_creation_input_tokens} tokens to cache)"
    return "NO CACHE (prefix too short to cache, or cache_control missing)"


def call_with_cache(client: Anthropic, user_message: str):
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # marks this block cacheable
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return text, response.usage


def main() -> None:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    print("[Call 1] first request with this system prompt (expect a cache MISS)...")
    text1, usage1 = call_with_cache(client, "Say hello world.")
    print(f"[Call 1] response: {text1}")
    print(
        f"[Call 1] cache_creation_input_tokens={usage1.cache_creation_input_tokens}, "
        f"cache_read_input_tokens={usage1.cache_read_input_tokens}, "
        f"input_tokens={usage1.input_tokens}"
    )
    print(f"[Call 1] cache status: {describe_cache(usage1)}\n")

    print("[Call 2] identical system prompt again (expect a cache HIT)...")
    text2, usage2 = call_with_cache(client, "Say hello world again, differently.")
    print(f"[Call 2] response: {text2}")
    print(
        f"[Call 2] cache_creation_input_tokens={usage2.cache_creation_input_tokens}, "
        f"cache_read_input_tokens={usage2.cache_read_input_tokens}, "
        f"input_tokens={usage2.input_tokens}"
    )
    print(f"[Call 2] cache status: {describe_cache(usage2)}")


if __name__ == "__main__":
    main()
