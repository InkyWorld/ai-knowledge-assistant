import base64

from anthropic import AsyncAnthropic

from app.core.config import settings


async def parse_pdf_to_markdown(file_path: str, client: AsyncAnthropic) -> str:

    # Read the PDF file and encode its content as Base64
    with open(file_path, "rb") as pdf_file:
        pdf_content = pdf_file.read()
        encoded_pdf = base64.b64encode(pdf_content).decode("utf-8")

    # Build the system prompt
    system_prompt = (
        "Your task is to extract all text, tables, and data from this document "
        "and return them in Markdown format without your own additions or comments."
    )

    # Build the model request
    response = await client.messages.create(
        model=settings.anthropic_model,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": encoded_pdf,
                        },
                    }
                ],
            },
        ],
        max_tokens=5000,
    )

    # Extract text from the model response
    markdown_output = response.content[0].text
    return markdown_output


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    async def main() -> None:
        input_path = Path("data/input.pdf")
        output_path = Path("data/output/output.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        markdown = await parse_pdf_to_markdown(str(input_path), client)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

    asyncio.run(main())
