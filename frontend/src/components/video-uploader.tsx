import { useRef, useState } from "react"
import { ArrowRight, LoaderCircle, UploadCloud } from "lucide-react"
import type { ProcessingProgress } from "@/features/transcription/api"

type VideoUploaderProps = { onFile: (file: File) => void; busy: boolean; progress: ProcessingProgress }
const ACCEPTED_EXTENSION = /\.(mp4|mov|mkv|avi|webm|mpeg|mpg|mp3|wav|m4a|aac|ogg|flac|opus|weba|aiff|aif|wma)$/i

export function VideoUploader({ onFile, busy, progress }: VideoUploaderProps) {
  const [dragging, setDragging] = useState(false)
  const [invalid, setInvalid] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const accept = (file?: File) => {
    if (!file) return
    if (!file.type.startsWith("video/") && !file.type.startsWith("audio/") && !ACCEPTED_EXTENSION.test(file.name)) {
      setInvalid("Escolha um arquivo de vídeo ou áudio compatível.")
      return
    }
    setInvalid("")
    onFile(file)
  }

  return <div className={`dropzone${dragging ? " is-dragging" : ""}`} role="button" tabIndex={busy ? -1 : 0} aria-label="Escolha ou solte um arquivo de vídeo ou áudio" aria-disabled={busy} onClick={() => { if (!busy) inputRef.current?.click() }} onKeyDown={(event) => { if (!busy && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); inputRef.current?.click() } }} onDragOver={(event) => { event.preventDefault(); if (!busy) setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); if (!busy) accept(event.dataTransfer.files[0]) }}>
    <input ref={inputRef} className="file-input" id="video-file" type="file" accept="video/*,audio/*,.mkv,.mpeg,.mpg,.m4a,.aac,.ogg,.flac" onClick={(event) => event.stopPropagation()} onChange={(event) => { accept(event.target.files?.[0]); event.currentTarget.value = "" }} disabled={busy} />
    <div className="upload-icon"><UploadCloud size={24} strokeWidth={1.7} /></div>
    <h2>{busy ? "Preparando legenda" : "Enviar vídeo ou áudio"}</h2>
    <p className="drop-description">Solte seu arquivo aqui ou escolha no dispositivo.</p>
    {busy ? <div className="processing-progress" role="status" aria-live="polite">
      <div className="progress-copy"><LoaderCircle className="spin" size={16} /><span>{progress.message}</span><strong>{progress.progress > 0 ? `${progress.progress}%` : ""}</strong></div>
      <div className="progress-track" role="progressbar" aria-label="Progresso do processamento" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress.progress}><span style={{ width: `${progress.progress}%` }} /></div>
      <div className="progress-stages"><span className={progress.progress >= 15 ? "done" : ""}>Áudio</span><span className={progress.progress >= 30 ? "done" : ""}>Transcrição</span><span className={progress.progress >= 65 ? "done" : ""}>Tradução</span></div>
    </div> : <span className="select-file">Escolher arquivo <ArrowRight size={15} /></span>}
    <p className="file-hint">Vídeo ou áudio <span>·</span> até 2 GB</p>
    {invalid && <p className="inline-error" role="alert">{invalid}</p>}
  </div>
}
