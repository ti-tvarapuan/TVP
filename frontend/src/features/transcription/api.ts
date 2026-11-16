import type { TranscriptionJob } from "./types"

const API_URL = import.meta.env.VITE_API_URL || ""

async function getError(response: Response) {
  const body = await response.json().catch(() => ({}))
  return body.error || "Não foi possível processar o vídeo. Tente novamente."
}

export type ProcessingProgress = { stage: string; progress: number; message: string }

export async function transcribeVideo(file: File | string, targetLanguage: string, onProgress: (progress: ProcessingProgress) => void): Promise<TranscriptionJob> {
  const form = new FormData()
  if (typeof file === "string") form.append("url", file)
  else form.append("video", file)
  form.append("target_language", targetLanguage)
  const response = await fetch(`${API_URL}/api/subtitles`, { method: "POST", body: form })
  if (!response.ok) throw new Error(await getError(response))
  if (!response.body) throw new Error("O navegador não recebeu o fluxo de progresso do servidor.")

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const messages = buffer.split(/\r?\n\r?\n/)
    buffer = messages.pop() || ""
    for (const message of messages) {
      const event = message.match(/^event:\s*(.+)$/m)?.[1]
      const data = message.match(/^data:\s*(.+)$/m)?.[1]
      if (!event || !data) continue
      const payload = JSON.parse(data)
      if (event === "progress") onProgress(payload)
      if (event === "error") throw new Error(payload.error || "Não foi possível processar o vídeo.")
      if (event === "complete") return payload.job as TranscriptionJob
    }
    if (done) break
  }
  throw new Error("O processamento terminou sem retornar o vídeo legendado.")
}

export async function downloadYoutube(url: string) {
  const response = await fetch(`${API_URL}/api/youtube/download`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) })
  if (!response.ok) throw new Error(await getError(response))
  const objectUrl = URL.createObjectURL(await response.blob())
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = "video.mp4"
  link.click()
  URL.revokeObjectURL(objectUrl)
}

export async function downloadYoutubeAudio(url: string) {
  const response = await fetch(`${API_URL}/api/audio/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  })
  if (!response.ok) throw new Error(await getError(response))
  const objectUrl = URL.createObjectURL(await response.blob())
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = "audio.mp3"
  link.click()
  URL.revokeObjectURL(objectUrl)
}

export async function downloadVideo(job: TranscriptionJob, filename: string) {
  const response = await fetch(`${API_URL}/api/videos/with-subtitles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_path: job.video_path, subtitle_path: job.subtitle_path }),
  })
  if (!response.ok) throw new Error(await getError(response))
  const objectUrl = URL.createObjectURL(await response.blob())
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = `${filename.replace(/\.[^.]+$/, "")}_pt.mp4`
  link.click()
  URL.revokeObjectURL(objectUrl)
}

export function mediaUrl(path: string) {
  return `${API_URL}${path}`
}
