@echo off
TITLE Voice-to-Text Agent Launcher
cd /d "%~dp0"

echo ==========================================
echo Voice2Text Agent (Windows)
echo Converts your voice into friendly, polished text and pastes it automatically.
echo.
echo Quick use:
echo   - Hold CTRL + ALT + SPACE to record
echo   - Release to stop and process
echo   - Paste is automatic (Ctrl+V is sent for you)
echo.
echo Exit:
echo   - Press ESC to quit the agent
echo   - (If needed) Ctrl+C here closes the console session
echo ==========================================
echo.

echo [1/3] Unlocking PowerShell Execution Policy...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process"

echo [2/3] Activating Python 3.11 Environment...
call venv_ucm_voice2text_python311\Scripts\activate.bat

echo [3/3] Launching Agent...
python main.py

IF ERRORLEVEL 1 (
  echo Agent exited with an error. Press any key to close...
  pause
)