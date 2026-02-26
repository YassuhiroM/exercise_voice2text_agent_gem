# VoiceFlow Clone (Windows 11) — Voice-to-Text Agent

## 🛠 Project Overview
A local, privacy-focused automation agent. It captures voice via a global hotkey, transcribes bilingual speech (EN/ES), styles it via Ollama, and auto-pastes it into the active window.

### Hardware & Environment
* **CPU:** AMD Ryzen 5 7520U
* **RAM:** 8.00 GB (7.28 GB usable) — **Optimized with Sequential Processing.**
* **Python:** 3.11.9 (Stable for AI libraries)

---

## 🏗 System Architecture (Memory Safety)
To prevent system lag, the agent executes tasks sequentially:
1. **Record:** 16kHz Mono audio streamed to disk (~320KB per 10s).
2. **Transcribe:** `faster-whisper` (tiny/int8) processed on CPU.
3. **Style:** Local `Ollama` (llama3.2:1b) for grammar correction.
4. **Paste:** `pyautogui` injection into active cursor.

---

## 📁 Project Structure
```text
exercise_voice2text_agent_gem/
├── core/
│   ├── transcriber.py      # DONE: Whisper-tiny integration
│   ├── style_rewriter.py   # DONE: Ollama 1B styling
│   └── clipboard_paster.py # DONE: Automation logic
├── audio_handler.py        # DONE: PyAudio recording logic
├── main.py                 # DONE: Orchestrator & Hotkey Listener
├── requirements.txt        # DONE: Verified dependencies
└── README.md               # DONE: Final Documentation
