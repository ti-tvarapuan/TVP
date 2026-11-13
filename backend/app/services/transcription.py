from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_name: str, device: str, compute_type: str):
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> list[dict]:
        segments, _info = self.model.transcribe(
            audio_path, language="en", vad_filter=True, beam_size=5
        )
        return [
            {"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip()}
            for segment in segments
            if segment.text.strip()
        ]
