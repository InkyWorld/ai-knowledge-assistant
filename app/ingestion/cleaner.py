import re


class MarkdownCleaner:
    def clean(self, markdown: str) -> str:
        markdown = self._remove_bold_from_headings(markdown)
        markdown = self._remove_double_bold(markdown)
        markdown = self._remove_escaped_parentheses(markdown)
        markdown = self._remove_service_sections(markdown)
        markdown = self._normalize_horizontal_rules(markdown)
        markdown = self._normalize_whitespace(markdown)

        return markdown.strip()

    @staticmethod
    def _remove_bold_from_headings(markdown: str) -> str:
        """
        **# Заголовок** -> # Заголовок
        **## Заголовок** -> ## Заголовок
        **### Заголовок** -> ### Заголовок
        """
        return re.sub(
            r"^\s*\*\*(#{1,6})\s*(.*?)\*\*\s*$",
            r"\1 \2",
            markdown,
            flags=re.MULTILINE,
        )

    @staticmethod
    def _remove_double_bold(markdown: str) -> str:
        r"""
        Убирает случайное двойное форматирование:

        **\*\*текст:\*\***
        ->
        текст:
        """

        markdown = markdown.replace(r"\*\*", "")

        markdown = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            markdown,
        )

        return markdown

    @staticmethod
    def _remove_escaped_parentheses(markdown: str) -> str:
        r"""
        1\) -> 1)
        """
        return re.sub(
            r"(\d+)\\\)",
            r"\1)",
            markdown,
        )

    @staticmethod
    def _remove_service_sections(markdown: str) -> str:
        """
        Удаляет служебную информацию zakon.rada.gov.ua,
        которая не является содержанием нормативного акта.
        """

        service_headers = (
            "Публікації документа",
            "Реквізити",
            "Законодавство України станом",
        )

        lines = markdown.splitlines()
        result: list[str] = []

        skip = False

        for line in lines:
            stripped = line.strip()

            if any(
                stripped.startswith(f"# {header}")
                or stripped.startswith(f"## {header}")
                or stripped.startswith(f"### {header}")
                for header in service_headers
            ):
                skip = True
                continue

            if skip and stripped.startswith("#"):
                skip = False

            if not skip:
                result.append(line)

        return "\n".join(result)

    @staticmethod
    def _normalize_horizontal_rules(markdown: str) -> str:
        """
        --- остаётся валидным Markdown-разделителем.
        Убираем дубликаты.
        """
        return re.sub(
            r"(?:\n---\n){2,}",
            "\n---\n",
            markdown,
        )

    @staticmethod
    def _normalize_whitespace(markdown: str) -> str:
        """
        Убирает лишние пустые строки.
        Максимум две пустые строки подряд.
        """
        markdown = re.sub(
            r"\n{3,}",
            "\n\n",
            markdown,
        )

        return markdown.strip()
