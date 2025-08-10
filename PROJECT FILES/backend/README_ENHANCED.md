# Voice Scam Shield - Enhanced Backend v2.0

🛡️ **Advanced real-time voice fraud detection system with machine learning capabilities**

## 🌟 New Features

### Enhanced Transcription
- **Real-time transcription** with multiple engine support (Google Speech Recognition, Vosk, OpenAI Whisper)
- **Audio quality analysis** and preprocessing
- **Fallback mechanisms** for reliable transcription
- **Live streaming transcription** via WebSocket

### Advanced Fraud Classification
- **Machine Learning-powered classification** with 80%+ accuracy target
- **Pattern-based detection** with 40+ fraud indicators
- **Linguistic analysis** including urgency detection, personal info extraction
- **Risk scoring system** with detailed rationale
- **Real-time analysis** with actionable recommendations

### Real-time Processing
- **WebSocket-based live transcription** and analysis
- **Streaming audio processing** with 3-second chunks
- **Live risk assessment** during ongoing calls
- **Session management** with comprehensive reporting

## 📋 Quick Setup

### Automated Setup (Recommended)
```bash
# Navigate to backend directory
cd backend

# Run the enhanced setup script
python setup_enhanced.py
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create .env file from template
cp .env.template .env
# Edit .env with your configuration
```

## 🚀 Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### Core Endpoints (Original)
- `POST /upload-audio` - Basic audio analysis
- `GET /reports/{report_id}` - Retrieve analysis report
- `GET /audio/{filename}` - Download audio file
- `WebSocket /ws` - Basic WebSocket connection

### Enhanced Endpoints (New)
- `POST /upload-audio-enhanced` - Advanced audio analysis with ML
- `POST /analyze-transcript` - Analyze text with enhanced classifier
- `WebSocket /ws/live-transcription` - Real-time transcription and analysis
- `GET /health` - System health and feature status

## 🎯 Enhanced Classification Features

### Fraud Pattern Detection
- **Financial scams**: Money transfer requests, banking info theft
- **Verification scams**: OTP requests, account verification
- **Authority impersonation**: IRS, police, tech support scams
- **Urgency tactics**: Time pressure, account threats
- **Tech support scams**: Remote access, fake virus alerts
- **Romance scams**: Military/overseas money requests
- **Investment scams**: Cryptocurrency, unrealistic returns
- **Prize/lottery scams**: Winner notifications, claim fees

### Machine Learning Features
- **TF-IDF vectorization** with n-gram analysis
- **Naive Bayes classification** with training data
- **Cross-validation** for accuracy measurement
- **Automatic model retraining** capabilities

### Linguistic Analysis
- Word count and sentence structure analysis
- Urgency and pressure tactic detection
- Money and financial term extraction
- Personal information request identification
- Emotional manipulation indicators

## 📊 Classification Output Example

```json
{
  "label": "Scam",
  "confidence": 0.887,
  "risk_score": 0.745,
  "rationale": "Detected 4 fraud indicators: financial: Money transfer request, verification: OTP keyword, urgency: Time pressure tactic",
  "keywords": ["Money transfer request", "OTP keyword", "Time pressure tactic"],
  "fraud_indicators": [
    "financial: Money transfer request",
    "verification: OTP/verification code request", 
    "urgency: Time pressure tactic",
    "impersonation: Bank impersonation"
  ],
  "linguistic_features": {
    "word_count": 45,
    "urgency_words": 3,
    "money_words": 2,
    "personal_info_words": 1
  },
  "pattern_matches": ["financial", "verification", "urgency", "impersonation"],
  "recommendation": "⚠️ HIGH RISK: This appears to be a scam call. Do NOT provide personal information, money, or access to your devices. Hang up immediately and report the call.",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 🌐 WebSocket Real-time Analysis

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-transcription');
```

### Protocol
```json
// Start session
{"type": "start"}

// Send audio chunk (base64 encoded)
{"type": "audio_chunk", "data": "base64_audio_data"}

// Stop session
{"type": "stop"}
```

