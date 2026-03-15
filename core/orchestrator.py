"""VoiceFlow end-to-end orchestrator.

Goals:
- Link recording -> transcription -> styling -> clipboard paste.
- Keep memory usage low on 8GB systems via sequential processing + gc.collect().
- Print clear status updates for each pipeline stage.
- Avoid double-processing (manual stop + watcher thread).
- Support push-to-talk + optional recorder auto-stop behavior safely.
"""

from __future__ import annotations

import gc
import threading
import time
from pathlib import Path

from core.audio_handler import Recorder
from core.clipboard_paster import Paster
from core.style_rewriter import StyleRewriter
from core.transcriber import Transcriber


class VoiceFlowOrchestrator:
    """Coordinates the full voice-to-text pipeline from hotkey events."""

    def __init__(self) -> None:
        self.recorder = Recorder()
        self.transcriber = Transcriber(keep_model_loaded=False)
        self.rewriter = StyleRewriter(model_name="llama3.2:1b", timeout_seconds=10.0)
        self.paster = Paster(paste_delay_seconds=0.1)

        # ---- state / concurrency guards ----
        self.is_processing: bool = False
        self._lock = threading.Lock()

        self._current_audio_path: Path | None = None
        self._last_processed_path: Path | None = None

        # After an auto-stop completes, key-release may still call toggle().
        # Ignore "start" toggles for a short window to avoid accidental new recordings.
        self._ignore_start_until: float = 0.0  # monotonic seconds

    # ---------------------------------------------------------------------
    # Public API (keeps compatibility with your existing main.py)
    # ---------------------------------------------------------------------
    def toggle(self) -> None:
        """Toggle recording state. Used by hotkey press/release."""
        # If we're in the small ignore window (typically caused by auto-stop),
        # do not start a new recording accidentally.
        if not self.recorder.is_recording and time.monotonic() < self._ignore_start_until:
            # Quietly ignore (or print a small info line)
            # print("[INFO] Ignoring start (auto-stop cooldown).")
            return

        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_and_process()

    def start_recording(self) -> None:
        """Starts recording and spawns a watcher thread that processes if recorder stops itself."""
        with self._lock:
            if self.recorder.is_recording:
                return
            if self.is_processing:
                print("[INFO] Busy processing previous audio. Please wait.")
                return

            audio_path = self.recorder.start()
            self._current_audio_path = audio_path
            print(f"[RECORDING] Listening... saving to {audio_path}")

            # Watcher handles recorder auto-stop (if recorder has a max duration / internal stop)
            threading.Thread(
                target=self._wait_for_auto_stop,
                args=(audio_path,),
                daemon=True,
            ).start()

    def stop_and_process(self) -> None:
        """Stops recording (manual stop) and processes the resulting audio once."""
        audio_path = self.recorder.stop()
        if not audio_path:
            print("[ERROR] Recorder returned no audio path.")
            return

        print("[RECORDING] Stopped.")
        self._process_recording_once(audio_path, source="manual-stop")

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _wait_for_auto_stop(self, audio_path: Path) -> None:
        """Watches recorder and processes if it stops without a manual stop call."""
        while self.recorder.is_recording:
            time.sleep(0.1)

        # recorder stopped (either by timeout/internal stop OR manual stop)
        self._process_recording_once(audio_path, source="auto-stop")

        # Prevent the immediate key-release (which calls toggle()) from starting a new recording
        # right after auto-stop processing completes.
        # This is a small UX guard; manual stop path already works fine.
        self._ignore_start_until = time.monotonic() + 0.75

    def _process_recording_once(self, audio_path: Path | None, source: str) -> None:
        """Ensures a given audio path is processed at most once."""
        if audio_path is None:
            return

        with self._lock:
            # Skip duplicates: manual stop + watcher thread can race
            if self._last_processed_path == audio_path:
                return
            if self.is_processing:
                # Already processing something (rare). Skip duplicate processing.
                return

            self.is_processing = True
            self._last_processed_path = audio_path

        try:
            self._process_recording(audio_path)
        finally:
            with self._lock:
                self.is_processing = False
                self._current_audio_path = None

    def _process_recording(self, audio_path: Path) -> None:
        """Runs the full pipeline: transcribe -> style -> paste -> cleanup."""
        if not audio_path.exists():
            print("[ERROR] Empty audio path or file missing. Please record again.")
            return

        raw_text = ""
        try:
            print("[TRANSCRIBING] Processing recorded audio...")
            raw_text = self.transcriber.transcribe(audio_path=audio_path, delete_audio=False)

            if not raw_text.strip():
                print("[ERROR] Empty audio detected (stopped too quickly or silence only).")
                return

            gc.collect()

            print("[STYLING] Refining text with Ollama...")
            try:
                final_text = self.rewriter.rewrite(raw_text)
            except (ConnectionError, TimeoutError) as exc:
                print(f"[STYLING] Fallback to raw transcript: {exc}")
                final_text = raw_text

            print("[PASTING] Copying to clipboard and sending Ctrl+V...")
            self.paster.paste_text(final_text)
            print("[PASTING] Done.")
        except FileNotFoundError as exc:
            print(f"[ERROR] Recorder output file not found: {exc}")
        except RuntimeError as exc:
            print(f"[ERROR] Transcriber initialization/runtime failure: {exc}")
        except ValueError as exc:
            print(f"[ERROR] Nothing to paste: {exc}")
        except PermissionError as exc:
            print(f"[ERROR] Paste injection failed: {exc}")
        finally:
            # Always clean up the temp audio file
            try:
                audio_path.unlink(missing_ok=True)
            except Exception as exc:
                print(f"[WARN] Could not delete temp audio file: {exc}")
