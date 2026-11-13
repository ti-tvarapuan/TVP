from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, send_file, url_for
from werkzeug.utils import secure_filename

from app.services.media import MediaError, extract_audio
from app.services.subtitles import save_vtt, to_vtt
from app.services.transcription import Transcriber
from app.services.translation import OllamaTranslator, TranslationError
from app.services.video import embed_subtitles

main_bp = Blueprint("main", __name__)
ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "webm", "mpeg", "mpg"}


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
    video_url = request.form.get("url", "").strip()
    uploaded = request.files.get("video")
    if bool(video_url) == bool(uploaded and uploaded.filename):
        return jsonify({"error": "Envie um arquivo no campo 'video' ou uma URL no campo 'url'."}), 400

    from urllib.parse import urlparse
    video_root = Path(current_app.config["VIDEO_FOLDER"])
    video_root.mkdir(parents=True, exist_ok=True)
    original_name = (secure_filename(uploaded.filename) if uploaded and uploaded.filename else "") or "video.mp4"
    if video_url:
        original_name = secure_filename(Path(urlparse(video_url).path).name) or "video.mp4"
    extension = Path(original_name).suffix.lower().lstrip(".")
    if video_url and extension not in ALLOWED_EXTENSIONS:
        original_name = "video.mp4"
        extension = "mp4"
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Formato de video nao suportado."}), 400
    job_dir = video_root / original_name
    job_dir.mkdir(parents=True, exist_ok=True)
    video_path = job_dir / original_name
    audio_path = job_dir / f"{Path(original_name).stem}.wav"
    vtt_path = job_dir / f"{Path(original_name).stem}.vtt"
    succeeded = False

    try:
        if video_url:
            _download_video(video_url, video_path)
        else:
            if extension not in ALLOWED_EXTENSIONS:
                return jsonify({"error": "Formato de vídeo não suportado."}), 400
            uploaded.save(video_path)
        if video_url:
            url_extension = Path(urlparse(video_url).path).suffix.lower().lstrip(".")
            if url_extension in ALLOWED_EXTENSIONS:
                extension = url_extension
                target_path = job_dir / f"{Path(original_name).stem}.{extension}"
                video_path.replace(target_path)
                video_path = target_path

        extract_audio(video_path, audio_path, current_app.config["FFMPEG_BINARY"])
        transcriber, translator = _services()
        segments = transcriber.transcribe(str(audio_path))
        if not segments:
            return jsonify({"error": "Nenhuma fala foi identificada no vídeo."}), 422
        translated = translator.translate_segments(segments)
        save_vtt(to_vtt(translated), vtt_path)
        succeeded = True
        return jsonify({
            "video_path": str(video_path.resolve()),
            "subtitle_path": str(vtt_path.resolve()),
            "audio_path": str(audio_path.resolve()),
            "video_url": url_for("main.get_video", job=job_dir.name, filename=video_path.name, _external=True),
            "subtitle_url": url_for("main.get_subtitle", job=job_dir.name, filename=vtt_path.name, _external=True),
        }), 201
    except (MediaError, TranslationError) as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception:
        current_app.logger.exception("Erro inesperado durante o processamento do vídeo")
        return jsonify({"error": "Erro interno ao processar o vídeo."}), 500
    finally:
        if not succeeded:
            vtt_path.unlink(missing_ok=True)


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

    if video_path.suffix.lower().lstrip(".") not in ALLOWED_EXTENSIONS or subtitle_path.suffix.lower() != ".vtt":
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
