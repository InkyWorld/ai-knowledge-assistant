def repair_tool_pairs(messages: list[dict]) -> list[dict]:
    """Каждому tool_use должен соответствовать tool_result, иначе API отклонит запрос."""
    fixed: list[dict] = []
    for i, msg in enumerate(messages):
        fixed.append(msg)
        if msg["role"] != "assistant" or isinstance(msg["content"], str):
            continue
        ids = [b["id"] for b in msg["content"] if b["type"] == "tool_use"]
        if not ids:
            continue
        nxt = messages[i + 1] if i + 1 < len(messages) else None
        answered: set[str] = set()
        if nxt and nxt["role"] == "user" and not isinstance(nxt["content"], str):
            answered = {b["tool_use_id"] for b in nxt["content"] if b.get("type") == "tool_result"}
        missing = [t for t in ids if t not in answered]
        if missing:
            fixed.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": t, "content": "Виконання перервано.", "is_error": True}
                for t in missing
            ]})
    return fixed


def trim_to_last_turns(messages: list[dict], k: int = 6) -> list[dict]:
    """Оставляет последние k реплик, начиная с сообщения пользователя с текстом (граница реплики)."""
    starts = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    return messages[starts[-k]:] if len(starts) > k else messages