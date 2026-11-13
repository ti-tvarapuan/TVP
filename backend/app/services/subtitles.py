from pathlib import Path


def format_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}.{millis:03d}"


def to_vtt(segments: list[dict]) -> str:
    lines = ["WEBVTT", ""]
    for segment in segments:
        lines.extend([
            f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}",
            segment["text"],
            "",
        ])
    return "\n".join(lines)


def save_vtt(content: str, path: Path) -> None:
    path.write_text(content, encoding="utf-8")
