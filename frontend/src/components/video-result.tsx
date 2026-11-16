import { useState } from "react"
import { ArrowDownToLine, Check, FileAudio, FileVideo, LoaderCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { downloadVideo, mediaUrl } from "@/features/transcription/api"
import type { TranscriptionJob } from "@/features/transcription/types"
import { VideoPlayer } from "@/components/video-player"

type VideoResultProps = { job: TranscriptionJob; name: string; language?: string; onReset: () => void }
const AUDIO_EXTENSION = /\.(mp3|wav|m4a|aac|ogg|flac|opus|weba|aiff|aif|wma)$/i

export function VideoResult({ job, name, language = "Portuguese", onReset }: VideoResultProps) {
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState("")
  const isAudio = AUDIO_EXTENSION.test(name)
  const handleDownload = async () => {
    setDownloading(true)
    setError("")
    try { await downloadVideo(job, name) } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha ao preparar o download.") } finally { setDownloading(false) }
  }

  return <section className={`result-card${isAudio ? " audio-result" : ""}`} aria-label={isAudio ? "Áudio legendado" : "Vídeo legendado"}>
    <div className="result-topline"><div className="ready-label"><span className="ready-dot"><Check size={12} /></span> Legenda pronta</div><button className="text-action" onClick={onReset}>Novo arquivo</button></div>
    {isAudio ? <div className="audio-playback"><FileAudio size={22} /><audio controls preload="metadata" src={mediaUrl(job.video_url)}><track default kind="subtitles" srcLang="pt" label={language} src={mediaUrl(job.subtitle_url)} /></audio></div> : <div className="video-frame"><VideoPlayer src={mediaUrl(job.video_url)} subtitleSrc={mediaUrl(job.subtitle_url)} subtitleLabel={language} /></div>}
    <div className="video-caption"><div className="video-file-icon">{isAudio ? <FileAudio size={18} /> : <FileVideo size={18} />}</div><div className="video-file-copy"><strong>{name}</strong><span>Legenda: {language}</span></div></div>
    <div className="download-row">
      <div><strong>{isAudio ? "Arquivos prontos" : "Vídeo com legenda"}</strong><span>{isAudio ? "Baixe o áudio e a legenda." : "Baixe uma cópia com as legendas."}</span></div>
      {isAudio ? <div className="audio-downloads"><a href={mediaUrl(job.video_url)} download><ArrowDownToLine size={15} /> Áudio</a><a href={mediaUrl(job.subtitle_url)} download><ArrowDownToLine size={15} /> Legenda</a></div> : <Button className="download-button" onClick={handleDownload} disabled={downloading}>{downloading ? <LoaderCircle className="spin" /> : <ArrowDownToLine />} {downloading ? "Preparando…" : "Baixar vídeo"}</Button>}
    </div>
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>
}
