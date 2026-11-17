from pathlib import Path
import json
import queue
import shutil
import threading
import uuid
from flask import Blueprint, Response, current_app, jsonify, request, send_file, stream_with_context, url_for
from werkzeug.utils import secure_filename

from app.services.media import MediaError, download_youtube_video, extract_audio, extract_audio_track, extract_subtitle
from app.services.subtitles import save_vtt, to_vtt
from app.services.transcription import Transcriber
from app.services.translation import OllamaTranslator, TranslationError
from app.services.video import embed_subtitles

main_bp = Blueprint("main", __name__)
VIDEO_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "webm", "mpeg", "mpg"}
AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "aac", "ogg", "flac", "opus", "weba", "aiff", "aif", "wma"}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
_PROCESSING_LOCK = threading.Lock()
_PENDING_JOBS = queue.Queue(maxsize=3)


def _services():
    config = current_app.config
    # Carregamento tardio: iniciar o servidor não baixa/carrega o modelo Whisper.
    if "transcriber" not in current_app.extensions:
        current_app.extensions["transcriber"] = Transcriber(
            config["WHISPER_MODEL"], config["WHISPER_DEVICE"], config["WHISPER_COMPUTE_TYPE"]
        )
    if "translator" not in current_app.extensions:
        current_app.extensions["translator"] = OllamaTranslator(
            config["OLLAMA_URL"], config["OLLAMA_MODEL"]
        )
    return current_app.extensions["transcriber"], current_app.extensions["translator"]


