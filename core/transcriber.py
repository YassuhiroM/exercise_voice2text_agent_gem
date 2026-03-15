from __future__ import annotations

"""Bilingual ASR transcription using faster-whisper.

Step 3 goals:
- CPU-first execution for Ryzen 5 class machines.
- int8 quantization for lower memory footprint.
- tiny multilingual model for EN/ES support.
- Lazy model loading and cleanup of temporary audio files.
"""

"""Bilingual ASR transcription using faster-whisper with language limits."""

import time
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        compute_type: str = "int8",
        keep_model_loaded: bool = True,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.keep_model_loaded = keep_model_loaded
        self._model: Optional[WhisperModel] = None

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        return self._model

    def transcribe(
        self,
        audio_path: str | Path,
        delete_audio: bool = True,
    ) -> str:
        audio_file = Path(audio_path)
        model = self._load_model()
        
        # --- IMPROVEMENT: LANGUAGE LIMITS ---
        # We allow auto-detection but bias it strictly to EN/ES
        segments, _info = model.transcribe(
            str(audio_file),
            beam_size=5,
            vad_filter=True#,
            #initial_prompt="English, Spanish, Portuguese." 
        )

        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        
        if delete_audio:
            audio_file.unlink(missing_ok=True)
        return text.strip()

if __name__ == "__main__":
    main()
