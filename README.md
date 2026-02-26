# VoiceFlow Clone (Windows 11) — Voice-to-Text Agent

## Environment Setup

Recommended virtual environment name for this machine:
- `venv_ucm_general_python311`

Example setup (Windows PowerShell):

```powershell
python -m venv venv_ucm_general_python311
.\venv_ucm_general_python311\Scripts\Activate.ps1
pip install -r requirements.txt
```

> The code does not hardcode the venv name; the active interpreter is used at runtime.

---

## Step 1 — Plan

This repository starts with the planning phase for a low-memory voice-to-text desktop agent for Windows 11.

### Objectives
- Record microphone audio with a global hotkey (`CTRL+ALT+SPACE`).
- Transcribe bilingual speech (English/Spanish) using `faster-whisper` (`tiny`).
- Rewrite text with Ollama (`llama3.2:1b`) in a relaxed but grammatically correct style.
- Copy rewritten text to clipboard and auto-paste with `CTRL+V`.
- Show live state in a lightweight CustomTkinter overlay.

---

## Proposed Project Structure

```text
voiceflow_clone/
  app.py                     # App entrypoint; starts GUI + service coordination
  config.py                  # Config values (hotkeys, model names, temp paths)
  gui/
    overlay.py               # CustomTkinter small status window
  core/
    orchestrator.py          # Sequential pipeline coordinator and state machine
    hotkey_listener.py       # Non-blocking pynput listener and key-state tracking
    transcriber.py           # faster-whisper wrapper (load, transcribe, unload)
    style_rewriter.py        # Ollama client wrapper (rewrite prompt + timeout)
    clipboard_paster.py      # Clipboard write + Ctrl+V automation
  audio_handler.py           # PyAudio recorder to temp WAV files (thread-safe)
  tests/
    test_hotkey_listener.py  # Hotkey toggle behavior with mocked key events
    test_pipeline_flow.py    # Sequential state transitions and lock behavior
    test_clipboard.py        # Clipboard + paste invocation mocks
```

---

## Step 2 — Audio Capture Implementation (Development Loop)

### Plan
- Use a `Recorder` class in `audio_handler.py` based on PyAudio.
- Keep memory usage low by writing incoming microphone chunks directly into a temporary `.wav` file on disk.
- Use a fixed 16kHz, mono, 16-bit PCM stream (Whisper-friendly, smaller files).
- Make start/stop thread-safe with a lock so a hotkey toggle cannot race under rapid key presses.

### Edit Code
- Added `audio_handler.py` with:
  - `Recorder.start()` to initialize PyAudio input and temp WAV output.
  - `Recorder.stop()` to close stream/file/driver safely.
  - `Recorder.toggle()` for start/stop behavior from `main.py`.
  - `DeviceNotFoundError` for disconnected/unavailable microphone handling.

### Run Tools
- Standalone test:
  - `python audio_handler.py`

### Observe
- Expected data size for 10 seconds at 16kHz mono PCM16:
  - `16000 samples/sec * 2 bytes/sample * 10 sec = 320,000 bytes`
  - plus WAV header (~44 bytes) => approximately 320 KB.

### Repair
If microphone is disconnected / unavailable:
1. Catch and raise `DeviceNotFoundError` with user-readable guidance.
2. Set UI status to `Microphone unavailable — reconnect and retry`.
3. Ask user to verify Windows input settings and close conflicting apps.
4. Keep pipeline idle until a valid WAV exists.

### Update Docs
- Audio buffering is disk-backed to reduce RAM pressure before ASR.

---

## Step 3 — Bilingual Transcription (ASR)

### Plan
- `Transcriber` lives in `core/transcriber.py` and uses `faster-whisper`.
- Model settings for low-memory hardware:
  - Model: `tiny` (multilingual)
  - Device: `cpu` by default; auto-upgrade to `cuda` if NVIDIA GPU is detected.
  - Compute type: `int8` for lower memory usage.
- Model loading is lazy: instantiate only when `transcribe()` is first called.
- Language logic:
  - Default: `language=None` (auto-detect English/Spanish from audio).
  - Optional force mode: pass `language="en"` or `language="es"`.

### Edit Code
- Added `core/transcriber.py` with:
  - `Transcriber.transcribe(audio_path)` that returns the raw transcript string.
  - Cleanup: audio file deletion in `finally` to recover disk space.
  - Error handling for:
    - `FileNotFoundError` (missing WAV)
    - `RuntimeError` (model initialization/transcription pressure)

### Run Tools
- Test command:
  - `python core/transcriber.py <path_to_sample.wav> --language en`
