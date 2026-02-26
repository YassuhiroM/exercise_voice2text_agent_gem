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

## Style Profile

- **Profile name:** Relaxed but Correct
- **Behavior:** Keep a conversational tone while fixing grammar, punctuation, capitalization, and clarity.
- **Constraint:** Return only rewritten text (no explanations).

System prompt used by Step 4:

> "You are a writing assistant. Rewrite the following text to be relaxed, conversational, but grammatically perfect. Do not add explanations, only return the corrected text."

---

## Project Structure

```text
exercise_voice2text_agent_gem/
  main.py
  core/
    __init__.py
    audio_handler.py
    transcriber.py
    style_rewriter.py
    clipboard_paster.py
    orchestrator.py
```

---

## Step 2 — Audio Capture Implementation

- `core/audio_handler.py` records microphone audio at 16kHz mono PCM16.
- Audio is streamed directly to a temporary WAV file on disk to avoid large RAM buffers.
- Start/stop/toggle methods are thread-safe.

Expected 10s file size at 16kHz mono PCM16:
- `16000 * 2 * 10 + 44` ≈ `320,044 bytes` (~320 KB)

---

## Step 3 — Bilingual Transcription (ASR)

- `core/transcriber.py` uses `faster-whisper` with:
  - model: `tiny`
  - compute type: `int8`
  - device: `cpu` (or `cuda` when NVIDIA GPU is detected)
- Supports bilingual EN/ES workflow:
  - auto-detect with `language=None`
  - forced language with `language='en'` or `language='es'`
- Cleans temporary audio file after transcription (`delete_audio=True`).

Benchmark notes for Ryzen 5:
- Script prints duration, processing time, and RTF.
- `RTF = processing_time / audio_duration`.

---

## Step 4 — Local LLM Styling (Ollama)

- `core/style_rewriter.py` uses model `llama3.2:1b` with timeout protection.
- Keep sequential resource control: unload ASR model before calling Ollama.
- Handles `ConnectionError` when Ollama service is unavailable.

---

## Step 5 — Automation & Injection (**DONE**)

### Plan
- `core/clipboard_paster.py` introduces a `Paster` class.
- Focus assumption: user already triggered via global hotkey and the cursor is in the destination app (Slack/Word/Browser/etc.).
- Paste flow:
  1. Receive text
  2. Copy to clipboard
  3. Wait 100ms
  4. Send `Ctrl+V`

### Edit Code
- Added `Paster.paste_text(text: str)` with:
  - input validation,
  - clipboard copy via `pyperclip`,
  - 0.1s delay,
  - keyboard injection via `pyautogui.hotkey("ctrl", "v")`.

### Run Tools
- Manual test command:
  - `python core/clipboard_paster.py --text "Hello from the Automation Agent!" --wait-seconds 5`
- Behavior:
  - script waits 5 seconds so you can click Notepad (or any target input), then pastes.

### Observe
- Text should appear almost instantly after the 5-second wait.
- Clipboard should match the pasted value and is printed by the script.

### Repair
- If keystrokes are not registering due to Windows permissions/security context:
  - run terminal as **Administrator** and retry.
  - ensure target application is focused and accepts keyboard shortcuts.

---

## Sequential Low-Memory Pipeline

```text
Record -> Stop -> Transcribe (tiny/int8) -> Unload ASR resources -> Rewrite (llama3.2:1b) -> Clipboard/Paste
```


---

## Final Usage (Step 6 — Full Pipeline Integration)

### Plan
- `VoiceFlowOrchestrator` maps the stop-recording event to a strict sequential chain:
  - `Transcribe -> gc.collect() -> Rewrite -> Paste`
- Console statuses are printed for visibility:
  - `[RECORDING] -> [TRANSCRIBING] -> [STYLING] -> [PASTING]`
- Temporary WAV cleanup happens at the end of the chain.

### Edit Code
- Added `core/orchestrator.py` to coordinate recorder, ASR, style rewriting, and paste automation.
- Added `main.py` to run a global `pynput` listener and bind `CTRL+ALT+SPACE` to orchestrator toggle.

### Run Tools (Big Bang Test)
```bash
python main.py
```
1. Open Notepad (or any target app).
2. Press `CTRL+ALT+SPACE` to start recording.
3. Speak in English/Spanish.
4. Press `CTRL+ALT+SPACE` again to stop + process.

### Observe
- On Ryzen 5 / 8GB RAM, you should see a RAM "wave":
  - rise during ASR,
  - dip after `gc.collect()`,
  - small rise during Ollama rewrite.

### Repair
- **Empty Audio:** If stopped too fast or silent, pipeline aborts with an informative message.
- **Ollama Down/Slow:** If styling fails or times out, raw transcript is pasted so text is not lost.
