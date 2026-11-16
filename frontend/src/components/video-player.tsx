import { useEffect, useRef, useState, type CSSProperties } from "react"
import { Captions, Maximize, Minimize, Pause, Play, Volume2, VolumeX } from "lucide-react"
import "./video-player.css"

type VideoPlayerProps = {
  src: string
  subtitleSrc: string
  subtitleLabel?: string
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) return "0:00"
  const wholeSeconds = Math.floor(seconds)
  return `${Math.floor(wholeSeconds / 60)}:${String(wholeSeconds % 60).padStart(2, "0")}`
}

export function VideoPlayer({ src, subtitleSrc, subtitleLabel = "Português" }: VideoPlayerProps) {
  const frameRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [captionsOn, setCaptionsOn] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    const updateTime = () => setCurrentTime(video.currentTime)
    const updateDuration = () => setDuration(video.duration || 0)
    const updatePlayState = () => setPlaying(!video.paused)
    video.addEventListener("timeupdate", updateTime)
    video.addEventListener("loadedmetadata", updateDuration)
    video.addEventListener("durationchange", updateDuration)
    video.addEventListener("play", updatePlayState)
    video.addEventListener("pause", updatePlayState)
    return () => {
      video.removeEventListener("timeupdate", updateTime)
      video.removeEventListener("loadedmetadata", updateDuration)
      video.removeEventListener("durationchange", updateDuration)
      video.removeEventListener("play", updatePlayState)
      video.removeEventListener("pause", updatePlayState)
    }
  }, [])

  useEffect(() => {
    const updateFullscreen = () => setFullscreen(document.fullscreenElement === frameRef.current)
    document.addEventListener("fullscreenchange", updateFullscreen)
    return () => document.removeEventListener("fullscreenchange", updateFullscreen)
  }, [])

  useEffect(() => {
    const track = videoRef.current?.textTracks[0]
    if (track) track.mode = captionsOn ? "showing" : "hidden"
  }, [captionsOn])

  const togglePlayback = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) void video.play()
    else video.pause()
  }
  const toggleFullscreen = async () => {
    if (!frameRef.current) return
    if (document.fullscreenElement) await document.exitFullscreen()
    else await frameRef.current.requestFullscreen()
  }

  return <div className="tvp-player" ref={frameRef}>
    <video
      ref={videoRef}
      className="tvp-player-video"
      playsInline
      preload="metadata"
      src={src}
      controlsList="nodownload noplaybackrate"
      disablePictureInPicture
      onClick={togglePlayback}
      onContextMenu={(event) => event.preventDefault()}
    >
      <track default kind="subtitles" srcLang="pt-BR" label={subtitleLabel} src={subtitleSrc} />
    </video>
    <div className="tvp-player-controls" aria-label="Controles do vídeo">
      <button type="button" className="tvp-control-button tvp-play-button" onClick={togglePlayback} aria-label={playing ? "Pausar" : "Reproduzir"}>
        {playing ? <Pause size={17} fill="currentColor" /> : <Play size={17} fill="currentColor" />}
      </button>
      <span className="tvp-time">{formatTime(currentTime)} <span>/</span> {formatTime(duration)}</span>
      <input className="tvp-seek" type="range" min={0} max={duration || 0} step={0.1} value={Math.min(currentTime, duration || 0)} onChange={(event) => { if (videoRef.current) videoRef.current.currentTime = Number(event.target.value) }} aria-label="Posição do vídeo" style={{ "--seek-progress": `${duration ? currentTime / duration * 100 : 0}%` } as CSSProperties} />
      <button type="button" className={`tvp-control-button${captionsOn ? " is-active" : ""}`} onClick={() => setCaptionsOn((value) => !value)} aria-label={captionsOn ? "Desativar legendas" : "Ativar legendas"} aria-pressed={captionsOn}><Captions size={18} /></button>
      <button type="button" className="tvp-control-button tvp-volume-button" onClick={() => setMuted((value) => !value)} aria-label={muted || volume === 0 ? "Ativar áudio" : "Silenciar"}>{muted || volume === 0 ? <VolumeX size={17} /> : <Volume2 size={17} />}</button>
      <input className="tvp-volume" type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(event) => { const next = Number(event.target.value); setVolume(next); setMuted(next === 0); if (videoRef.current) videoRef.current.volume = next }} aria-label="Volume" style={{ "--volume-progress": `${muted ? 0 : volume * 100}%` } as CSSProperties} />
      <button type="button" className="tvp-control-button" onClick={() => void toggleFullscreen()} aria-label={fullscreen ? "Sair da tela cheia" : "Tela cheia"}>{fullscreen ? <Minimize size={17} /> : <Maximize size={17} />}</button>
    </div>
  </div>
}
