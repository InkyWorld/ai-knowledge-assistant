
from dataclasses import dataclass
from datetime import date

from app.core.clients import get_anthropic
from app.core.config import settings
from app.prompts.sql import SQL_SYSTEM

SUBMIT_SQL = {
    "name": "submit_sql",
    "description": "Передає згенерований SQL (або порожній рядок, якщо запит неможливо побудувати) "
                   "і коротке пояснення.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Один SELECT для PostgreSQL або порожній рядок"},
            "reason": {"type": "string", "description": "Пояснення логіки або причина відмови"},
        },
        "required": ["sql", "reason"],
    },
}


@dataclass
class GeneratedSQL:
    sql: str
    reason: str


def generate_sql(question: str) -> GeneratedSQL:
    response = get_anthropic().messages.create(
        model=settings.anthropic_model, max_tokens=500,
        system=SQL_SYSTEM.format(today=date.today().isoformat()),
        tools=[SUBMIT_SQL], tool_choice={"type": "tool", "name": "submit_sql"},
        messages=[{"role": "user", "content": question}],
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return GeneratedSQL(sql=block.input.get("sql", "").strip(), reason=block.input.get("reason", ""))