from ollama import Client


class TranslationError(RuntimeError):
    pass


_LANGUAGES = {
    "ar": ("Arabic", "ar"),
    "arabic": ("Arabic", "ar"),
    "de": ("German", "de"),
    "german": ("German", "de"),
    "en": ("English", "en"),
    "english": ("English", "en"),
    "es": ("Spanish", "es"),
    "spanish": ("Spanish", "es"),
    "fr": ("French", "fr"),
    "french": ("French", "fr"),
    "hi": ("Hindi", "hi"),
    "hindi": ("Hindi", "hi"),
    "it": ("Italian", "it"),
    "italian": ("Italian", "it"),
    "ja": ("Japanese", "ja"),
    "japanese": ("Japanese", "ja"),
    "ko": ("Korean", "ko"),
    "korean": ("Korean", "ko"),
    "nl": ("Dutch", "nl"),
    "dutch": ("Dutch", "nl"),
    "pt": ("Portuguese", "pt"),
    "portuguese": ("Portuguese", "pt"),
    "português": ("Portuguese", "pt"),
    "brazilian portuguese": ("Portuguese", "pt-BR"),
    "português brasileiro": ("Portuguese", "pt-BR"),
    "ru": ("Russian", "ru"),
    "russian": ("Russian", "ru"),
    "tr": ("Turkish", "tr"),
    "turkish": ("Turkish", "tr"),
    "zh": ("Chinese", "zh"),
    "chinese": ("Chinese", "zh"),
}


def _language_name_and_code(language: str) -> tuple[str, str]:
    normalized = language.strip().lower().replace("_", "-")
    if normalized in _LANGUAGES:
        return _LANGUAGES[normalized]
    if "-" in normalized:
        base = normalized.split("-", 1)[0]
        known = _LANGUAGES.get(base)
        if known:
            return known[0], language.strip()
    return language.strip(), ""


def _language_label(name: str, code: str) -> str:
    return f"{name} ({code})" if code else name


class OllamaTranslator:
    def __init__(self, base_url: str, model: str):
        self.client = Client(host=base_url.rstrip("/"))
        self.model = model

    def translate(
        self,
        text: str,
        target_language: str = "Portuguese",
        source_language: str = "auto",
        content_type: str = "general",
    ) -> str:
        if not text.strip():
            return ""
        target_name, target_code = _language_name_and_code(target_language)
        target_label = _language_label(target_name, target_code)
        style_instruction = (
            " Preserve names and use concise subtitle phrasing."
            if content_type == "subtitle" else ""
        )
        if source_language.strip().lower() in {"", "auto", "automatic", "detect"}:
            source_instruction = "Detect the source language automatically."
            prompt = (
                f"You are a professional multilingual translator. {source_instruction} "
                f"Translate the text into {target_label}, accurately conveying "
                f"its meaning and nuances while using natural grammar and vocabulary.{style_instruction} "
                f"Produce only the {target_name} translation, without explanations or commentary. "
                f"Please translate the following text into {target_name}:\n\n\n{text}"
            )
        else:
            source_name, source_code = _language_name_and_code(source_language)
            source_label = _language_label(source_name, source_code)
            prompt = (
                f"You are a professional {source_label} to "
                f"{target_label} translator. Accurately convey the meaning and "
                f"nuances of the original text using natural {target_name} grammar and vocabulary.{style_instruction} "
                f"Produce only the {target_name} translation, without explanations or commentary. "
                f"Please translate the following {source_name} text into {target_name}:\n\n\n{text}"
            )
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt,
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
        return [
            {**segment, "text": self.translate(segment["text"], content_type="subtitle")}
            for segment in segments
        ]
