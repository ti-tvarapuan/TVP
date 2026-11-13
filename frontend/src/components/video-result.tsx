import { useState } from "react"
import { ArrowDownToLine, Check, FileVideo, Languages, LoaderCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { downloadVideo, mediaUrl } from "@/features/transcription/api"
import type { TranscriptionJob } from "@/features/transcription/types"

type VideoResultProps = { job: TranscriptionJob; name: string; onReset: () => void }

export function VideoResult({ job, name, onReset }: VideoResultProps) {
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState("")
  const handleDownload = async () => {
    setDownloading(true)
    setError("")
    try { await downloadVideo(job, name) } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha ao preparar o download.") } finally { setDownloading(false) }
  }
  return <section className="result-card" aria-label="Vídeo transcrito">
    <div className="result-topline"><div className="ready-label"><span className="ready-dot"><Check size={11} /></span> Legenda pronta</div><button className="text-action" onClick={onReset}>Transcrever outro vídeo</button></div>
    <div className="video-frame"><video controls playsInline crossOrigin="anonymous" src={mediaUrl(job.video_url)}><track default kind="subtitles" srcLang="pt-BR" label="Português" src={mediaUrl(job.subtitle_url)} /></video></div>
    <div className="video-caption"><div className="video-file-icon"><FileVideo size={19} /></div><div className="video-file-copy"><strong>{name}</strong><span>Áudio original · Legenda em português</span></div><span className="language-pill"><Languages size={13} /> PT-BR</span></div>
    <div className="download-row"><div><strong>Pronto para assistir offline?</strong><span>Baixe o vídeo com a legenda incluída.</span></div><Button className="download-button" onClick={handleDownload} disabled={downloading}>{downloading ? <LoaderCircle className="spin" /> : <ArrowDownToLine />} {downloading ? "Preparando…" : "Baixar vídeo"}</Button></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>
}
