import type { TranscriptionJob } from "./types"

const API_URL = import.meta.env.VITE_API_URL || ""

async function getError(response: Response) {
  const body = await response.json().catch(() => ({}))
  return body.error || "Não foi possível processar o vídeo. Tente novamente."
}

export async function transcribeVideo(file: File): Promise<TranscriptionJob> {
  const form = new FormData()
  form.append("video", file)
  const response = await fetch(`${API_URL}/api/subtitles`, { method: "POST", body: form })
  if (!response.ok) throw new Error(await getError(response))
  return response.json()
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
