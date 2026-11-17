import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_VIDEO_SIZE_MB", "2048")) * 1024 * 1024
    MAX_DOCUMENT_SIZE_BYTES = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "25")) * 1024 * 1024
    MAX_DOCUMENT_CHARACTERS = int(os.getenv("MAX_DOCUMENT_CHARACTERS", "500000"))
    MAX_DOCUMENT_PAGES = int(os.getenv("MAX_DOCUMENT_PAGES", "500"))
    TRANSLATION_CHUNK_CHARACTERS = int(os.getenv("TRANSLATION_CHUNK_CHARACTERS", "2500"))
    VIDEO_FOLDER = Path(os.getenv("VIDEO_FOLDER", BASE_DIR.parent / "videos"))
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", VIDEO_FOLDER))
    OUTPUT_FOLDER = Path(os.getenv("OUTPUT_FOLDER", VIDEO_FOLDER))
    FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "translategemma:4b")
