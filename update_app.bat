@echo off
setlocal enabledelayedexpansion

TITLE "Voice-to-Text Sync & Update"
cd /d "%~dp0"

set "FAILED=0"
set "STASHED=0"

echo.
echo ================================
echo Voice2Text - Sync ^& Update
echo ================================
echo Repo folder: %CD%
echo.

echo [1/3] Pulling latest changes from GitHub...

git rev-parse --is-inside-work-tree >nul 2>&1
IF ERRORLEVEL 1 (
  echo [ERROR] This folder is not a git repository.
  set "FAILED=1"
  goto :END
)

REM If working tree has changes, stash them first
git diff --quiet
IF ERRORLEVEL 1 (
  echo [INFO] Local changes detected. Stashing before pull...
  git stash push -m "auto-stash update_app"
  IF ERRORLEVEL 1 (
    echo [ERROR] Failed to stash local changes.
    set "FAILED=1"
    goto :END
  )
  set "STASHED=1"
)

git pull origin main
IF ERRORLEVEL 1 (
  echo [ERROR] git pull failed. Fix git issues and retry.
  set "FAILED=1"
  goto :END
)

REM Re-apply stashed changes (may conflict)
IF "%STASHED%"=="1" (
  echo [INFO] Re-applying stashed changes...
  git stash pop
  IF ERRORLEVEL 1 (
    echo [WARN] Stash pop had conflicts. Resolve them, then commit.
    set "FAILED=1"
    goto :END
  )
)

echo.
echo [2/3] Updating Python packages...
IF NOT EXIST "venv_ucm_voice2text_python311\Scripts\activate.bat" (
  echo [ERROR] Virtual environment not found: venv_ucm_voice2text_python311
  set "FAILED=1"
  goto :END
)

call venv_ucm_voice2text_python311\Scripts\activate.bat
IF ERRORLEVEL 1 (
  echo [ERROR] Failed to activate virtual environment.
  set "FAILED=1"
  goto :END
)

python -m pip install --upgrade pip
IF ERRORLEVEL 1 (
  echo [ERROR] Failed to upgrade pip.
  set "FAILED=1"
  goto :END
)

IF NOT EXIST "requirements.txt" (
  echo [ERROR] requirements.txt not found in %CD%
  set "FAILED=1"
  goto :END
)

python -m pip install -r requirements.txt
IF ERRORLEVEL 1 (
  echo [ERROR] pip install failed. Check the error above.
  set "FAILED=1"
  goto :END
)

echo.
echo [3/3] Checking Ollama Status (optional)...
where ollama >nul 2>&1
IF ERRORLEVEL 1 (
  echo [INFO] Ollama not found. Skipping.
) ELSE (
  ollama list
  IF ERRORLEVEL 1 (
    echo [WARN] Ollama command failed. If you don't use Ollama, ignore this.
  )
)

:END
echo.
echo ======================================================
IF "%FAILED%"=="0" (
  echo Done! Your local app is synced and dependencies are updated.
  echo ======================================================
  exit /b 0
) ELSE (
  echo Update finished with errors. Please review messages above.
  echo ======================================================
  pause
  exit /b 1
)