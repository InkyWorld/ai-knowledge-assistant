import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class ChatSession:
    def __init__(self, model: str = "claude-haiku-4-5", system: str | None = None):
        self.model = model
        self.system = system
        self.history: list[dict] = []

    def send(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": self.history,
        }
        if self.system:
            kwargs["system"] = self.system

        response = client.messages.create(**kwargs)
        assistant_text = response.content[0].text

        self.history.append({"role": "assistant", "content": assistant_text})
        return assistant_text


if __name__ == "__main__":
    chat = ChatSession()
    print("Chat initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        print(chat.send(user_input))
