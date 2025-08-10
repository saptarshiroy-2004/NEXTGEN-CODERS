Voice Scam Shield - v2 (OpenAI ASR + LLM)
----------------------------------------

This repo is a ready-to-run local prototype:
- FastAPI backend (OpenAI Whisper + OpenAI LLM classification)
- React frontend (Vite)
- Docker Compose to run backend + frontend

Important:
- Put your OpenAI key into a `.env` file or export `OPENAI_API_KEY` in your shell.
- The backend will try to call the OpenAI API. If OpenAI is unreachable, it falls back to simulated outputs so you can still test the UI.

Run locally (without Docker):
1) Backend
   cd backend
   python -m venv venv
   source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

2) Frontend
   cd frontend
   npm install
   npm run dev

Run with Docker:
- Create a .env with OPENAI_API_KEY=sk-...
- docker compose up --build

