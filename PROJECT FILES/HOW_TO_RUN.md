# 🚀 Voice Scam Shield - One-Click Setup

## Quick Start (One-Click)

### Option 1: Use the Enhanced Launcher (Recommended)
**Double-click:** `🚀 START WEBSITE.bat`

This will automatically:
- ✅ Check all prerequisites (Python, Node.js, FFmpeg)
- ✅ Set up virtual environment
- ✅ Install all dependencies
- ✅ Start both backend and frontend servers
- ✅ Open your browser to http://127.0.0.1:5173

### Option 2: Use Your Existing Launcher
**Double-click:** `start_native.bat` (your original script)

### Option 3: PowerShell Version
Right-click `run_website.ps1` → "Run with PowerShell"

## What Each Script Does

| Script | Description |
|--------|-------------|
| `🚀 START WEBSITE.bat` | **Main launcher** - Use this one! |
| `run_website.bat` | Enhanced batch script with error checking |
| `run_website.ps1` | PowerShell version with colored output |
| `start_native.bat` | Your original script (also works great!) |
| `start_server.bat` | Backend-only launcher |

## Prerequisites

The launcher will check for these automatically:

1. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
2. **Node.js 16+** - [Download here](https://nodejs.org/)
3. **FFmpeg** (optional) - [Download here](https://www.gyan.dev/ffmpeg/builds/)

## Manual Setup (If needed)

If you prefer manual setup:

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## URLs After Starting

- 🌐 **Website**: http://127.0.0.1:5173
- 📡 **Backend API**: http://127.0.0.1:8000
- 📚 **API Documentation**: http://127.0.0.1:8000/docs

## Troubleshooting

### Port Already in Use
If you get port errors:
- Backend (8000): Change port in `backend/main.py` or kill the process using port 8000
- Frontend (5173): Kill the process using port 5173

### FFmpeg Warning
Audio features need FFmpeg. Download from: https://www.gyan.dev/ffmpeg/builds/
Add to your system PATH.

### Python/Node Not Found
Make sure Python and Node.js are installed and added to your system PATH.

## Project Structure

```
voice_scam_shield_v2/
├── 🚀 START WEBSITE.bat    ← **USE THIS ONE!**
├── run_website.bat         ← Enhanced launcher
├── run_website.ps1         ← PowerShell version
├── start_native.bat        ← Your original (also good)
├── backend/                ← Python/FastAPI
│   ├── main.py
│   ├── requirements.txt
│   └── venv/
└── frontend/               ← React/Vite
    ├── package.json
    └── node_modules/
```

## Development Tips

- **Hot Reload**: Both servers support hot reload - changes will auto-refresh
- **API Testing**: Visit http://127.0.0.1:8000/docs for interactive API testing
- **Logs**: Check the terminal windows for error messages
- **Stop Servers**: Close the terminal windows or press `Ctrl+C`

---

**🎉 Enjoy your Voice Scam Shield application!**
