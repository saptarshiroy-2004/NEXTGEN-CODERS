# Voice Scam Shield - One-Click PowerShell Launcher
param()

# Set console title and colors
$Host.UI.RawUI.WindowTitle = "Voice Scam Shield - One-Click Launcher"
Write-Host "===========================================" -ForegroundColor Green
Write-Host "  🚀 Voice Scam Shield - One-Click Start" -ForegroundColor Green  
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend/main.py")) {
    Write-Host "❌ Error: backend/main.py not found!" -ForegroundColor Red
    Write-Host "   Make sure you're running this from the project root directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend/package.json")) {
    Write-Host "❌ Error: frontend/package.json not found!" -ForegroundColor Red
    Write-Host "   Make sure you're running this from the project root directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python not found! Please install Python 3.8+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    Write-Host "✅ Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Node.js not found! Please install Node.js" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check FFmpeg (optional)
try {
    ffmpeg -version 2>$null | Out-Null
    Write-Host "✅ Found FFmpeg - audio features enabled" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: FFmpeg not found - audio features may be limited" -ForegroundColor Yellow
    Write-Host "   Download from: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
}

Write-Host ""

# Setup Python environment
Write-Host "🔹 Setting up Python environment..." -ForegroundColor Cyan
if (-not (Test-Path "backend/venv/Scripts/activate.ps1")) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    Set-Location backend
    python -m venv venv
    Set-Location ..
}

# Install Python dependencies
Write-Host "🔹 Installing Python dependencies..." -ForegroundColor Cyan
Set-Location backend
& "./venv/Scripts/activate.ps1"
pip install -r requirements.txt --quiet
deactivate
Set-Location ..

# Install Node.js dependencies  
Write-Host "🔹 Installing Node.js dependencies..." -ForegroundColor Cyan
Set-Location frontend
npm install --silent
Set-Location ..

Write-Host ""
Write-Host "✅ Dependencies ready! Starting servers..." -ForegroundColor Green
Write-Host ""

# Start Backend Server
Write-Host "🔹 Starting Backend (Python/FastAPI)..." -ForegroundColor Cyan
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ./venv/Scripts/activate.ps1; Write-Host 'Backend running at http://127.0.0.1:8000' -ForegroundColor Green; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Wait a moment for backend to initialize
Start-Sleep 3

# Start Frontend Server
Write-Host "🔹 Starting Frontend (React/Vite)..." -ForegroundColor Cyan
$frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; Write-Host 'Frontend running at http://127.0.0.1:5173' -ForegroundColor Green; npm run dev" -PassThru

# Wait for servers to be ready
Write-Host "🔹 Waiting for servers to start..." -ForegroundColor Cyan

do {
    Start-Sleep 2
    Write-Host "   Backend loading..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $backendReady = $true
    } catch {
        $backendReady = $false
    }
} while (-not $backendReady)

do {
    Start-Sleep 2
    Write-Host "   Frontend loading..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $frontendReady = $true
    } catch {
        $frontendReady = $false
    }
} while (-not $frontendReady)

Write-Host ""
Write-Host "✅ SUCCESS! Both servers are running:" -ForegroundColor Green
Write-Host "   📡 Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   🌐 Frontend: http://127.0.0.1:5173" -ForegroundColor White
Write-Host "   📚 API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""

# Open the website
Write-Host "🚀 Opening Voice Scam Shield in your browser..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host " 🎉 Voice Scam Shield is now running!" -ForegroundColor Green
Write-Host "" 
Write-Host " To stop the servers:" -ForegroundColor Yellow
Write-Host " - Close the Backend and Frontend PowerShell windows" -ForegroundColor Yellow
Write-Host " - Or press Ctrl+C in each window" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this launcher"
