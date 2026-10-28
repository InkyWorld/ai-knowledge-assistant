import uuid
from typing import Any

from langfuse import observe
from langgraph.errors import GraphRecursionError

from app.agent.graph import new_turn_input
from app.agent.runtime import agent_with_memory
from app.core.observability import flush_tracing, init_tracing


@observe(as_type="agent", name="agent_run")
def run_agent(agent: Any, input_state: dict, config: dict) -> dict:
    return agent.invoke(input_state, config)


def final_text(state: dict) -> str:
    content = state["messages"][-1]["content"]
    return "".join(b["text"] for b in content if b["type"] == "text").strip()


def main() -> None:
    init_tracing()
    thread_id = input("thread_id (Enter = новий): ").strip() or str(uuid.uuid4())
    print("thread:", thread_id)
    with agent_with_memory() as agent:
        while question := input("Ви: ").strip():
            try:
                state = run_agent(
                    agent,
                    new_turn_input(question),
                    {"configurable": {"thread_id": thread_id}, "recursion_limit": 25},
                )
                print("Асистент:", final_text(state))
            except GraphRecursionError:
                print("Асистент: не вдалося завершити за ліміт кроків.")
    flush_tracing()


if __name__ == "__main__":
    main()