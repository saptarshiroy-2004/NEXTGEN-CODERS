@echo off
echo ===========================================
echo   🛡️ Voice Scam Shield - Simple Launch
echo ===========================================
echo.

echo ✅ Starting simplified fraud detection system...
echo.

REM Set up Python virtual environment
echo 🔧 Setting up Python environment...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

REM Install simplified dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python dependency installation failed
    pause
    exit /b 1
)

echo ✅ Python dependencies installed successfully
cd ..

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd frontend
call npm install

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Frontend dependency installation failed
    pause
    exit /b 1
)

echo ✅ Frontend dependencies installed successfully
cd ..

echo.
echo 🚀 Starting servers...
echo.

REM Start backend
echo 📡 Starting backend server...
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate.bat && python main.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo 🌐 Starting frontend server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

REM Wait for servers to start
timeout /t 5 /nobreak >nul

echo.
echo ✅ Servers are starting up!
echo.
echo 🌐 Frontend: http://localhost:5173
echo 📡 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to open the website...
pause >nul

start http://localhost:5173

echo.
echo 🎉 Voice Scam Shield is now running!
echo.
echo To stop the servers, close the server terminal windows.
pause
