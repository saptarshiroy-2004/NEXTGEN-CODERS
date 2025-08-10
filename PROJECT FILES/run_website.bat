@echo off
title Voice Scam Shield - One-Click Launcher
color 0A

echo ===========================================
echo   🚀 Voice Scam Shield - One-Click Start
echo ===========================================
echo.

:: Check if we're in the right directory
if not exist "backend\main.py" (
    echo ❌ Error: backend\main.py not found!
    echo    Make sure you're running this from the project root directory.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ❌ Error: frontend\package.json not found!
    echo    Make sure you're running this from the project root directory.
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Node.js not found! Please install Node.js
    pause
    exit /b 1
)

:: Check FFmpeg (optional but recommended)
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Warning: FFmpeg not found - audio features may be limited
    echo    Download from: https://www.gyan.dev/ffmpeg/builds/
    echo.
)

:: Check/Create Python virtual environment
echo 🔹 Setting up Python environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo    Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

:: Install Python dependencies
echo 🔹 Installing Python dependencies...
cd backend
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
cd ..

:: Install Node.js dependencies
echo 🔹 Installing Node.js dependencies...
cd frontend
call npm install --silent
cd ..

echo.
echo ✅ Dependencies ready! Starting servers...
echo.

:: Start Backend Server
echo 🔹 Starting Backend (Python/FastAPI)...
start "VSS-Backend" cmd /k "cd backend && venv\Scripts\activate && echo Backend running at http://127.0.0.1:8000 && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend Server
echo 🔹 Starting Frontend (React/Vite)...
start "VSS-Frontend" cmd /k "cd frontend && echo Frontend running at http://127.0.0.1:5173 && npm run dev"

:: Wait for servers to be ready
echo 🔹 Waiting for servers to start...

:wait_backend
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8000/docs >nul 2>&1
if %errorlevel% neq 0 (
    echo    Backend loading...
    goto wait_backend
)

:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:5173 >nul 2>&1
if %errorlevel% neq 0 (
    echo    Frontend loading...
    goto wait_frontend
)

echo.
echo ✅ SUCCESS! Both servers are running:
echo    📡 Backend:  http://127.0.0.1:8000
echo    🌐 Frontend: http://127.0.0.1:5173
echo    📚 API Docs: http://127.0.0.1:8000/docs
echo.

:: Open the website
echo 🚀 Opening Voice Scam Shield in your browser...
start http://127.0.0.1:5173

echo.
echo ════════════════════════════════════════════
echo  🎉 Voice Scam Shield is now running!
echo  
echo  To stop the servers:
echo  - Close the Backend and Frontend terminal windows
echo  - Or press Ctrl+C in each window
echo ════════════════════════════════════════════
echo.
echo Press any key to close this launcher...
pause >nul
