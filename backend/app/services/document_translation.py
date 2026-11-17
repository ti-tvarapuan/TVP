"""Orquestra a tradução de documentos em blocos compatíveis com o modelo."""

import re

from app.services.translation import TranslationError


class DocumentTranslationError(RuntimeError):
    pass


class DocumentTranslationService:
    def __init__(self, translator, chunk_characters: int = 2500):
        self.translator = translator
        self.chunk_characters = chunk_characters

    def translate(
        self,
        text: str,
        target_language: str = "Portuguese",
        source_language: str = "auto",
    ) -> str:
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text.strip())]
        translated_paragraphs = []
        try:
            for paragraph in filter(None, paragraphs):
                chunks = _split_paragraph(paragraph, self.chunk_characters)
                translated_chunks = [
                    self.translator.translate(chunk, target_language, source_language)
                    for chunk in chunks
                ]
                translated_paragraphs.append(" ".join(translated_chunks))
        except TranslationError as exc:
            raise DocumentTranslationError(str(exc)) from exc
        return "\n\n".join(translated_paragraphs)


def _split_paragraph(paragraph: str, limit: int) -> list[str]:
    if len(paragraph) <= limit:
        return [paragraph]

    chunks = []
    current = ""
    for word in paragraph.split():
        if current and len(current) + len(word) + 1 > limit:
            chunks.append(current)
            current = word
        elif not current:
            current = word
        else:
            current = f"{current} {word}"

        # A single unusually long token still must make progress through the
        # model instead of silently exceeding the configured prompt size.
        while len(current) > limit:
            chunks.append(current[:limit])
            current = current[limit:]

    if current:
        chunks.append(current)
    return chunks
