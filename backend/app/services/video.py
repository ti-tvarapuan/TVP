import subprocess
from pathlib import Path

from app.services.media import MediaError


def embed_subtitles(video_path: Path, subtitle_path: Path, output_path: Path, ffmpeg_binary: str) -> None:
    command = [
        ffmpeg_binary, "-y", "-i", str(video_path), "-i", str(subtitle_path),
        "-map", "0:v:0", "-map", "0:a?", "-map", "1:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-c:s", "mov_text", "-metadata:s:s:0", "language=por",
        "-movflags", "+faststart", str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg não foi encontrado. Verifique FFMPEG_BINARY e o PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-1500:]
        raise MediaError(f"Não foi possível incorporar a legenda: {detail}") from exc
