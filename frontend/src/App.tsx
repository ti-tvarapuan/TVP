import { useCallback, useState } from "react"
import { Sparkles } from "lucide-react"
import { SiteHeader } from "@/components/brand"
import { VideoResult } from "@/components/video-result"
import { VideoUploader } from "@/components/video-uploader"
import { transcribeVideo } from "@/features/transcription/api"
import type { TranscriptionJob } from "@/features/transcription/types"

export function App() {
  const [job, setJob] = useState<TranscriptionJob | null>(null)
  const [fileName, setFileName] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const handleFile = useCallback(async (file: File) => {
    setBusy(true); setError(""); setJob(null); setFileName(file.name)
    try { setJob(await transcribeVideo(file)) } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível processar o vídeo.") } finally { setBusy(false) }
  }, [])
  return <div className="app-shell" id="inicio">
    <SiteHeader />
    <main className="main-content">
      <section className="hero"><div className="eyebrow"><span className="eyebrow-line" /> SEU VÍDEO, AGORA EM PORTUGUÊS</div><h1>Entenda cada palavra.<br /><span>Sem perder o ritmo.</span></h1><p>Envie um vídeo em inglês. A gente transcreve, traduz e prepara tudo para você assistir com legendas em português.</p></section>
      <div className="workspace">{job ? <VideoResult job={job} name={fileName} onReset={() => { setJob(null); setFileName(""); setError("") }} /> : <VideoUploader onFile={handleFile} busy={busy} />}{error && <p className="inline-error main-error" role="alert">{error}</p>}</div>
      <section className="steps" id="como-funciona"><div className="step"><span className="step-number">01</span><div><strong>Envie seu vídeo</strong><p>Escolha um arquivo do seu dispositivo.</p></div></div><span className="step-divider" /><div className="step"><span className="step-number">02</span><div><strong>Deixe com a gente</strong><p>Transcrição e tradução em um só passo.</p></div></div><span className="step-divider" /><div className="step"><span className="step-number">03</span><div><strong>Assista e baixe</strong><p>Veja com legenda ou salve o vídeo.</p></div></div></section>
    </main>
    <footer className="site-footer"><span>Feito para aproximar você de cada história.</span><span className="footer-brand">TVP <Sparkles size={13} /></span></footer>
  </div>
}

export default App
