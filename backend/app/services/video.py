import subprocess
from pathlib import Path

from app.services.media import MediaError


def embed_subtitles(video_path: Path, subtitle_path: Path, output_path: Path, ffmpeg_binary: str) -> None:
    subtitle_filter_path = str(subtitle_path.resolve()).replace("\\", "/")
    for character in ("\\", ":", "'", ",", "[", "]"):
        subtitle_filter_path = subtitle_filter_path.replace(character, "\\" + character)
    base_command = [
        ffmpeg_binary, "-y", "-i", str(video_path),
        "-vf", (
            f"subtitles='{subtitle_filter_path}':"
            "force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,"
            "BackColour=&H00000000,BorderStyle=3,Outline=2,Shadow=0,MarginV=22'"
        ),
        "-map", "0:v:0", "-map", "0:a?",
    ]
    output_options = ["-c:a", "aac", "-movflags", "+faststart", str(output_path)]
    try:
        # Prefer NVIDIA's hardware encoder; burn-in still applies the subtitle
        # filter, while NVENC avoids the slower CPU video encode.
        gpu_command = base_command + ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-b:v", "0"] + output_options
        result = subprocess.run(gpu_command, capture_output=True, text=True)
        if result.returncode != 0:
            output_path.unlink(missing_ok=True)
            cpu_command = base_command + ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"] + output_options
            subprocess.run(cpu_command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MediaError("FFmpeg não foi encontrado. Verifique FFMPEG_BINARY e o PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-1500:]
        raise MediaError(f"Não foi possível incorporar a legenda: {detail}") from exc
