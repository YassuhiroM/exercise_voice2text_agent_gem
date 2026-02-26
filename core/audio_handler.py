import threading
import time
import tempfile
import wave
import numpy as np
from pathlib import Path
from typing import Optional
import pyaudio

class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, frames_per_buffer: int = 1024) -> None:
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
        
        # --- IMPROVEMENT: SILENCE TIMEOUT ---
        self.last_speech_time = 0
        self.SILENCE_THRESHOLD = 500  # Adjust if it auto-stops too easily

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    def start(self) -> Path:
        with self._lock:
            if self._is_recording: return self._output_path
            self._audio = pyaudio.PyAudio()
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_wav_path = Path(tmp_wav.name)
            tmp_wav.close()
            wave_handle = wave.open(str(tmp_wav_path), "wb")
            wave_handle.setnchannels(self.channels)
            wave_handle.setsampwidth(self._sample_width)
            wave_handle.setframerate(self.sample_rate)
            
            self.last_speech_time = time.time() # Reset timer on start
            
            self._stream = self._audio.open(
                format=self.sample_format, channels=self.channels,
                rate=self.sample_rate, input=True,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=self._on_audio_chunk,
            )
            self._wave_file = wave_handle
            self._output_path = tmp_wav_path
            self._is_recording = True
            self._stream.start_stream()
            return tmp_wav_path

    def stop(self) -> Optional[Path]:
        with self._lock:
            if not self._is_recording: return self._output_path
            self._is_recording = False
            output_path = self._output_path
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if self._wave_file: self._wave_file.close()
            if self._audio: self._audio.terminate()
            return output_path

    def _on_audio_chunk(self, in_data, frame_count, time_info, status):
        with self._lock:
            if not self._is_recording: return (None, pyaudio.paComplete)
            
            # Check for silence
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            if np.abs(audio_data).mean() > self.SILENCE_THRESHOLD:
                self.last_speech_time = time.time()
            
            # Auto-stop if silent for 10s
            if time.time() - self.last_speech_time > 10.0:
                # We can't call self.stop() directly here comfortably, 
                # but we can signal the is_recording to false
                self._is_recording = False
                return (None, pyaudio.paComplete)

            if self._wave_file:
                self._wave_file.writeframes(in_data)
        return (None, pyaudio.paContinue)

    def toggle(self) -> Optional[Path]:
        return self.stop() if self.is_recording else self.start()
