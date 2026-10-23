from app.agent.tools.calculator import safe_eval
from app.rag.relevance import is_relevant
from app.rag.retriever import retrieve

TOOLS = [
    {
        "name": "rag_search",
        "description": (
            "Шукає у базі нормативних документів (постанови КМУ) фрагменти за змістом: що змінено, "
            "хто уповноважений, до якої дати, які громади. Повертає до 4 фрагментів із джерелом. "
            "НЕ використовуй для підрахунків і статистики по всіх документах."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Самодостатній пошуковий запит українською"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Обчислює арифметичний вираз (+, -, *, /, дужки). Використовуй для будь-яких розрахунків, не рахуй сам.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Наприклад: (12 + 8) * 3"}},
            "required": ["expression"],
        },
    },
]


def run_rag_search(query: str) -> str:
    chunks = retrieve(query, search_limit=15, rerank_limit=4)
    if not chunks or not is_relevant(chunks[0]):
        return "Нічого релевантного не знайдено."
    return "\n\n".join(
        f"[{i}] (джерело: {c.source}, фрагмент {c.index})\n{c.text[:1500]}" for i, c in enumerate(chunks, 1)
    )


HANDLERS = {
    "rag_search": lambda args: run_rag_search(args["query"]),
    "calculator": lambda args: str(safe_eval(args["expression"])),
}


def execute_tool(name: str, args: dict) -> tuple[str, bool]:
    handler = HANDLERS.get(name)
    if handler is None:
        return f"Unknown tool: {name}", True
    try:
        return handler(args), False
    except Exception as exc:  # noqa: BLE001 — любая ошибка инструмента становится tool_result
        return f"{type(exc).__name__}: {exc}", True