### Real-time Response
```json
{
  "type": "live_transcription",
  "session_id": "abc123...",
  "segment": {"text": "Hello, this is your bank...", "confidence": 0.95},
  "accumulated_transcript": "Hello, this is your bank calling about suspicious activity...",
  "analysis": {
    "label": "Suspicious",
    "confidence": 0.72,
    "risk_score": 0.45,
    "recommendation": "⚠️ SUSPICIOUS: This call shows warning signs...",
    "fraud_indicators": ["impersonation: Bank impersonation", "urgency: Account threat"]
  },
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## ⚙️ Configuration (.env)

```env
# OpenAI API Key (optional)
OPENAI_API_KEY=your_api_key_here

# Transcription Engine
TRANSCRIPTION_ENGINE=google  # Options: google, vosk, openai

# Classification Engine  
CLASSIFICATION_ENGINE=enhanced  # Options: enhanced, openai, basic

# Real-time Features
ENABLE_REAL_TIME_TRANSCRIPTION=true
ENABLE_ML_CLASSIFICATION=true

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

## 🔧 Dependencies

### Core Dependencies
- FastAPI - Web framework
- Pydub - Audio processing
- OpenAI - AI services (optional)
- NumPy - Numerical computing

### Enhanced Dependencies
- SpeechRecognition - Multiple STT engines
- Vosk - Offline speech recognition
- Scikit-learn - Machine learning
- NLTK - Natural language processing
- LibROSA - Audio analysis
- WebRTCVAD - Voice activity detection

## 📈 Performance Targets

- **Transcription Accuracy**: 85%+ with fallback engines
- **Classification Accuracy**: 80%+ with ML model
- **Real-time Latency**: <3 seconds per chunk
- **False Positive Rate**: <10%
- **Processing Speed**: 50+ audio files/minute

## 🔍 Accuracy Improvements

### Transcription Enhancements
1. **Multi-engine fallback**: Google → Vosk → OpenAI → Basic
2. **Audio quality analysis**: SNR, clarity, noise detection
3. **Preprocessing**: Noise reduction, volume normalization
4. **Chunk overlap**: 50% overlap for better continuity

### Classification Enhancements
1. **40+ fraud patterns** with regex and keyword matching
2. **Machine learning model** trained on diverse datasets
3. **Linguistic feature extraction** (urgency, personal info, etc.)
4. **Risk scoring algorithm** combining multiple factors
5. **Real-time pattern updates** based on new fraud trends

## 🛠️ Development

### Adding New Fraud Patterns
```python
# In enhanced_fraud_classifier.py
FraudPattern(
    pattern=r"\\b(new|pattern)\\s+(regex)",
    weight=2.0,
    category="new_category", 
    description="Description of the pattern",
    regex=True
)
```

### Testing Classification
```python
from enhanced_fraud_classifier import get_global_classifier

classifier = get_global_classifier()
result = classifier.classify("Test transcript here")
print(f"Label: {result.label}, Confidence: {result.confidence}")
```

### Adding Transcription Engines
```python
# In real_time_transcriber.py
class CustomTranscriber(TranscriptionEngine):
    def transcribe(self, audio_path: Path) -> TranscriptionSegment:
        # Implement custom transcription logic
        return TranscriptionSegment(...)
```

## 🐛 Troubleshooting

### Common Issues

**PyAudio Installation Fails**
```bash
# Windows
pip install pipwin && pipwin install pyaudio

# Linux
sudo apt-get install python3-pyaudio portaudio19-dev

# macOS  
brew install portaudio
```

**Vosk Model Not Found**
```bash
# Download manually
mkdir models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

**Real-time WebSocket Disconnects**
- Check firewall settings
- Increase WebSocket timeout
- Verify audio chunk encoding

### Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View logs
tail -f logs/voice_scam_shield.log
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### System Status
The `/health` endpoint provides:
- Feature availability status
- ML model status
- Transcription engine status
- System resource usage

## 🔮 Future Enhancements

- [ ] **Deep learning models** for better accuracy
- [ ] **Multi-language support** for global fraud detection  
- [ ] **Voice biometric analysis** for caller identification
- [ ] **Emotion detection** in voice patterns
- [ ] **Call recording integration** with PBX systems
- [ ] **Real-time dashboard** with fraud analytics
- [ ] **API rate limiting** and authentication
- [ ] **Database integration** for historical analysis

## 📄 License

This enhanced backend maintains the same license as the original project.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

**🛡️ Enhanced Voice Scam Shield - Protecting against voice fraud with AI**
