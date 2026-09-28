from collections.abc import Iterator

from anthropic import Anthropic

from app.core.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)


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
    
    def send_stream(self, user_message: str) -> Iterator[str]:
        self.history.append({"role": "user", "content": user_message})

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": self.history,
        }
        if self.system:
            kwargs["system"] = self.system

        assistant_text = ""
        with client.messages.stream(**kwargs) as stream:
            for chunk in stream.text_stream:
                assistant_text += chunk
                yield chunk

        self.history.append({"role": "assistant", "content": assistant_text})



if __name__ == "__main__":
    chat = ChatSession(model=settings.anthropic_model)
    print("Chat initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        for chunk in chat.send_stream(user_input):
            print(chunk, end="", flush=True)
        print()
