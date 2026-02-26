"""VoiceFlow end-to-end orchestrator.

Step 6 goals:
- Link recording -> transcription -> styling -> clipboard paste.
- Keep memory usage low on 8GB systems via sequential processing + gc.collect().
- Print clear status updates for each pipeline stage.
"""

from __future__ import annotations

import gc
from pathlib import Path

from core.audio_handler import Recorder
from core.clipboard_paster import Paster
from core.style_rewriter import StyleRewriter
from core.transcriber import Transcriber
import time

class VoiceFlowOrchestrator:
    """Coordinates the full voice-to-text pipeline from a single toggle event."""

    def __init__(self) -> None:
        self.recorder = Recorder()
        self.transcriber = Transcriber(keep_model_loaded=False)
        self.rewriter = StyleRewriter(model_name="llama3.2:1b", timeout_seconds=10.0)
        self.paster = Paster(paste_delay_seconds=0.1)

    def toggle(self):
        if not self.recorder.is_recording:
            # Start recording
            audio_path = self.recorder.start()
            
            # Start a background "watcher" thread or use a loop
            threading.Thread(target=self._wait_for_auto_stop, args=(audio_path,), daemon=True).start()
        else:
            # Manual stop
            audio_path = self.recorder.stop()
            if audio_path:
                self._process_recording(audio_path)
    
    def _wait_for_auto_stop(self, audio_path):
        """Watches the recorder and processes if a timeout happens."""
        while self.recorder.is_recording:
            time.sleep(0.1)  # Check every 100ms
        
        # If we get here, the recorder stopped (either manually or via timeout)
        # We check if we are already processing to avoid double-processing
        if not self.is_processing:
            self._process_recording(audio_path)
        
    def _start_recording(self) -> None:
        audio_path = self.recorder.start()
        print(f"[RECORDING] Listening... saving to {audio_path}")

    def _process_recording(self, audio_path: Path | None) -> None:
        if audio_path is None or not audio_path.exists():
            print("[ERROR] Empty audio path. Please record again.")
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
            Path(audio_path).unlink(missing_ok=True)
