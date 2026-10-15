from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatHistory:
    messages: list[ChatMessage]

    def append(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))

    def to_api_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def to_text(self, last: int = 4) -> str:  # for the query rewriter
        names = {"user": "Користувач", "assistant": "Асистент"}
        return "\n".join(f"{names[m.role]}: {m.content}" for m in self.messages[-last:])

    def reset(self) -> None:
        self.messages.clear()
