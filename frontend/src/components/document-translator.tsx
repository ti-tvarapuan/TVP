import { useRef, useState } from "react"
import { ArrowDownToLine, Clipboard, FileText, Languages, LoaderCircle, UploadCloud } from "lucide-react"
import { downloadTranslation, translateDocument, type DocumentTranslation } from "@/features/documents/api"

const LANGUAGES = ["Portuguese", "English", "Spanish", "French", "German", "Italian", "Japanese", "Chinese", "Arabic"]
const MAX_FILE_BYTES = 25 * 1024 * 1024

export function DocumentTranslator() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [sourceLanguage, setSourceLanguage] = useState("auto")
  const [targetLanguage, setTargetLanguage] = useState("Portuguese")
  const [result, setResult] = useState<DocumentTranslation | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [copied, setCopied] = useState(false)

  const chooseFile = (candidate?: File) => {
    if (!candidate) return
    if (!/\.(txt|pdf)$/i.test(candidate.name)) {
      setFile(null)
      setResult(null)
      setError("Escolha um arquivo TXT ou PDF.")
      return
    }
    if (candidate.size > MAX_FILE_BYTES) {
      setFile(null)
      setResult(null)
      setError("O arquivo deve ter no máximo 25 MB.")
      return
    }
    setFile(candidate)
    setResult(null)
    setCopied(false)
    setError("")
  }

  const submit = async () => {
    if (!file) return
    setBusy(true)
    setError("")
    setResult(null)
    try {
      setResult(await translateDocument(file, sourceLanguage, targetLanguage))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível traduzir o documento.")
    } finally {
      setBusy(false)
    }
  }

  const copyResult = async () => {
    if (!result) return
    try {
      await navigator.clipboard.writeText(result.translated_text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setError("Não foi possível copiar. Selecione o texto e copie manualmente.")
    }
  }

  return <section className="document-module" aria-labelledby="document-title">
    <div className="document-heading">
      <span className="document-icon"><Languages size={19} /></span>
      <div><h2 id="document-title">Traduzir documento</h2><p>Envie um arquivo TXT ou PDF para traduzir com TranslateGemma.</p></div>
    </div>

    <div className="document-controls">
      <input ref={inputRef} className="file-input" type="file" accept=".txt,.pdf,text/plain,application/pdf" onChange={(event) => { chooseFile(event.target.files?.[0]); event.currentTarget.value = "" }} />
      <button className="document-file-picker" type="button" onClick={() => inputRef.current?.click()} disabled={busy}>
        <UploadCloud size={18} /><span>{file ? file.name : "Escolher arquivo TXT ou PDF"}</span><small>{file ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` : "Até 25 MB"}</small>
      </button>

      <label className="document-language" htmlFor="document-source">Idioma de origem
        <select id="document-source" value={sourceLanguage} onChange={(event) => setSourceLanguage(event.target.value)} disabled={busy}>
          <option value="auto">Detectar automaticamente</option>
          {LANGUAGES.map((language) => <option key={language} value={language}>{language}</option>)}
        </select>
      </label>
      <label className="document-language" htmlFor="document-target">Traduzir para
        <select id="document-target" value={targetLanguage} onChange={(event) => setTargetLanguage(event.target.value)} disabled={busy}>
          {LANGUAGES.map((language) => <option key={language} value={language}>{language}</option>)}
        </select>
      </label>
      <button className="document-submit" type="button" onClick={() => void submit()} disabled={!file || busy}>
        {busy ? <LoaderCircle className="spin" size={16} /> : <Languages size={16} />}
        {busy ? "Traduzindo…" : "Traduzir documento"}
      </button>
    </div>

    <p className="document-note"><FileText size={14} /> PDFs escaneados precisam passar por OCR antes do envio.</p>
    {error && <p className="inline-error" role="alert">{error}</p>}

    {result && <div className="document-result" aria-live="polite">
      <div className="document-result-heading">
        <div><strong>Tradução pronta</strong><span>{result.filename} · {result.target_language}</span></div>
        <div className="document-result-actions">
          <button type="button" onClick={() => void copyResult()}><Clipboard size={14} /> {copied ? "Copiado" : "Copiar"}</button>
          <button type="button" onClick={() => downloadTranslation(result.filename, result.translated_text)}><ArrowDownToLine size={14} /> Baixar TXT</button>
        </div>
      </div>
      <pre className="document-translation">{result.translated_text}</pre>
    </div>}
  </section>
}
