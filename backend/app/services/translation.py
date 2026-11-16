from ollama import Client


class TranslationError(RuntimeError):
    pass


class OllamaTranslator:
    def __init__(self, base_url: str, model: str):
        self.client = Client(host=base_url.rstrip("/"))
        self.model = model

    def translate(self, text: str, target_language: str = "Portuguese") -> str:
        if not text.strip():
            return ""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Translate the following subtitle into {target_language}. "
                        "Detect its source language automatically. Preserve meaning, names, and concise subtitle style. Return only the translation.\n\n"
                        f"{text}"
                    ),
                }],
                stream=False,
            )
            translated = response.message.content.strip()
        except Exception as exc:
            raise TranslationError(f"Falha ao traduzir com Ollama ({self.model}): {exc}") from exc
        if not translated:
            raise TranslationError("O Ollama retornou uma tradução vazia.")
        return translated

    def translate_segments(self, segments: list[dict]) -> list[dict]:
        # Mantém os tempos de cada segmento do Whisper.
        return [{**segment, "text": self.translate(segment["text"])} for segment in segments]
