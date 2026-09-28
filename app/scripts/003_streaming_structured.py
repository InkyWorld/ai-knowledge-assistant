import asyncio
import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
MODEL = os.getenv("ANTHROPIC_MODEL", "")
client = AsyncAnthropic()


class TextAnalysis(BaseModel):
    summary: str
    sentiment: str
    key_entities: list[str]


async def structured_output_demo():
    print("--- Structured Output Demo ---")
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[
            {
                "name": "record_analysis",
                "description": "Сохранить результаты анализа текста.",
                "input_schema": TextAnalysis.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "record_analysis"},
        messages=[
            {
                "role": "user",
                "content": "Проанализируй текст: FastAPI — крутой фреймворк, но иногда меня напрягают миграции в SQLAlchemy.",
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use":
            result = TextAnalysis(**block.input)
            print(f"Summary: {result.summary}\nSentiment: {result.sentiment}\nEntities: {result.key_entities}")


async def streaming_demo():
    print("\n--- Streaming Demo ---")
    async with client.messages.stream(
        max_tokens=1024,
        messages=[{"role": "user", "content": "Напиши 3 причины использовать Pydantic, очень кратко."}],
        model=MODEL,
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(structured_output_demo())
    asyncio.run(streaming_demo())
