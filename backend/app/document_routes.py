"""Endpoints HTTP para tradução de documentos."""

from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app.services.document_translation import (
    DocumentTranslationError,
    DocumentTranslationService,
)
from app.services.documents import DocumentError, DocumentTooLarge, extract_document_text
from app.services.translation import OllamaTranslator


documents_bp = Blueprint("documents", __name__)


@documents_bp.post("/api/documents/translate")
def translate_document():
    max_bytes = current_app.config["MAX_DOCUMENT_SIZE_BYTES"]
    content_length = request.content_length
    if content_length is not None and content_length > max_bytes + 1024 * 1024:
        return jsonify({"error": "O arquivo excede o limite de tamanho para documentos."}), 413

    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Envie um arquivo TXT ou PDF no campo 'file'."}), 400

    filename = secure_filename(uploaded.filename)
    if not filename:
        return jsonify({"error": "O nome do arquivo é inválido."}), 400

    target_language = request.form.get("target_language", "Portuguese").strip()
    source_language = request.form.get("source_language", "auto").strip() or "auto"
    if not target_language:
        return jsonify({"error": "Informe o idioma de destino em 'target_language'."}), 400
    if len(target_language) > 80 or len(source_language) > 80:
        return jsonify({"error": "O nome do idioma não pode exceder 80 caracteres."}), 400

    content = uploaded.stream.read(max_bytes + 1)
    if len(content) > max_bytes:
        return jsonify({"error": "O arquivo excede o limite de tamanho para documentos."}), 413

    try:
        text = extract_document_text(
            filename,
            content,
            current_app.config["MAX_DOCUMENT_CHARACTERS"],
            current_app.config["MAX_DOCUMENT_PAGES"],
        )
        translator = current_app.extensions.get("translator")
        if translator is None:
            config = current_app.config
            translator = OllamaTranslator(config["OLLAMA_URL"], config["OLLAMA_MODEL"])
            current_app.extensions["translator"] = translator
        service = DocumentTranslationService(
            translator,
            current_app.config["TRANSLATION_CHUNK_CHARACTERS"],
        )
        translated_text = service.translate(text, target_language, source_language)
    except DocumentTooLarge as exc:
        return jsonify({"error": str(exc)}), 413
    except DocumentError as exc:
        return jsonify({"error": str(exc)}), 400
    except DocumentTranslationError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception:
        current_app.logger.exception("Erro inesperado ao traduzir documento")
        return jsonify({"error": "Erro interno ao traduzir o documento."}), 500

    return jsonify({
        "filename": filename,
        "source_format": Path(filename).suffix.lower().lstrip("."),
        "source_language": source_language,
        "target_language": target_language,
        "translated_text": translated_text,
    })
