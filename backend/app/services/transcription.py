from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_name: str, device: str, compute_type: str):
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe_with_progress(self, audio_path: str):
        segments, _info = self.model.transcribe(
            audio_path, language=None, vad_filter=True, beam_size=5
        )
        duration = float(_info.duration or 0)
        results = []
        for segment in segments:
            if segment.text.strip():
                results.append({"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip()})
            if duration > 0:
                yield min(1.0, float(segment.end) / duration), None
        yield 1.0, results
