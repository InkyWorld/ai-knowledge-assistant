from pathlib import Path

import pymupdf
from anthropic.types import TextBlock

from app.core.clients import get_anthropic
from app.ingestion.cleaner import MarkdownCleaner
from app.prompts.document_processor import PDF_TO_MARKDOWN_PROMPT


class DocumentProcessor:
    def __init__(self, cleaner: MarkdownCleaner):
        self.cleaner = cleaner

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Витягує сирий текст з PDF локально, щоб уникнути галюцинацій Claude"""
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc.pages():
            text += f"{page.get_text()}\n"
        return text

    def process(self, file_path: Path) -> str:
        raw_pdf_text = self.extract_text_from_pdf(file_path)

        response = get_anthropic().messages.create(
            model="claude-haiku-4-5",
            max_tokens=8192,
            messages=[{"role": "user", "content": f"{PDF_TO_MARKDOWN_PROMPT}\n\n<text>\n{raw_pdf_text}\n</text>"}],
        )
        if not response.content or not isinstance(response.content[0], TextBlock):
            raise ValueError("Failed to process PDF text with the API.")
        response_text = response.content[0].text

        return self.cleaner.clean(response_text)


if __name__ == "__main__":
    from pathlib import Path

    def main() -> None:
        cleaner = MarkdownCleaner()
        test_pdf_folder_input_path = Path("data/input/Про внесення змін до постанови КМУ")
        test_pdf_folder_output_path = Path("data\\markdown\\Про внесення змін до постанови КМУ")
        test_pdf_folder_output_path.mkdir(parents=True, exist_ok=True)
        for input_path in test_pdf_folder_input_path.glob("*.pdf"):
            output_file_path = test_pdf_folder_output_path / (input_path.stem + ".md")
            processor = DocumentProcessor(cleaner)
            markdown_text = processor.process(input_path)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

    main()
