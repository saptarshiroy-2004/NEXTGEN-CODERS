import os
import uuid
import json
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import asyncio
import re
from pydub import AudioSegment
import random

BASE = Path(__file__).parent
STORAGE = BASE / "storage"
AUDIO_DIR = STORAGE / "audio"
TRANSCRIPTS_DIR = STORAGE / "transcripts"
REPORTS_DIR = STORAGE / "reports"
for d in (STORAGE, AUDIO_DIR, TRANSCRIPTS_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Dataset paths
DATASET_PATH = Path(r"C:\Users\KIIT0001\Desktop\STUDY\HACKATHON\FRAUD CALL\datasets")
DATASET_CALLS_FILE = DATASET_PATH / "calls.jsonl"
DATASET_AUDIO_DIR = DATASET_PATH / "audio"

app = FastAPI(title="Voice Scam Shield - Simplified Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(msg)
            except:
                self.disconnect(ws)

manager = ConnectionManager()

def convert_to_wav(src_path: Path) -> Path:
    """Convert audio file to WAV format"""
    dest = AUDIO_DIR / (src_path.stem + ".wav")
    try:
        audio = AudioSegment.from_file(src_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(dest, format="wav")
        return dest
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return src_path

def simple_fraud_classifier(transcript: str) -> dict:
    """Simple rule-based fraud detection classifier"""
    transcript_lower = transcript.lower()
    
    # Fraud keywords and patterns
    scam_keywords = [
        'urgent', 'immediate', 'act now', 'limited time', 'verify account',
        'suspend', 'suspended', 'unauthorized', 'security alert', 'confirm identity',
        'social security', 'ssn', 'credit card', 'bank account', 'wire transfer',
        'bitcoin', 'cryptocurrency', 'gift card', 'iTunes', 'amazon card',
        'refund', 'owe money', 'pay now', 'arrest warrant', 'legal action',
        'irs', 'medicare', 'insurance claim', 'winner', 'congratulations',
        'free', 'no cost', 'guaranteed', 'risk-free', 'once in lifetime',
        'virus', 'hacked', 'compromised', 'malware', 'tech support'
    ]
    
    suspicious_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card pattern
        r'\$\d+',  # Money amounts
        r'call.*back.*\d{3}[-.]?\d{3}[-.]?\d{4}',  # Phone number callbacks
    ]
    
    # Calculate fraud indicators
    keyword_matches = [kw for kw in scam_keywords if kw in transcript_lower]
    pattern_matches = []
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, transcript_lower)
        pattern_matches.extend(matches)
    
    # Determine fraud level
    fraud_score = len(keyword_matches) * 0.1 + len(pattern_matches) * 0.2
    
    if fraud_score >= 0.6:
        label = "Scam"
        confidence = min(0.9, 0.7 + fraud_score * 0.2)
    elif fraud_score >= 0.3:
        label = "Suspicious"
        confidence = min(0.8, 0.6 + fraud_score * 0.1)
    else:
        label = "Safe"
        confidence = max(0.5, 1.0 - fraud_score)
    
    return {
        "label": label,
        "confidence": round(confidence, 2),
        "rationale": f"Found {len(keyword_matches)} fraud keywords and {len(pattern_matches)} suspicious patterns",
        "keywords": keyword_matches[:5],  # Limit to first 5
        "pattern_matches": pattern_matches[:3],  # Limit to first 3
        "fraud_score": round(fraud_score, 2)
    }

def mock_transcribe(wav_path: Path) -> str:
    """Enhanced mock transcription using real dataset examples"""
    # Try to get a real transcript from dataset
    calls = load_dataset_calls()
    if calls:
        # Use filename to try to match with dataset calls
        filename = wav_path.stem.lower()
        
        # First, try to match exact call IDs
        for call in calls:
            if call.get('id', '').lower() in filename:
                return call.get('transcript', '')
        
        # If no exact match, pick a random real example based on filename hints
        if 'scam' in filename:
            scam_calls = [c for c in calls if c.get('label') == 'scam']
            if scam_calls:
                return random.choice(scam_calls).get('transcript', '')
        elif 'safe' in filename:
            safe_calls = [c for c in calls if c.get('label') == 'safe']
            if safe_calls:
                return random.choice(safe_calls).get('transcript', '')
        elif 'suspicious' in filename:
            suspicious_calls = [c for c in calls if c.get('label') == 'suspicious']
            if suspicious_calls:
                return random.choice(suspicious_calls).get('transcript', '')
        
        # Otherwise, return a completely random real transcript
        return random.choice(calls).get('transcript', '')
    
    # Fallback to original samples if dataset not available
    sample_transcripts = {
        "scam": "Hello, this is urgent! Your social security number has been compromised. You need to verify your account immediately by providing your SSN and credit card details to avoid suspension.",
        "suspicious": "Congratulations! You've won a free gift card worth $500. Call us back at 555-SCAM to claim your prize. This is a limited time offer!",
        "safe": "Hi, this is John from ABC Company. I'm calling to schedule a follow-up meeting about the project we discussed. Please call me back when convenient."
    }
    
    filename = wav_path.stem.lower()
    for key, transcript in sample_transcripts.items():
        if key in filename:
            return transcript
    
    return "This is a sample transcript. In a real application, this would be the actual audio transcription from a speech recognition service."

def load_dataset_calls() -> list:
    """Load all call data from the dataset"""
    calls = []
    if DATASET_CALLS_FILE.exists():
        try:
            with open(DATASET_CALLS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        call_data = json.loads(line.strip())
                        calls.append(call_data)
        except Exception as e:
            print(f"Error loading dataset: {e}")
    return calls

def get_dataset_call_by_id(call_id: str) -> dict:
    """Get a specific call from the dataset by ID"""
    calls = load_dataset_calls()
    for call in calls:
        if call.get('id') == call_id:
            return call
    return None

def generate_report(uid: str, wav_path: Path, transcript: str, classification: dict, is_simulation: bool = False, original_label: str = None) -> dict:
    """Generate analysis report"""
    ts = datetime.utcnow().isoformat()
    report = {
        "id": uid,
        "created_at": ts,
        "audio_file": wav_path.name if wav_path else None,
        "transcript": transcript,
        "scam_detection": classification,
        "analysis_version": "simplified_v1.0",
        "is_simulation": is_simulation,
        "original_label": original_label
    }
    
    # Save report
    (REPORTS_DIR / f"{uid}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (TRANSCRIPTS_DIR / f"{uid}.txt").write_text(transcript, encoding="utf-8")
    
    return report

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and analyze audio file"""
    uid = uuid.uuid4().hex
    raw_path = AUDIO_DIR / f"{uid}_{file.filename}"
    
    # Save uploaded file
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Convert to WAV
    wav_path = convert_to_wav(raw_path)
    
    # Mock transcription (replace with real transcription service)
    transcript = mock_transcribe(wav_path)
    
    # Classify for fraud
    classification = simple_fraud_classifier(transcript)
    
    # Generate report
    report = generate_report(uid, wav_path, transcript, classification)

    # Broadcast to connected clients
    await manager.broadcast({"type": "alert", "report": report})
    
    return report

@app.post("/analyze-transcript")
async def analyze_transcript(data: dict):
    """Analyze transcript text directly"""
    transcript = data.get("transcript", "")
    if not transcript:
        return JSONResponse({"error": "No transcript provided"}, status_code=400)
    
    classification = simple_fraud_classifier(transcript)
    
    return {
        "transcript": transcript,
        "analysis": classification,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    """Get specific report by ID"""
    p = REPORTS_DIR / f"{report_id}.json"
    if not p.exists():
        return JSONResponse({"error": "Report not found"}, status_code=404)
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))

@app.get("/reports")
def list_reports():
    """List all reports"""
    reports = []
    for report_file in REPORTS_DIR.glob("*.json"):
        try:
            report_data = json.loads(report_file.read_text(encoding="utf-8"))
            reports.append({
                "id": report_data.get("id"),
                "created_at": report_data.get("created_at"),
                "label": report_data.get("scam_detection", {}).get("label", "Unknown"),
                "confidence": report_data.get("scam_detection", {}).get("confidence", 0)
            })
        except Exception:
            continue
    
    # Sort by creation time (newest first)
    reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"reports": reports[:50]}  # Limit to 50 most recent

@app.get("/audio/{filename}")
def get_audio(filename: str):
    """Serve audio files"""
    p = AUDIO_DIR / filename
    if not p.exists():
        return JSONResponse({"error": "Audio file not found"}, status_code=404)
    return FileResponse(p)

# Simulation endpoints
@app.get("/simulation/calls")
def get_simulation_calls():
    """Get all available simulation calls"""
    calls = load_dataset_calls()
    # Return summary info for the frontend
    call_summaries = []
    for call in calls:
        call_summaries.append({
            "id": call.get("id"),
            "label": call.get("label"),
            "reason": call.get("reason"),
            "transcript_preview": call.get("transcript", "")[:100] + "..." if len(call.get("transcript", "")) > 100 else call.get("transcript", "")
        })
    
    # Group by label for better organization
    grouped = {"scam": [], "suspicious": [], "safe": []}
    for call in call_summaries:
        label = call["label"]
        if label in grouped:
            grouped[label].append(call)
    
    return {
        "total": len(call_summaries),
        "calls_by_type": grouped,
        "all_calls": call_summaries
    }

@app.post("/simulation/analyze/{call_id}")
async def simulate_call_analysis(call_id: str):
    """Simulate analysis of a specific call from the dataset"""
    call_data = get_dataset_call_by_id(call_id)
    if not call_data:
        return JSONResponse({"error": "Call not found in dataset"}, status_code=404)
    
    # Get the real transcript
    transcript = call_data.get("transcript", "")
    original_label = call_data.get("label", "unknown")
    
    # Analyze with our classifier
    classification = simple_fraud_classifier(transcript)
    
    # Generate a simulation report
    uid = f"sim_{call_id}_{uuid.uuid4().hex[:8]}"
    report = generate_report(
        uid=uid,
        wav_path=None,  # No audio file for simulation
        transcript=transcript,
        classification=classification,
        is_simulation=True,
        original_label=original_label
    )
    
    # Add additional simulation data
    report["simulation_data"] = {
        "dataset_call_id": call_id,
        "original_label": original_label,
        "original_reason": call_data.get("reason", ""),
        "accuracy": "correct" if classification["label"].lower() == original_label.lower() else "incorrect",
        "has_audio": (DATASET_AUDIO_DIR / call_data.get("audio_path", "")).exists() if call_data.get("audio_path") else False
    }
    
    # Broadcast simulation result
    await manager.broadcast({
        "type": "simulation_alert", 
        "report": report,
        "is_simulation": True
    })
    
    return report

@app.get("/simulation/random")
def get_random_simulation_call():
    """Get a random call for simulation"""
    calls = load_dataset_calls()
    if not calls:
        return JSONResponse({"error": "No calls available in dataset"}, status_code=404)
    
    random_call = random.choice(calls)
    return {
        "id": random_call.get("id"),
        "label": random_call.get("label"),
        "reason": random_call.get("reason"),
        "transcript": random_call.get("transcript"),
        "has_audio": (DATASET_AUDIO_DIR / random_call.get("audio_path", "")).exists() if random_call.get("audio_path") else False
    }

@app.get("/simulation/dataset-audio/{call_id}")
def get_dataset_audio(call_id: str):
    """Serve audio files from the dataset"""
    call_data = get_dataset_call_by_id(call_id)
    if not call_data:
        return JSONResponse({"error": "Call not found"}, status_code=404)
    
    audio_path = call_data.get("audio_path")
    if not audio_path:
        return JSONResponse({"error": "No audio file associated with this call"}, status_code=404)
    
    full_audio_path = DATASET_AUDIO_DIR / audio_path
    if not full_audio_path.exists():
        return JSONResponse({"error": "Audio file not found on disk"}, status_code=404)
    
    return FileResponse(full_audio_path)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_json({"type": "pong", "message": "Connected"})
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "simplified_v1.0",
        "features": {
            "audio_upload": True,
            "transcript_analysis": True,
            "fraud_detection": True,
            "real_time_alerts": True,
            "report_storage": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Scam Shield - Simplified Backend",
        "version": "1.0",
        "endpoints": {
            "upload": "/upload-audio",
            "analyze": "/analyze-transcript", 
            "reports": "/reports",
            "health": "/health",
            "websocket": "/ws"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
