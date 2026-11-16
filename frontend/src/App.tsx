import { useCallback, useState } from "react"
import { AudioLines, Captions, Download, Link2 } from "lucide-react"
import { SiteHeader } from "@/components/brand"
import { VideoResult } from "@/components/video-result"
import { VideoUploader } from "@/components/video-uploader"
import { downloadYoutube, downloadYoutubeAudio, transcribeVideo, type ProcessingProgress } from "@/features/transcription/api"
import type { TranscriptionJob } from "@/features/transcription/types"

const IDIOMAS = ["Portuguese", "English", "Spanish", "French", "German", "Italian", "Japanese", "Chinese", "Arabic"]

export function App() {
  const [job, setJob] = useState<TranscriptionJob | null>(null)
  const [fileName, setFileName] = useState("")
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState<ProcessingProgress>({ stage: "uploading", progress: 0, message: "Preparando arquivo…" })
  const [error, setError] = useState("")
  const [youtubeUrl, setYoutubeUrl] = useState("")
  const [targetLanguage, setTargetLanguage] = useState("Portuguese")

  const handleFile = useCallback(async (file: File) => {
    setBusy(true)
    setError("")
    setJob(null)
    setFileName(file.name)
    setProgress({ stage: "uploading", progress: 0, message: "Enviando arquivo…" })
    try {
      setJob(await transcribeVideo(file, targetLanguage, setProgress))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível processar o arquivo.")
    } finally {
      setBusy(false)
    }
  }, [targetLanguage])

  const handleYoutube = async (action: "video" | "audio" | "subtitles") => {
    setBusy(true)
    setError("")
    const actionMessage = action === "video" ? "Baixando vídeo…" : action === "audio" ? "Extraindo áudio…" : "Preparando vídeo do YouTube…"
    setProgress({ stage: "downloading", progress: 2, message: actionMessage })
    try {
      if (action === "video") {
        await downloadYoutube(youtubeUrl)
      } else if (action === "audio") {
        await downloadYoutubeAudio(youtubeUrl)
      } else {
        setFileName("Vídeo do YouTube")
        setJob(await transcribeVideo(youtubeUrl, targetLanguage, setProgress))
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível processar a URL.")
    } finally {
      setBusy(false)
    }
  }

  return <div className="app-shell" id="inicio">
    <SiteHeader />
    <main className="main-content">
      <section className="hero">
        <span className="eyebrow">VÍDEOS E ÁUDIOS, DO SEU JEITO</span>
        <h1>O que vamos fazer hoje?</h1>
      </section>

      <section className="workspace" aria-label="Baixar ou legendar mídia">
        {job ? <VideoResult job={job} name={fileName} language={targetLanguage} onReset={() => { setJob(null); setFileName(""); setError("") }} /> : <>
          <div className="youtube-form">
            <label htmlFor="youtube-url"><Link2 size={16} /> Link do YouTube</label>
            <input id="youtube-url" value={youtubeUrl} onChange={(event) => setYoutubeUrl(event.target.value)} placeholder="Cole a URL do vídeo" disabled={busy} />
            <label className="language-select" htmlFor="target-language">Idioma da legenda
              <select id="target-language" value={targetLanguage} onChange={(event) => setTargetLanguage(event.target.value)} disabled={busy}>
                {IDIOMAS.map((language) => <option key={language} value={language}>{language}</option>)}
              </select>
            </label>
            <div className="youtube-actions">
              <button className="primary-action" disabled={busy || !youtubeUrl.trim()} onClick={() => void handleYoutube("subtitles")}><Captions size={16} /> Legendar</button>
              <button disabled={busy || !youtubeUrl.trim()} onClick={() => void handleYoutube("video")}><Download size={15} /> Vídeo</button>
              <button disabled={busy || !youtubeUrl.trim()} onClick={() => void handleYoutube("audio")}><AudioLines size={15} /> Áudio</button>
            </div>
            {busy && <p className="form-status" role="status">{progress.message} {progress.progress > 0 ? `${progress.progress}%` : ""}</p>}
          </div>

          <div className="or-divider"><span>ou</span></div>
          <VideoUploader onFile={handleFile} busy={busy} progress={progress} />
        </>}
        {error && <p className="inline-error main-error" role="alert">{error}</p>}
      </section>

      <section className="about-section" id="sobre">
        <span className="eyebrow">SOBRE A TVP</span>
        <p>Aqui você pode baixar vídeos e áudios do YouTube ou da sua máquina e também legendá-los em vários idiomas.</p>
      </section>
    </main>
  </div>
}

export default App