- If using the Step 2 recorder output and you want to keep the file for repeated tests:
  - `python core/transcriber.py <path_to_sample.wav> --keep-audio`

### Observe
- The script prints:
  - Audio duration
  - Processing time
  - Real Time Factor (RTF)
- Formula: `RTF = processing_time / audio_duration`
  - `RTF < 1.0` => faster than real time.

### Repair
- `FileNotFoundError`: recorder likely failed or file was already cleaned.
- `RuntimeError`: close heavy apps, keep `cpu` + `int8`, retry.

### Update Docs (ASR benchmark notes for Ryzen 5)
The benchmark command above reports exact timing on your machine. Use this table after local runs:

| Audio Duration (s) | Processing Time (s) | RTF |
|---:|---:|---:|
| 10 | _fill from local run_ | _fill_ |
| 30 | _fill from local run_ | _fill_ |
| 60 | _fill from local run_ | _fill_ |

---

## Non-Blocking Hotkey Design (`pynput`)

`pynput.keyboard.Listener` runs on its own thread and only dispatches lightweight toggle events. Heavy pipeline tasks execute in a separate worker thread so UI/hotkeys remain responsive.

---

## Memory-Safe Sequential Pipeline (8GB Strategy)

Record -> Stop -> Transcribe (tiny) -> Release resources -> Rewrite (Ollama 1B) -> Clipboard/Paste
To ensure your **Gemini 1.5 Pro** coder has the perfect context for Step 3, your `README.md` should act as a "Single Source of Truth." It must reflect the hardware constraints and the successful completion of the recording module.

Here is exactly how your `README.md` should look.

---

# VoiceFlow Clone (Windows 11) — Voice-to-Text Agent

## 🛠 Project Overview

A local, privacy-focused automation agent that captures voice, transcribes it, styles it for a "relaxed but correct" tone, and pastes it into any active window.

### Hardware Constraints (Target System)

* **Processor:** AMD Ryzen 5 7520U (2.80 GHz)
* **RAM:** 8.00 GB (7.28 GB usable) — **Strict memory management required.**
* **OS:** Windows 11

---

## 🏗 Step 1 — Architecture & Plan

* **Sequential Pipeline:** To stay under the 8GB RAM limit, the app runs stages one-by-one:
`Record -> Stop -> Transcribe (Tiny) -> Style (Ollama 1B) -> Paste`.
* **Trigger:** Global Hotkey `CTRL+ALT+SPACE` managed via `pynput`.
* **Dependencies:** `pyaudio` for hardware-level streaming and `faster-whisper` for CPU-optimized inference.

---

## 🎤 Step 2 — Audio Capture Implementation

### Plan

* Implement `audio_handler.py` using **PyAudio**.
* **Memory Strategy:** Stream audio chunks directly to a temporary `.wav` file on disk to maintain a near-zero RAM footprint during recording.
* **Audio Specs:** 16kHz, Mono, 16-bit PCM (Native Whisper format).

### Observe & Metrics

* **Data Footprint:** 10 seconds of audio at these specs results in a file of approximately **320 KB**.
* **RAM Usage:** Minimal (approx. 20-40MB during active recording).

### Repair & Troubleshooting

* **ModuleNotFoundError:** Ensure `pyaudio` is installed in the local environment (`pip install pyaudio`).
* **DeviceNotFoundError:** Handled gracefully with a custom exception if the microphone is disconnected.

---

## 🔊 Step 3 — Bilingual Transcription (Next)

**Objective:** Convert the saved `.wav` file into raw text using `faster-whisper`.

* **Model:** `tiny` (Multilingual) to support English and Spanish.
* **Quantization:** `int8` to ensure the model fits within <150MB of RAM.

---

## 📁 Project Structure

```text
exercise_voice2text_agent_gem/
├── core/
│   ├── audio_handler.py    # DONE: Thread-safe recording to disk
│   ├── transcriber.py      # TODO: Faster-Whisper integration
│   ├── style_rewriter.py   # TODO: Ollama API integration
│   └── clipboard_paster.py # TODO: PyAutoGUI automation
├── main.py                 # DONE: Hotkey listener & state toggle
├── requirements.txt        # DONE: Optimized dependencies
└── README.md               # DONE: Documentation & Loop status

```

---

### Why this is better for your AI Coder:

By explicitly stating the **320 KB** calculation and the **Sequential Pipeline** logic in the `README.md`, you prevent the AI from suggesting a solution that loads everything into RAM at once, which would likely crash your 8GB Vivobook.

**Would you like me to generate the "Memory Check" utility code now? This will help you monitor your 7.28GB RAM in real-time while the transcriber runs.**
