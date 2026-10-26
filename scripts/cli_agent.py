import uuid

from langgraph.errors import GraphRecursionError

from app.agent.runtime import agent_with_memory


def final_text(state: dict) -> str:
    content = state["messages"][-1]["content"]
    return "".join(b["text"] for b in content if b["type"] == "text").strip()


def main() -> None:
    thread_id = input("thread_id (Enter = новий): ").strip() or str(uuid.uuid4())
    print("thread:", thread_id)
    with agent_with_memory() as agent:
        while question := input("Ви: ").strip():
            try:
                state = agent.invoke(
                    {"messages": [{"role": "user", "content": question}], "stop_reason": ""},
                    {"configurable": {"thread_id": thread_id}, "recursion_limit": 25},
                )
                print("Асистент:", final_text(state))
            except GraphRecursionError:
                print("Асистент: не вдалося завершити за ліміт кроків.")


if __name__ == "__main__":
    main()