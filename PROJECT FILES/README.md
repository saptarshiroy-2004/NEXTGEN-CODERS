# 🎙️ Voice Scam Shield – v2 (OpenAI ASR + LLM)

## 📌 Overview
**Voice Scam Shield – v2** is a ready-to-run local prototype that detects potential scam calls from audio input.

**Features:**
- **FastAPI Backend** with:
  - OpenAI Whisper ASR (speech-to-text)
  - OpenAI LLM classification (Scam / Suspicious / Safe)
  - Offline fallback (faster-whisper + heuristic classification)
- **React Frontend** (Vite)
- **Docker Compose** support for running backend + frontend together
- WebSocket alerts for real-time updates

---

## ⚙️ Requirements
- Python **3.9+**
- Node.js **16+**
- (Optional) **Docker & Docker Compose**
- OpenAI API key (**paid account recommended** for transcription/classification)

---


---

## 🔑 Environment Variables
Create a `.env` file **inside** the backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Backend will be available at:
➡️ http://127.0.0.1:8000
Swagger Docs:
➡️ http://127.0.0.1:8000/docs

cd frontend
npm install
npm run dev

Frontend will be available at:
➡️ http://127.0.0.1:5173




