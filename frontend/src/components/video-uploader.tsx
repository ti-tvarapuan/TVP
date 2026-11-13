import { useState } from "react"
import { ArrowRight, LoaderCircle, UploadCloud } from "lucide-react"

type VideoUploaderProps = { onFile: (file: File) => void; busy: boolean }

export function VideoUploader({ onFile, busy }: VideoUploaderProps) {
  const [dragging, setDragging] = useState(false)
  const [invalid, setInvalid] = useState("")
  const accept = (file?: File) => {
    if (!file) return
    if (!file.type.startsWith("video/") && !/\.(mp4|mov|mkv|avi|webm|mpeg|mpg)$/i.test(file.name)) {
      setInvalid("Escolha um arquivo de vídeo, como MP4, MOV ou WEBM.")
      return
    }
    setInvalid("")
    onFile(file)
  }
  return <div className={`dropzone${dragging ? " is-dragging" : ""}`} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); accept(event.dataTransfer.files[0]) }}>
    <input className="file-input" id="video-file" type="file" accept="video/*,.mkv,.mpeg,.mpg" onChange={(event) => accept(event.target.files?.[0])} disabled={busy} />
    <div className="upload-icon"><UploadCloud size={25} strokeWidth={1.7} /></div>
    <h2>{busy ? "Estamos preparando sua legenda" : "Arraste seu vídeo para cá"}</h2>
    <p className="drop-description">Seu vídeo em inglês ganha uma legenda em português em poucos instantes.</p>
    {busy ? <div className="upload-progress"><LoaderCircle className="spin" size={17} /> Transcrevendo e traduzindo…</div> : <label className="select-file" htmlFor="video-file">ou escolha um arquivo <ArrowRight size={15} /></label>}
    <p className="file-hint">MP4, MOV, MKV, AVI ou WEBM <span>·</span> até 2 GB</p>
    {invalid && <p className="inline-error" role="alert">{invalid}</p>}
  </div>
}
