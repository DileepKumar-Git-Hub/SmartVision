@echo off
REM SmartVision OCR Pro - Windows Startup Script

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║   SmartVision OCR Pro - Local Development Setup        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo 📦 Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✓ Dependencies installed

REM Download TextBlob corpora
echo.
echo 📥 Downloading language models...
python -m textblob.download_corpora > nul 2>&1
echo ✓ Models downloaded

REM Start Flask backend
echo.
echo 🚀 Starting Flask OCR Backend...
echo    Backend: http://localhost:5000
echo    Press Ctrl+C to stop
echo.

python backend/app.py

pause
