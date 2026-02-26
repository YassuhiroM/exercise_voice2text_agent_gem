# VoiceFlow Clone (Windows 11) — Voice-to-Text Agent

## 🛠 Project Overview
A local, privacy-focused automation agent designed for Windows 11. It captures voice via a global hotkey, transcribes bilingual speech (EN/ES), styles the text for a "relaxed but correct" tone, and auto-pastes it into the active window.

### Hardware Context (Critical for Performance)
* **CPU:** AMD Ryzen 5 7520U (2.80 GHz)
* **RAM:** 8.00 GB (7.28 GB usable)
* **GPU:** Integrated Radeon Graphics (shares system RAM)

---

## 🏗 System Architecture (8GB RAM Strategy)
To prevent system freezing and memory swapping, this agent uses a **Sequential Pipeline**:
1. **Record:** Stream audio directly to disk to keep RAM footprint < 50MB.
2. **Stop & Transcribe:** Load `faster-whisper` (tiny), process, then release resources.
3. **Style:** Call local `Ollama` API to process text using `llama3.2:1b`.
4. **Paste:** Use `pyautogui` to inject text into the active cursor position.

---

## 📁 Project Structure
```text
exercise_voice2text_agent_gem/
├── core/
│   ├── audio_handler.py    # DONE: Thread-safe 16kHz recording to WAV
│   ├── transcriber.py      # DONE: Bilingual faster-whisper (tiny/int8)
│   ├── style_rewriter.py   # TODO: Ollama 1B integration
│   └── clipboard_paster.py # TODO: PyAutoGUI automation
├── main.py                 # DONE: pynput Hotkey listener (CTRL+ALT+SPACE)
├── requirements.txt        # DONE: Optimized dependencies
└── README.md               # DONE: Documentation & Loop status
🚀 Setup & Usage
1. Environment
Recommended virtual environment: venv_ucm_general_python311

PowerShell
python -m venv venv_ucm_general_python311
.\venv_ucm_general_python311\Scripts\Activate.ps1
pip install -r requirements.txt
2. Local Models
ASR: Handled automatically by faster-whisper.

Styling: Install Ollama and run:
ollama pull llama3.2:1b

📈 Development Progress (Didactic Log)
Step 1 & 2: Audio & Trigger [DONE]
Status: Functional. Records at 16kHz Mono to minimize data size (~320KB per 10s).

Safety: Uses a thread-safe lock to prevent race conditions during rapid hotkey toggles.

Step 3: Transcription [DONE]
Model: tiny (multilingual) with int8 quantization.

Performance: Optimized for CPU inference on Ryzen 5.

Step 4: Styling [IN PROGRESS]
Objective: Implement style_rewriter.py to interface with Ollama.

Persona: Relaxed but grammatically perfect.