@main_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@main_bp.post("/api/subtitles")
def create_subtitles():
    # Parse and spool the incoming body before starting the SSE response. Reading
    # multipart data after the first yield can hit a disconnected WSGI input.
    video_url = request.form.get("url", "").strip()
    uploaded = request.files.get("video")
    target_language = request.form.get("target_language", "Portuguese").strip()
    try:
        _PENDING_JOBS.put_nowait(object())
    except queue.Full:
        return jsonify({"error": "A fila de processamento está cheia. Tente novamente em instantes."}), 429

    incoming_path = None
    if uploaded and uploaded.filename:
        video_root = Path(current_app.config["VIDEO_FOLDER"])
        video_root.mkdir(parents=True, exist_ok=True)
        incoming_path = video_root / f".upload-{uuid.uuid4().hex}.tmp"
        uploaded.save(incoming_path)

    def events():
        vtt_path = None
        succeeded = False
        acquired = False
        try:
            yield _sse("progress", {"stage": "queued", "progress": 0, "message": "Aguardando na fila de processamento…"})
            _PROCESSING_LOCK.acquire()
            acquired = True
            _PENDING_JOBS.get_nowait()
            if bool(video_url) == bool(uploaded and uploaded.filename):
                yield _sse("error", {"error": "Envie um arquivo no campo 'video' ou uma URL no campo 'url'."})
                return

            from urllib.parse import urlparse
            video_root = Path(current_app.config["VIDEO_FOLDER"])
            video_root.mkdir(parents=True, exist_ok=True)
            original_name = (secure_filename(uploaded.filename) if uploaded and uploaded.filename else "") or "video.mp4"
            if video_url:
                parsed_url = urlparse(video_url)
                if _is_youtube_url(video_url):
                    video_id = parsed_url.query and __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(parsed_url.query).get("v", [None])[0]
                    if not video_id and parsed_url.hostname == "youtu.be":
                        video_id = parsed_url.path.strip("/").split("/")[0]
                    if not video_id or not __import__("re").fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                        yield _sse("error", {"error": "URL do YouTube inválida ou sem ID de vídeo."})
                        return
                    original_name = f"youtube_{video_id}.mp4"
                else:
                    original_name = secure_filename(Path(parsed_url.path).name) or "video.mp4"
            extension = Path(original_name).suffix.lower().lstrip(".")
            if video_url and extension not in VIDEO_EXTENSIONS:
                original_name, extension = "video.mp4", "mp4"
            if extension not in ALLOWED_EXTENSIONS:
                yield _sse("error", {"error": "Formato de video nao suportado."})
                return

            job_dir = video_root / original_name
            job_dir.mkdir(parents=True, exist_ok=True)
            video_path = job_dir / original_name
            audio_path = job_dir / f"{Path(original_name).stem}.wav"
            vtt_path = job_dir / f"{Path(original_name).stem}.vtt"
            embedded_subtitle_path = job_dir / f"{Path(original_name).stem}.original.vtt"

            if video_url:
                yield _sse("progress", {"stage": "downloading", "progress": 2, "message": "Baixando vídeo…"})
                if _is_youtube_url(video_url):
                    download_youtube_video(video_url, video_path, current_app.config["MAX_CONTENT_LENGTH"])
                else:
                    _download_video(video_url, video_path)
            else:
                incoming_path.replace(video_path)

            if video_url:
                url_extension = Path(urlparse(video_url).path).suffix.lower().lstrip(".")
                if url_extension in ALLOWED_EXTENSIONS:
                    extension = url_extension
                    target_path = job_dir / f"{Path(original_name).stem}.{extension}"
                    video_path.replace(target_path)
                    video_path = target_path

            yield _sse("progress", {"stage": "extracting_audio", "progress": 15, "message": "Separando o áudio do vídeo…"})
            embedded_subtitle_found = (
                extract_subtitle(video_path, embedded_subtitle_path, current_app.config["FFMPEG_BINARY"])
                if extension in VIDEO_EXTENSIONS else False
            )
            extract_audio(video_path, audio_path, current_app.config["FFMPEG_BINARY"])
            yield _sse("progress", {"stage": "transcribing", "progress": 30, "message": "Transcrevendo o áudio…"})
            transcriber, translator = _services()
            segments = []
            for progress, result in transcriber.transcribe_with_progress(str(audio_path)):
                if result is None:
                    yield _sse("progress", {"stage": "transcribing", "progress": round(30 + progress * 35), "message": "Transcrevendo o áudio…"})
                else:
                    segments = result
            if not segments:
                yield _sse("error", {"error": "Nenhuma fala foi identificada no vídeo."})
                return
            yield _sse("progress", {"stage": "translating", "progress": 65, "message": f"Traduzindo para {target_language}…"})
            translated = []
            for index, segment in enumerate(segments, start=1):
                translated.append({
                    **segment,
                    "text": translator.translate(
                        segment["text"], target_language, content_type="subtitle"
                    ),
                })
                progress = index / len(segments)
                yield _sse("progress", {"stage": "translating", "progress": round(65 + progress * 30), "message": f"Traduzindo para {target_language}…"})
            save_vtt(to_vtt(translated), vtt_path)
            succeeded = True
            result = {
                "video_path": str(video_path.resolve()), "subtitle_path": str(vtt_path.resolve()),
                "audio_path": str(audio_path.resolve()),
                "video_url": url_for("main.get_video", job=job_dir.name, filename=video_path.name, _external=True),
                "subtitle_url": url_for("main.get_subtitle", job=job_dir.name, filename=vtt_path.name, _external=True),
            }
            if embedded_subtitle_found:
                result["original_subtitle_path"] = str(embedded_subtitle_path.resolve())
                result["original_subtitle_url"] = url_for("main.get_subtitle", job=job_dir.name, filename=embedded_subtitle_path.name, _external=True)
            yield _sse("complete", {"progress": 100, "job": result})
        except (MediaError, TranslationError) as exc:
            yield _sse("error", {"error": str(exc)})
        except Exception:
            current_app.logger.exception("Erro inesperado durante o processamento do vídeo")
            yield _sse("error", {"error": "Erro interno ao processar o vídeo."})
        finally:
            if incoming_path:
                incoming_path.unlink(missing_ok=True)
            if not succeeded and vtt_path:
                vtt_path.unlink(missing_ok=True)
            if acquired:
                _PROCESSING_LOCK.release()
            else:
                try:
                    _PENDING_JOBS.get_nowait()
                except queue.Empty:
                    pass

    response = Response(stream_with_context(events()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    return response


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _is_youtube_url(value: str) -> bool:
    from urllib.parse import urlparse
    host = (urlparse(value).hostname or "").lower().removeprefix("www.")
    return host in {"youtube.com", "m.youtube.com", "youtu.be", "youtube-nocookie.com"}


@main_bp.post("/api/youtube/download")
def download_youtube_only():
    data = request.get_json(silent=True) or {}
    video_url = data.get("url", "")
    if not isinstance(video_url, str) or not _is_youtube_url(video_url):
        return jsonify({"error": "Informe uma URL válida do YouTube."}), 400
    job_dir = Path(current_app.config["VIDEO_FOLDER"]) / "youtube-downloads"
    job_dir.mkdir(parents=True, exist_ok=True)
    output_path = job_dir / "youtube_video.mp4"
    try:
        download_youtube_video(video_url, output_path, current_app.config["MAX_CONTENT_LENGTH"])
        return send_file(output_path, mimetype="video/mp4", as_attachment=True, download_name="video.mp4")
    except MediaError as exc:
        return jsonify({"error": str(exc)}), 502


@main_bp.post("/api/audio/extract")
def extract_audio_only():
    """Receive a local video or YouTube URL and return its audio as MP3."""
    uploaded = request.files.get("video")
    if request.is_json:
        data = request.get_json(silent=True) or {}
        video_url = data.get("url", "") if isinstance(data, dict) else ""
    else:
        video_url = request.form.get("url", "")
    if not isinstance(video_url, str):
        return jsonify({"error": "Informe uma URL do YouTube válida."}), 400
    video_url = video_url.strip()
    has_upload = bool(uploaded and uploaded.filename)
    if bool(video_url) == has_upload:
        return jsonify({"error": "Envie um arquivo no campo 'video' ou uma URL no campo 'url'."}), 400

    if video_url:
        from urllib.parse import urlparse

        parsed_url = urlparse(video_url)
        if parsed_url.scheme not in {"http", "https"} or not _is_youtube_url(video_url):
            return jsonify({"error": "Informe uma URL http(s) válida do YouTube."}), 400
        source_name = "video.mp4"
        download_name = "audio.mp3"
    else:
        source_name = secure_filename(uploaded.filename)
        extension = Path(source_name).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({"error": "Formato de vídeo não suportado."}), 400
        download_name = f"{Path(source_name).stem or 'audio'}.mp3"

    video_root = Path(current_app.config["VIDEO_FOLDER"])
    work_dir = video_root / "audio-extractions" / uuid.uuid4().hex
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = work_dir / source_name
    audio_path = work_dir / download_name
    try:
        if video_url:
            download_youtube_video(video_url, video_path, current_app.config["MAX_CONTENT_LENGTH"])
        else:
            uploaded.save(video_path)
        extract_audio_track(video_path, audio_path, current_app.config["FFMPEG_BINARY"])
        response = send_file(
            audio_path, mimetype="audio/mpeg", as_attachment=True, download_name=download_name,
        )
        response.call_on_close(lambda: shutil.rmtree(work_dir, ignore_errors=True))
        return response
    except MediaError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        return jsonify({"error": str(exc)}), 502
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        current_app.logger.exception("Erro ao extrair áudio do vídeo")
        return jsonify({"error": "Erro interno ao extrair o áudio."}), 500


@main_bp.get("/api/videos/<job>/<filename>")
def get_video(job: str, filename: str):
    if Path(job).name != job or Path(filename).name != filename:
        return jsonify({"error": "Caminho inválido."}), 400
    path = Path(current_app.config["VIDEO_FOLDER"]) / job / filename
    if not path.is_file() or path.suffix.lower().lstrip(".") not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Vídeo não encontrado."}), 404
    response = send_file(path, conditional=True)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@main_bp.get("/api/subtitles/<job>/<filename>")
def get_subtitle(job: str, filename: str):
    if Path(job).name != job or Path(filename).name != filename or not filename.endswith(".vtt"):
        return jsonify({"error": "Caminho inválido."}), 400
    path = Path(current_app.config["VIDEO_FOLDER"]) / job / filename
    if not path.is_file():
        return jsonify({"error": "Legenda não encontrada."}), 404
    response = send_file(path, mimetype="text/vtt; charset=utf-8", conditional=True)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@main_bp.post("/api/videos/with-subtitles")
def download_video_with_subtitles():
    data = request.get_json(silent=True) or {}
    video_value = data.get("video_path")
    subtitle_value = data.get("subtitle_path")
    if not isinstance(video_value, str) or not isinstance(subtitle_value, str):
        return jsonify({"error": "Envie 'video_path' e 'subtitle_path' no JSON."}), 400

    video_root = Path(current_app.config["VIDEO_FOLDER"]).resolve()
    try:
        video_path = Path(video_value).resolve(strict=True)
        subtitle_path = Path(subtitle_value).resolve(strict=True)
        video_path.relative_to(video_root)
        subtitle_path.relative_to(video_path.parent)
    except (OSError, ValueError):
        return jsonify({"error": "Os caminhos precisam apontar para arquivos existentes desta aplicação."}), 400

    if video_path.suffix.lower().lstrip(".") not in VIDEO_EXTENSIONS or subtitle_path.suffix.lower() != ".vtt":
        return jsonify({"error": "O vídeo ou arquivo de legenda tem formato inválido."}), 400

    output_path = video_path.parent / f"{video_path.stem}_pt.mp4"
    try:
        embed_subtitles(video_path, subtitle_path, output_path, current_app.config["FFMPEG_BINARY"])
        response = send_file(
            output_path, mimetype="video/mp4", as_attachment=True,
            download_name=f"{video_path.stem}_pt.mp4",
        )
        return response
    except MediaError as exc:
        output_path.unlink(missing_ok=True)
        return jsonify({"error": str(exc)}), 502
    except Exception:
        output_path.unlink(missing_ok=True)
        current_app.logger.exception("Erro ao preparar vídeo com legenda")
        return jsonify({"error": "Erro interno ao incorporar a legenda."}), 500


def _download_video(url: str, destination: Path) -> None:
    # URLs são opcionais; limite de bytes e timeout evitam downloads sem limite.
    import requests
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MediaError("URL inválida: use http ou https.")
    try:
        with requests.get(url, stream=True, timeout=(10, 60)) as response:
            response.raise_for_status()
            content_length = int(response.headers.get("Content-Length", "0"))
            max_bytes = current_app.config["MAX_CONTENT_LENGTH"]
            if content_length and content_length > max_bytes:
                raise MediaError("O vídeo excede o tamanho máximo permitido.")
            total = 0
            with destination.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise MediaError("O vídeo excede o tamanho máximo permitido.")
                    output.write(chunk)
    except requests.RequestException as exc:
        raise MediaError(f"Falha ao baixar o vídeo: {exc}") from exc
