"""Bilingual ASR transcription using faster-whisper.

Step 3 goals:
- CPU-first execution for Ryzen 5 class machines.
- int8 quantization for lower memory footprint.
- tiny multilingual model for EN/ES support.
- Lazy model loading and cleanup of temporary audio files.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

LOGGER = logging.getLogger(__name__)


class Transcriber:
    """Lazy-loading wrapper around faster-whisper for EN/ES transcription."""

    def __init__(
        self,
        model_size: str = "tiny",
        device: Optional[str] = None,
        compute_type: str = "int8",
        keep_model_loaded: bool = True,
    ) -> None:
        self.model_size = model_size
        self.device = device or self._detect_device()
        self.compute_type = compute_type
        self.keep_model_loaded = keep_model_loaded
        self._model: Optional[WhisperModel] = None

    def _detect_device(self) -> str:
        """Prefer CUDA if NVIDIA GPU is detected, else CPU."""
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return "cpu"

        try:
            result = subprocess.run(
                [nvidia_smi, "-L"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
            if result.returncode == 0 and "GPU" in result.stdout:
                return "cuda"
        except Exception:
            return "cpu"

        return "cpu"

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except RuntimeError as exc:
                raise RuntimeError(
                    "Failed to initialize faster-whisper model. "
                    "Try using CPU/int8 and close heavy applications."
                ) from exc
        return self._model

    def unload(self) -> None:
        """Release model reference so Python can reclaim memory."""
        self._model = None

    def transcribe(
        self,
        audio_path: str | Path,
        language: Optional[str] = None,
        beam_size: int = 1,
        delete_audio: bool = True,
    ) -> str:
        """Transcribe audio and optionally remove source file afterwards.

        Args:
            audio_path: Path to WAV/compatible audio file.
            language: Force a language code (`en`, `es`) or None for auto-detect.
            beam_size: Low beam size for faster CPU execution.
            delete_audio: Delete the source file after transcription completes.

        Returns:
            Transcribed text as a single string.
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        model = self._load_model()
        try:
            if language in {"en", "es"}:
                segments, _info = model.transcribe(
                    str(audio_file),
                    language=language,
                    beam_size=beam_size,
                    vad_filter=True,
                )
            else:
                segments, _info = model.transcribe(
                    str(audio_file),
                    language=None,
                    beam_size=beam_size,
                    vad_filter=True,
                )

            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
            return text.strip()
        finally:
            if delete_audio:
                audio_file.unlink(missing_ok=True)
            if not self.keep_model_loaded:
                self.unload()


def audio_duration_seconds(audio_path: str | Path) -> float:
    with wave.open(str(audio_path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def main() -> None:
    parser = argparse.ArgumentParser(description="Test faster-whisper transcription")
    parser.add_argument("audio_path", help="Path to a WAV file")
    parser.add_argument("--language", choices=["en", "es"], default=None)
    parser.add_argument("--keep-audio", action="store_true", help="Do not delete input file")
    args = parser.parse_args()

    transcriber = Transcriber(keep_model_loaded=False)

    try:
        duration = audio_duration_seconds(args.audio_path)
        t0 = time.perf_counter()
        text = transcriber.transcribe(
            args.audio_path,
            language=args.language,
            delete_audio=not args.keep_audio,
        )
        elapsed = time.perf_counter() - t0
        rtf = elapsed / duration if duration > 0 else float("inf")

        print(f"[transcriber] Device: {transcriber.device}, compute_type: {transcriber.compute_type}")
        print(f"[transcriber] Duration: {duration:.2f}s")
        print(f"[transcriber] Processing time: {elapsed:.2f}s")
        print(f"[transcriber] RTF: {rtf:.2f}")
        print(f"[transcriber] Text: {text}")
    except FileNotFoundError as exc:
        print(f"[transcriber] File error: {exc}")
        print("[transcriber] Repair tip: ensure recorder saved a valid WAV before ASR.")
    except RuntimeError as exc:
        print(f"[transcriber] Runtime error: {exc}")
        print("[transcriber] Repair tip: reduce system load or keep CPU/int8 settings.")


if __name__ == "__main__":
    main()
