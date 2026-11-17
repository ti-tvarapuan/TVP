const API_URL = import.meta.env.VITE_API_URL || ""

export type DocumentTranslation = {
  filename: string
  source_format: "txt" | "pdf"
  source_language: string
  target_language: string
  translated_text: string
}

export async function translateDocument(
  file: File,
  sourceLanguage: string,
  targetLanguage: string,
): Promise<DocumentTranslation> {
  const form = new FormData()
  form.append("file", file)
  form.append("source_language", sourceLanguage)
  form.append("target_language", targetLanguage)

  const response = await fetch(`${API_URL}/api/documents/translate`, {
    method: "POST",
    body: form,
  })
  const result = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(result.error || "Não foi possível traduzir o documento.")
  }
  return result as DocumentTranslation
}

export function downloadTranslation(filename: string, text: string) {
  const baseName = filename.replace(/\.[^.]+$/, "") || "documento"
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }))
  const link = document.createElement("a")
  link.href = url
  link.download = `${baseName}_traduzido.txt`
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
