from pathlib import Path

import pymupdf
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

from app.core.config import settings
from app.ingestion.cleaner import MarkdownCleaner
from app.prompts.document_processor import PDF_TO_MARKDOWN_PROMPT


class DocumentProcessor:
    def __init__(self, client: AsyncAnthropic, cleaner: MarkdownCleaner):
        self.client = client
        self.cleaner = cleaner

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Витягує сирий текст з PDF локально, щоб уникнути галюцинацій Claude"""
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc.pages():
            text += f"{page.get_text()}\n"
        return text

    async def process(self, file_path: Path) -> str:
        raw_pdf_text = self.extract_text_from_pdf(file_path)

        response = await self.client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=8192,
            messages=[{"role": "user", "content": f"{PDF_TO_MARKDOWN_PROMPT}\n\n<text>\n{raw_pdf_text}\n</text>"}],
        )
        if not response.content or not isinstance(response.content[0], TextBlock):
            raise ValueError("Failed to process PDF text with the API.")
        response_text = response.content[0].text

        return self.cleaner.clean(response_text)


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    async def main() -> None:
        cleaner = MarkdownCleaner()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        test_pdf_folder_input_path = Path("data/input/Про внесення змін до постанови КМУ")
        test_pdf_folder_output_path = Path("data\\markdown\\Про внесення змін до постанови КМУ")
        test_pdf_folder_output_path.mkdir(parents=True, exist_ok=True)
        for input_path in test_pdf_folder_input_path.glob("*.pdf"):
            output_file_path = test_pdf_folder_output_path / (input_path.stem + ".md")
            processor = DocumentProcessor(client, cleaner)
            markdown_text = await processor.process(input_path)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

    asyncio.run(main())
