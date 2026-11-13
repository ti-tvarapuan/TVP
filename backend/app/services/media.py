import subprocess
from pathlib import Path


class MediaError(RuntimeError):
    pass


def extract_audio(video_path: Path, audio_path: Path, ffmpeg_binary: str) -> None:
    command = [
        ffmpeg_binary, "-y", "-i", str(video_path), "-vn",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg não foi encontrado. Verifique FFMPEG_BINARY e o PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-1000:]
        raise MediaError(f"Não foi possível extrair o áudio: {detail}") from exc
