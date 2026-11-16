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


def extract_audio_track(video_path: Path, audio_path: Path, ffmpeg_binary: str) -> None:
    """Extract the first audio stream as a broadly compatible MP3 file."""
    command = [
        ffmpeg_binary, "-y", "-i", str(video_path), "-map", "0:a:0", "-vn",
        "-codec:a", "libmp3lame", "-b:a", "192k", str(audio_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg não foi encontrado. Verifique FFMPEG_BINARY e o PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-1000:]
        raise MediaError(f"Não foi possível extrair a faixa de áudio: {detail}") from exc


def extract_subtitle(video_path: Path, subtitle_path: Path, ffmpeg_binary: str) -> bool:
    """Extract the first embedded text subtitle as WebVTT, if available."""
    command = [ffmpeg_binary, "-y", "-i", str(video_path), "-map", "0:s:0", "-c:s", "webvtt", str(subtitle_path)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return subtitle_path.is_file() and subtitle_path.stat().st_size > 0
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg was not found. Check FFMPEG_BINARY and PATH.") from exc
    except subprocess.CalledProcessError:
        subtitle_path.unlink(missing_ok=True)
        return False


def download_youtube_video(url: str, destination: Path, max_bytes: int) -> None:
    try:
        from yt_dlp import YoutubeDL
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.unlink(missing_ok=True)
        destination.with_suffix(".mp4").unlink(missing_ok=True)
        options = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(destination.with_suffix("")) + ".%(ext)s",
            "max_filesize": max_bytes,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with YoutubeDL(options) as downloader:
            downloader.download([url])
        downloaded = destination.with_suffix(".mp4")
        if not downloaded.exists():
            raise MediaError("O yt-dlp não gerou um arquivo MP4.")
        if downloaded != destination:
            downloaded.replace(destination)
    except MediaError:
        raise
    except Exception as exc:
        raise MediaError(f"Falha ao baixar o vídeo do YouTube: {exc}") from exc
