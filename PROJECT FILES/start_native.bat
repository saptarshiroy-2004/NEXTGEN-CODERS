@echo off
title Voice Scam Shield - Full Stack Starter
color 0A

echo ===========================================
echo   🚀 Starting Voice Scam Shield locally...
echo ===========================================

:: ---- 1. Check FFmpeg ----
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠ WARNING: FFmpeg not found!
    echo   Audio features may not work until installed.
    echo   Download: https://www.gyan.dev/ffmpeg/builds/
    echo.
)

:: ---- 2. Start Backend ----
echo 🔹 Starting Backend...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload"

:: ---- 3. Start Frontend ----
echo 🔹 Starting Frontend...
start cmd /k "cd frontend && npm install && npm run dev"

:: ---- 4. Wait for both servers ----
echo Waiting for servers to start...
:wait_backend
ping 127.0.0.1 -n 2 >nul
curl http://127.0.0.1:8000 >nul 2>nul
if %errorlevel% neq 0 goto wait_backend

:wait_frontend
ping 127.0.0.1 -n 2 >nul
curl http://127.0.0.1:5173 >nul 2>nul
if %errorlevel% neq 0 goto wait_frontend

:: ---- 5. Open Browser ----
echo ✅ Both servers are running. Opening app...
start http://127.0.0.1:5173

echo All set! Press any key to exit this window...
pause >nul
