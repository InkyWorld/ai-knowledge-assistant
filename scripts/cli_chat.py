from app.domain.chat import ChatHistory
from app.rag.pipeline import ask


def main() -> None:
    history = ChatHistory(messages=[])
    print("Chat initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        result = ask(user_input, history=history)
        history.append(role="user", content=user_input)
        history.append(role="assistant", content=result["answer"])
        print(result["answer"])
        if result["sources"]:
            print("\nДжерела:")
            for s in result["sources"]:
                print(f"  {s['source']} | (score={s['score']:.3f}) | (index={s['index']})")


if __name__ == "__main__":
    main()
