"""Audio capture handler for VoiceFlow Clone.

Step 2 focus:
- Record microphone input to a temporary WAV file on disk (not RAM buffers).
- Support thread-safe start/stop toggling from the main application.
"""

from __future__ import annotations

import threading
import time
import tempfile
import wave
from pathlib import Path
from typing import Optional

import pyaudio


class RecorderError(Exception):
    """Base recorder exception."""


class DeviceNotFoundError(RecorderError):
    """Raised when no valid microphone input device can be opened."""


class Recorder:
    """Thread-safe microphone recorder writing directly to a temp WAV file.

    Notes:
        - Uses 16kHz mono PCM16 by default (Whisper-friendly and compact).
        - Writes frames directly to disk from the stream callback to avoid
          keeping a large byte array in memory.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        frames_per_buffer: int = 1024,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.sample_format = pyaudio.paInt16
        self._sample_width = 2

        self._lock = threading.RLock()
        self._is_recording = False

        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._wave_file: Optional[wave.Wave_write] = None
        self._output_path: Optional[Path] = None

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    @property
    def output_path(self) -> Optional[Path]:
        with self._lock:
            return self._output_path

    def start(self) -> Path:
        """Start recording into a temp WAV file and return its path."""
        with self._lock:
            if self._is_recording:
                if self._output_path is None:
                    raise RecorderError("Recorder is active but output path is missing.")
                return self._output_path

            self._audio = pyaudio.PyAudio()
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_wav_path = Path(tmp_wav.name)
            tmp_wav.close()

            wave_handle = wave.open(str(tmp_wav_path), "wb")
            wave_handle.setnchannels(self.channels)
            wave_handle.setsampwidth(self._sample_width)
            wave_handle.setframerate(self.sample_rate)

            try:
                stream = self._audio.open(
                    format=self.sample_format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.frames_per_buffer,
                    stream_callback=self._on_audio_chunk,
                )
            except OSError as exc:
                wave_handle.close()
                tmp_wav_path.unlink(missing_ok=True)
                self._audio.terminate()
                self._audio = None
                raise DeviceNotFoundError(
                    "Unable to open microphone input device. "
                    "Check if the mic is connected and not used by another app."
                ) from exc
            except Exception:
                wave_handle.close()
                tmp_wav_path.unlink(missing_ok=True)
                self._audio.terminate()
                self._audio = None
                raise

            self._wave_file = wave_handle
            self._stream = stream
            self._output_path = tmp_wav_path
            self._is_recording = True
            self._stream.start_stream()

            return tmp_wav_path

    def stop(self) -> Optional[Path]:
        """Stop recording and return the output file path."""
        with self._lock:
            if not self._is_recording:
                return self._output_path

            stream = self._stream
            wave_handle = self._wave_file
            audio = self._audio

            self._is_recording = False
            self._stream = None
            self._wave_file = None
            output_path = self._output_path
            self._audio = None

        if stream is not None:
            if stream.is_active():
                stream.stop_stream()
            stream.close()

        if wave_handle is not None:
            wave_handle.close()

        if audio is not None:
            audio.terminate()

        return output_path

    def toggle(self) -> Optional[Path]:
        """Toggle recording state.

        Returns:
            - On start: output file path where recording is being written.
            - On stop: final output file path.
        """
        return self.stop() if self.is_recording else self.start()

    def cleanup_file(self) -> None:
        """Delete the last output file if it exists."""
        with self._lock:
            path = self._output_path
            self._output_path = None

        if path is not None:
            path.unlink(missing_ok=True)

    def _on_audio_chunk(self, in_data, frame_count, time_info, status):
        with self._lock:
            if self._wave_file is not None and self._is_recording:
                self._wave_file.writeframes(in_data)
        return (None, pyaudio.paContinue)


if __name__ == "__main__":
    # Standalone smoke-test: record 3 seconds and confirm file size.
    recorder = Recorder()
    print("[audio_handler] Starting 3-second recording test...")
    try:
        output = recorder.start()
        time.sleep(3)
        recorder.stop()
        if output.exists():
            size_bytes = output.stat().st_size
            print(f"[audio_handler] Saved: {output}")
            print(f"[audio_handler] File size: {size_bytes} bytes")
        else:
            print("[audio_handler] Recording stopped, but output file is missing.")
    except DeviceNotFoundError as exc:
        print(f"[audio_handler] Device error: {exc}")
        print("[audio_handler] Repair tip: reconnect/select microphone and retry.")
    except Exception as exc:
        print(f"[audio_handler] Unexpected error: {exc}")
    finally:
        recorder.stop()
