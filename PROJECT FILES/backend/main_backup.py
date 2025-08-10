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
import openai
from pydub import AudioSegment
from offline_transcriber import offline_transcribe
from offline_classifier import offline_classify
# Enhanced modules for improved accuracy
from real_time_transcriber import enhanced_offline_transcribe, RealTimeTranscriber
from enhanced_fraud_classifier import enhanced_offline_classify, get_global_classifier
from live_fraud_monitor import RealTimeFraudMonitor, enhanced_live_monitoring_endpoint

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

BASE = Path(__file__).parent
STORAGE = BASE / "storage"
AUDIO_DIR = STORAGE / "audio"
TRANSCRIPTS_DIR = STORAGE / "transcripts"
REPORTS_DIR = STORAGE / "reports"
for d in (STORAGE, AUDIO_DIR, TRANSCRIPTS_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Voice Scam Shield - Backend")

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
    dest = AUDIO_DIR / (src_path.stem + ".wav")
    audio = AudioSegment.from_file(src_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(dest, format="wav")
    return dest

def call_openai_transcribe(wav_path: Path) -> str:
    """Try OpenAI transcription, fallback if quota fails."""
    try:
        with open(wav_path, "rb") as f:
            resp = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return resp.text.strip()
    except Exception as e:
        if "insufficient_quota" in str(e):
            print("⚠ Quota exceeded, using offline transcription.")
            return offline_transcribe(wav_path)
        print("❌ Transcription failed:", e)
        return "[TRANSCRIPTION ERROR]"

def call_openai_classifier(transcript: str, model_name: str = "gpt-4o-mini") -> dict:
    """Try OpenAI classification, fallback if quota fails."""
    system = "You are a concise classifier. Return ONLY a JSON object with keys: label, confidence, rationale, keywords."
    prompt = f"Transcript:\n\"\"\"{transcript}\"\"\"\n\nClassify as one of: Scam, Suspicious, Safe. Provide a short rationale and keywords."
    try:
        resp = openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=400,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        if "insufficient_quota" in str(e):
            print("⚠ Quota exceeded, using offline classification.")
            return offline_classify(transcript)
        print("❌ Classification failed:", e)
        return offline_classify(transcript)

def generate_report(uid: str, wav_path: Path, transcript: str, classification: dict) -> dict:
    ts = datetime.utcnow().isoformat()
    report = {
        "id": uid,
        "created_at": ts,
        "audio_file": wav_path.name,
        "transcript": transcript,
        "scam_detection": classification
    }
    (REPORTS_DIR / f"{uid}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (TRANSCRIPTS_DIR / f"{uid}.txt").write_text(transcript, encoding="utf-8")
    return report

def generate_enhanced_report(uid: str, wav_path: Path, transcript: str, classification: dict) -> dict:
    """Generate enhanced report with additional analysis details"""
    ts = datetime.utcnow().isoformat()
    report = {
        "id": uid,
        "created_at": ts,
        "audio_file": wav_path.name,
        "transcript": transcript,
        "enhanced_scam_detection": classification,
        "analysis_type": "enhanced",
        "version": "2.0"
    }
    
    # Save enhanced report
    enhanced_filename = f"{uid}_enhanced.json"
    (REPORTS_DIR / enhanced_filename).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (TRANSCRIPTS_DIR / f"{uid}.txt").write_text(transcript, encoding="utf-8")
    
    return report

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    raw_path = AUDIO_DIR / f"{uid}_{file.filename}"
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    wav_path = convert_to_wav(raw_path)
    transcript = call_openai_transcribe(wav_path)
    classification = call_openai_classifier(transcript)
    report = generate_report(uid, wav_path, transcript, classification)

    asyncio.create_task(manager.broadcast({"type": "alert", "report": report}))
    return report

@app.post("/upload-audio-enhanced")
async def upload_audio_enhanced(file: UploadFile = File(...)):
    """Enhanced audio upload with improved transcription and classification"""
    uid = uuid.uuid4().hex
    raw_path = AUDIO_DIR / f"{uid}_{file.filename}"
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    wav_path = convert_to_wav(raw_path)
    
    # Try enhanced transcription first, fallback to OpenAI, then basic offline
    transcript = ""
    try:
        transcript = enhanced_offline_transcribe(wav_path)
        print("✅ Enhanced transcription successful")
    except Exception as e:
        print(f"⚠️ Enhanced transcription failed: {e}")
        try:
            transcript = call_openai_transcribe(wav_path)
            print("✅ OpenAI transcription fallback successful")
        except Exception as e2:
            print(f"⚠️ OpenAI transcription failed: {e2}")
            transcript = offline_transcribe(wav_path)
            print("✅ Basic offline transcription fallback")
    
    # Use enhanced classification
    try:
        classification = enhanced_offline_classify(transcript)
        print("✅ Enhanced classification successful")
    except Exception as e:
        print(f"⚠️ Enhanced classification failed: {e}")
        classification = call_openai_classifier(transcript)
    
    report = generate_enhanced_report(uid, wav_path, transcript, classification)
    
    asyncio.create_task(manager.broadcast({
        "type": "enhanced_alert", 
        "report": report,
        "enhanced": True
    }))
    return report

@app.post("/analyze-transcript")
async def analyze_transcript(data: dict):
    """Analyze transcript text with enhanced classifier"""
    transcript = data.get("transcript", "")
    if not transcript:
        return JSONResponse({"error": "No transcript provided"}, status_code=400)
    
    try:
        # Get global classifier instance for better performance
        classifier = get_global_classifier()
        result = classifier.classify(transcript)
        
        # Convert to dictionary for JSON response
        return {
            "label": result.label,
            "confidence": result.confidence,
            "risk_score": result.risk_score,
            "rationale": result.rationale,
            "keywords": result.keywords,
            "fraud_indicators": result.fraud_indicators,
            "linguistic_features": result.linguistic_features,
            "pattern_matches": result.pattern_matches,
            "recommendation": result.recommendation,
            "timestamp": result.timestamp
        }
    except Exception as e:
        return JSONResponse({"error": f"Analysis failed: {str(e)}"}, status_code=500)

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    p = REPORTS_DIR / f"{report_id}.json"
    if not p.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))

@app.get("/audio/{filename}")
def get_audio(filename: str):
    p = AUDIO_DIR / filename
    if not p.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(p)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
            await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.websocket("/ws/live-transcription")
async def live_transcription_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time audio transcription and analysis"""
    await ws.accept()
    
    # Initialize real-time transcriber
    transcriber = None
    session_id = uuid.uuid4().hex
    accumulated_transcript = ""
    
    async def transcription_callback(segment):
        """Callback for when transcription segments are available"""
        nonlocal accumulated_transcript
        
        if segment.get('text'):
            accumulated_transcript += " " + segment['text']
            
            # Analyze the current accumulated transcript
            try:
                classifier = get_global_classifier()
                result = classifier.classify(accumulated_transcript.strip())
                
                response = {
                    "type": "live_transcription",
                    "session_id": session_id,
                    "segment": segment,
                    "accumulated_transcript": accumulated_transcript.strip(),
                    "analysis": {
                        "label": result.label,
                        "confidence": result.confidence,
                        "risk_score": result.risk_score,
                        "recommendation": result.recommendation,
                        "fraud_indicators": result.fraud_indicators[:3]  # Limit for performance
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await ws.send_json(response)
                
            except Exception as e:
                await ws.send_json({
                    "type": "error",
                    "message": f"Analysis error: {str(e)}",
                    "segment": segment
                })
    
    try:
        while True:
            # Receive audio data or control messages
            data = await ws.receive_json()
            
            if data.get("type") == "start":
                # Initialize transcriber for real-time processing
                try:
                    transcriber = RealTimeTranscriber(
                        callback=transcription_callback,
                        preferred_engine="google",  # Use Google Speech Recognition for real-time
                        chunk_duration=3.0
                    )
                    await ws.send_json({
                        "type": "started",
                        "session_id": session_id,
                        "message": "Real-time transcription started"
                    })
                except Exception as e:
                    await ws.send_json({
                        "type": "error",
                        "message": f"Failed to start transcriber: {str(e)}"
                    })
            
            elif data.get("type") == "audio_chunk":
                # Process audio chunk (base64 encoded)
                if transcriber:
                    try:
                        import base64
                        audio_data = base64.b64decode(data.get("data", ""))
                        
                        # Create temporary audio file
                        temp_path = AUDIO_DIR / f"temp_{session_id}.wav"
                        with open(temp_path, "wb") as f:
                            f.write(audio_data)
                        
                        # Process audio chunk
                        await transcriber.process_audio_chunk(temp_path)
                        
                        # Clean up temporary file
                        if temp_path.exists():
                            temp_path.unlink()
                            
                    except Exception as e:
                        await ws.send_json({
                            "type": "error",
                            "message": f"Audio processing error: {str(e)}"
                        })
            
            elif data.get("type") == "stop":
                # Stop transcription and provide final analysis
                if transcriber:
                    transcriber = None
                
                if accumulated_transcript.strip():
                    # Generate final comprehensive report
                    try:
                        classifier = get_global_classifier()
                        final_result = classifier.classify(accumulated_transcript.strip())
                        
                        final_report = {
                            "type": "session_complete",
                            "session_id": session_id,
                            "final_transcript": accumulated_transcript.strip(),
                            "final_analysis": {
                                "label": final_result.label,
                                "confidence": final_result.confidence,
                                "risk_score": final_result.risk_score,
                                "rationale": final_result.rationale,
                                "keywords": final_result.keywords,
                                "fraud_indicators": final_result.fraud_indicators,
                                "linguistic_features": final_result.linguistic_features,
                                "pattern_matches": final_result.pattern_matches,
                                "recommendation": final_result.recommendation
                            },
                            "timestamp": final_result.timestamp
                        }
                        
                        # Save session report
                        session_report_path = REPORTS_DIR / f"session_{session_id}.json"
                        session_report_path.write_text(json.dumps(final_report, indent=2, ensure_ascii=False))
                        
                        await ws.send_json(final_report)
                        
                    except Exception as e:
                        await ws.send_json({
                            "type": "error",
                            "message": f"Final analysis error: {str(e)}"
                        })
                
                break
    
    except WebSocketDisconnect:
        # Clean up on disconnect
        if transcriber:
            transcriber = None
    except Exception as e:
        await ws.send_json({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        })

# Initialize global fraud monitor
fraud_monitor = RealTimeFraudMonitor(alert_threshold=0.3)

@app.websocket("/ws/live-fraud-monitor")
async def enhanced_live_fraud_monitoring(ws: WebSocket):
    """Enhanced WebSocket endpoint for comprehensive real-time fraud monitoring"""
    await enhanced_live_monitoring_endpoint(ws, fraud_monitor)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0",
        "features": {
            "enhanced_transcription": True,
            "enhanced_classification": True,
            "real_time_analysis": True,
            "live_fraud_monitoring": True,
            "immediate_warnings": True,
            "machine_learning": HAS_SKLEARN if 'HAS_SKLEARN' in globals() else False
        },
        "timestamp": datetime.utcnow().isoformat()
    }
