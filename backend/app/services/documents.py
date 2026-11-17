"""Leitura e validação de documentos enviados para tradução."""

from pathlib import Path

import fitz


class DocumentError(ValueError):
    """A entrada não é um documento compatível ou não contém texto utilizável."""


class DocumentTooLarge(DocumentError):
    """O documento excedeu um limite de tamanho configurado."""


def extract_document_text(
    filename: str,
    content: bytes,
    max_characters: int,
    max_pages: int,
) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".txt":
        text = _decode_text(content)
    elif extension == ".pdf":
        text = _extract_pdf_text(content, max_characters, max_pages)
    else:
        raise DocumentError("Formato não suportado. Envie um arquivo .txt ou .pdf.")

    text = text.strip()
    if not text:
        raise DocumentError("O documento não contém texto para traduzir.")
    if len(text) > max_characters:
        raise DocumentTooLarge("O texto extraído excede o limite de caracteres configurado.")
    return text


def _decode_text(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentError("O arquivo TXT precisa estar codificado em UTF-8.") from exc


def _extract_pdf_text(content: bytes, max_characters: int, max_pages: int) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as pdf:
            if pdf.is_encrypted:
                raise DocumentError("PDF protegido por senha não pode ser traduzido.")
            if len(pdf) > max_pages:
                raise DocumentTooLarge(f"O PDF excede o limite de {max_pages} páginas.")

            pages = []
            total_characters = 0
            for page in pdf:
                page_text = page.get_text("text", sort=True).strip()
                if not page_text:
                    continue
                total_characters += len(page_text)
                if total_characters > max_characters:
                    raise DocumentTooLarge("O texto extraído excede o limite de caracteres configurado.")
                pages.append(page_text)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("Não foi possível ler o PDF. Verifique se o arquivo está íntegro.") from exc

    text = "\n\n".join(pages)
    if not text.strip():
        raise DocumentError(
            "O PDF não contém texto selecionável. PDFs escaneados precisam passar por OCR antes do envio."
        )
    return text
