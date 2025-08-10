@echo off
cd /d "%~dp0backend"
echo Starting Voice Scam Shield Backend...
call venv\Scripts\activate
uvicorn main:app --reload
pause
