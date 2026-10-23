import json

from app.agent.manual_react import run_agent
from app.domain.chat import ChatHistory


def print_steps(steps: list[dict]) -> None:
    for s in steps:
        print(f"\n[Step {s['step'] + 1}] tool: {s['tool']}")
        if s["thought"]:
            print(f"  Thought: {s['thought']}")
        print(f"  Input: {json.dumps(s['input'], ensure_ascii=False)}")
        print(f"  Output: {s['output_preview']}")
        if s["is_error"]:
            print("  Status: error")


def main() -> None:
    history = ChatHistory(messages=[])
    print("Agent initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        result = run_agent(user_input, history=history)
        history.append(role="user", content=user_input)
        history.append(role="assistant", content=result.answer)
        if result.steps:
            print_steps(result.steps)
        print(f"\nAnswer: {result.answer}")
        if result.stopped_by == "max_steps":
            print("  Agent stopped by max steps limit.")
        print(f"  Tokens: input={result.input_tokens}, output={result.output_tokens}")


if __name__ == "__main__":
    main()