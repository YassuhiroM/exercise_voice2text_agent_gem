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