#!/usr/bin/env python3
"""
Chained multi-agent hello world — LangGraph version of chained_agents.py.

Same idea as chained_agents.py (Agent 1 -> Agent 2, passing one param),
but the chaining and state passing is expressed as a 2-node LangGraph
graph instead of Agent 1 calling Agent 2's Python function directly.

Purpose of each library in this program:
  - LangChain (langchain_anthropic.ChatAnthropic): the LLM client. It
    replaces the raw `anthropic.Anthropic().messages.create(...)` call
    from chained_agents.py with a `.invoke(...)` call — same underlying
    Claude API request, just wrapped in LangChain's model interface.
  - LangGraph (langgraph.graph.StateGraph): the orchestration/control-flow
    layer. It replaces "Agent 1's Python function directly calls Agent 2's
    Python function" with an explicit graph: two nodes (agent_one,
    agent_two) and one edge between them, plus a typed `state` dict that
    is threaded through both nodes instead of being passed as function
    arguments/return values.

Setup:
    pip install anthropic langgraph langchain-anthropic
    export ANTHROPIC_API_KEY=your_key_here

Run:
    python3 chained_agents_langgraph.py
"""

from typing import TypedDict

from langchain_anthropic import ChatAnthropic  # LangChain: wraps the Claude API call
from langgraph.graph import END, StateGraph  # LangGraph: defines the agent graph/flow

MODEL = "claude-haiku-4-5"
llm = ChatAnthropic(model=MODEL, max_tokens=1024)


# State is what gets passed between nodes in the graph — this replaces the
# plain function arguments/return values used in chained_agents.py.
class ChainState(TypedDict):
    greeting: str   # Agent 1's own hello-world message
    language: str   # the param Agent 1 passes to Agent 2
    reply: str      # Agent 2's response


def agent_one_node(state: ChainState) -> ChainState:
    """Agent 1: greets, then decides the param to hand to Agent 2 via state."""

    # --- Old (raw API / chained_agents.py) equivalent of this block: -------
    #     greeting = call_agent(
    #         client,
    #         system="You are Agent 1. Respond in exactly one line.",
    #         user_message="Say hello world in English and introduce yourself as Agent 1.",
    #     )
    #     language = "German"
    #     reply = agent_two(client, language)   # <-- Agent 1 calls Agent 2 directly
    # -------------------------------------------------------------------------
    print("[Agent 1] starting...")
    response = llm.invoke(
        [
            ("system", "You are Agent 1. Respond in exactly one line."),
            ("user", "Say hello world in English and introduce yourself as Agent 1."),
        ]
    )
    print(f"[Agent 1] {response.content}")

    state["greeting"] = response.content
    state["language"] = "German"  # this is the "one param" passed onward,
    # but here it travels via graph state, not a direct function call
    return state


def agent_two_node(state: ChainState) -> ChainState:
    """Agent 2: uses the param Agent 1 put in state (no direct call from Agent 1)."""

    # --- Old (raw API / chained_agents.py) equivalent of this block: -------
    #     def agent_two(client, language: str) -> str:
    #         result = call_agent(
    #             client,
    #             system="You are Agent 2. Respond in exactly one line.",
    #             user_message=f"Say hello world in {language} and introduce yourself as Agent 2.",
    #         )
    #         return result
    # -------------------------------------------------------------------------
    print(f"[Agent 2] called via graph edge with param: language={state['language']}")
    response = llm.invoke(
        [
            ("system", "You are Agent 2. Respond in exactly one line."),
            (
                "user",
                f"Say hello world in {state['language']} and introduce yourself as Agent 2.",
            ),
        ]
    )
    print(f"[Agent 2] {response.content}")

    state["reply"] = response.content
    return state


# --- Old (raw API / chained_agents.py) equivalent of the graph below: ------
#     def main() -> None:
#         client = Anthropic()
#         greeting, reply = agent_one(client)   # agent_one calls agent_two internally
#         print(greeting, reply)
# -----------------------------------------------------------------------------

# Build the graph: two nodes, one edge Agent 1 -> Agent 2.
# This replaces Agent 1 calling agent_two(...) directly in code — instead,
# the graph's edge decides what runs next.
graph = StateGraph(ChainState)
graph.add_node("agent_one", agent_one_node)
graph.add_node("agent_two", agent_two_node)
graph.set_entry_point("agent_one")
graph.add_edge("agent_one", "agent_two")
graph.add_edge("agent_two", END)
app = graph.compile()


def main() -> None:
    print("[Main] running chain graph: agent_one -> agent_two\n")
    result = app.invoke({"greeting": "", "language": "", "reply": ""})

    print("\n[Main] chain complete. Results:")
    print(f"  Agent 1: {result['greeting']}")
    print(f"  Agent 2: {result['reply']}")


if __name__ == "__main__":
    main()
