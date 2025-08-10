import asyncio
import websockets
import numpy as np
import json
import wave
import io
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# Enhanced offline transcription with better accuracy
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    print("⚠️ speech_recognition not installed. Install with: pip install SpeechRecognition")

try:
    import vosk
    import soundfile as sf
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False
    print("⚠️ vosk not installed. Install with: pip install vosk")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio"""
    text: str
    confidence: float
    start_time: float
    end_time: float
    timestamp: str
    is_final: bool = True
    speaker_id: Optional[str] = None

@dataclass
class AudioMetrics:
    """Audio quality and processing metrics"""
    sample_rate: int
    duration: float
    amplitude_avg: float
    amplitude_max: float
    noise_level: float
    clarity_score: float

class RealTimeTranscriber:
    """Enhanced real-time audio transcription with multiple engines"""

class EnhancedRealTimeTranscriber(RealTimeTranscriber):
    """Alias for backward compatibility"""
    pass
    
    def __init__(self, model_path: Optional[str] = None):
        self.is_running = False
        self.current_segment = ""
        self.segments: List[TranscriptionSegment] = []
        self.callbacks = []
        
        # Initialize speech recognition engines
        self.sr_recognizer = None
        self.vosk_model = None
        self.vosk_recognizer = None
        
        if HAS_SPEECH_RECOGNITION:
            self.sr_recognizer = sr.Recognizer()
            # Adjust for ambient noise
            self.sr_recognizer.energy_threshold = 300
            self.sr_recognizer.dynamic_energy_threshold = True
            self.sr_recognizer.pause_threshold = 0.5
            
        if HAS_VOSK and model_path and Path(model_path).exists():
            try:
                self.vosk_model = vosk.Model(model_path)
                self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
                logger.info("✅ Vosk model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load Vosk model: {e}")
    
    def add_callback(self, callback):
        """Add callback for real-time transcription updates"""
        self.callbacks.append(callback)
    
    async def notify_callbacks(self, segment: TranscriptionSegment):
        """Notify all callbacks of new transcription"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(segment)
                else:
                    callback(segment)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def analyze_audio_quality(self, audio_data: np.ndarray, sample_rate: int) -> AudioMetrics:
        """Analyze audio quality metrics"""
        duration = len(audio_data) / sample_rate
        amplitude_avg = np.mean(np.abs(audio_data))
        amplitude_max = np.max(np.abs(audio_data))
        
        # Simple noise estimation using high-frequency content
        if len(audio_data) > 1024:
            fft = np.fft.fft(audio_data)
            high_freq_energy = np.mean(np.abs(fft[len(fft)//2:]))
            total_energy = np.mean(np.abs(fft))
            noise_level = high_freq_energy / (total_energy + 1e-8)
        else:
            noise_level = 0.1
        
        # Calculate clarity score (simple heuristic)
        clarity_score = min(1.0, amplitude_avg * 10) * (1 - min(0.9, noise_level))
        
        return AudioMetrics(
            sample_rate=sample_rate,
            duration=duration,
            amplitude_avg=float(amplitude_avg),
            amplitude_max=float(amplitude_max),
            noise_level=float(noise_level),
            clarity_score=float(clarity_score)
        )
    
    def transcribe_with_google(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[TranscriptionSegment]:
        """Transcribe using Google Speech Recognition (free tier)"""
        if not HAS_SPEECH_RECOGNITION or not self.sr_recognizer:
            return None
        
        try:
            # Convert numpy array to audio data
            audio_bytes = io.BytesIO()
            with wave.open(audio_bytes, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            audio_bytes.seek(0)
            with sr.AudioFile(audio_bytes) as source:
                audio = self.sr_recognizer.record(source)
            
            # Use Google's free tier
            text = self.sr_recognizer.recognize_google(audio, show_all=False)
            
            return TranscriptionSegment(
                text=text,
                confidence=0.8,  # Google doesn't provide confidence in free tier
                start_time=0.0,
                end_time=len(audio_data) / sample_rate,
                timestamp=datetime.utcnow().isoformat(),
                is_final=True
            )
        except sr.UnknownValueError:
            logger.debug("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def transcribe_with_vosk(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[TranscriptionSegment]:
        """Transcribe using Vosk (offline)"""
        if not HAS_VOSK or not self.vosk_recognizer:
            return None
        
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Feed audio data to Vosk
            if self.vosk_recognizer.AcceptWaveform(audio_int16.tobytes()):
                result = json.loads(self.vosk_recognizer.Result())
                text = result.get('text', '')
                confidence = result.get('confidence', 0.7)
                
                if text.strip():
                    return TranscriptionSegment(
                        text=text,
                        confidence=confidence,
                        start_time=0.0,
                        end_time=len(audio_data) / sample_rate,
                        timestamp=datetime.utcnow().isoformat(),
                        is_final=True
                    )
            return None
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return None
    
    def fallback_transcribe(self, audio_data: np.ndarray) -> TranscriptionSegment:
        """Fallback transcription when all engines fail"""
        # Analyze audio to provide meaningful fallback
        metrics = self.analyze_audio_quality(audio_data, 16000)
        
        if metrics.clarity_score < 0.3:
            text = "[AUDIO TOO UNCLEAR TO TRANSCRIBE]"
            confidence = 0.1
        elif metrics.amplitude_avg < 0.01:
            text = "[SILENCE OR VERY LOW AUDIO]"
            confidence = 0.2
        else:
            text = "[TRANSCRIPTION UNAVAILABLE - AUDIO DETECTED]"
            confidence = 0.3
        
        return TranscriptionSegment(
            text=text,
            confidence=confidence,
            start_time=0.0,
            end_time=metrics.duration,
            timestamp=datetime.utcnow().isoformat(),
            is_final=True
        )
    
    async def transcribe_audio_chunk(self, audio_data: np.ndarray, sample_rate: int = 16000) -> TranscriptionSegment:
        """Transcribe audio chunk using best available method"""
        # Try multiple engines in order of preference
        segment = None
        
        # 1. Try Google Speech Recognition (best accuracy when available)
        segment = self.transcribe_with_google(audio_data, sample_rate)
        if segment and segment.confidence > 0.6:
            logger.info(f"✅ Google transcription: {segment.text[:50]}...")
            return segment
        
        # 2. Try Vosk (offline but good accuracy)
        segment = self.transcribe_with_vosk(audio_data, sample_rate)
        if segment and segment.confidence > 0.5:
            logger.info(f"✅ Vosk transcription: {segment.text[:50]}...")
            return segment
        
        # 3. Fallback
        logger.warning("⚠️ Using fallback transcription")
        return self.fallback_transcribe(audio_data)
    
    async def process_audio_stream(self, audio_stream):
        """Process continuous audio stream"""
        self.is_running = True
        buffer = np.array([])
        chunk_duration = 3.0  # Process every 3 seconds
        sample_rate = 16000
        chunk_size = int(chunk_duration * sample_rate)
        
        logger.info("🎤 Starting real-time audio processing")
        
        try:
            async for audio_chunk in audio_stream:
                if not self.is_running:
                    break
                
                # Convert to numpy array if needed
                if isinstance(audio_chunk, bytes):
                    audio_chunk = np.frombuffer(audio_chunk, dtype=np.float32)
                
                buffer = np.append(buffer, audio_chunk)
                
                # Process when we have enough audio
                if len(buffer) >= chunk_size:
                    # Take chunk for processing
                    chunk_to_process = buffer[:chunk_size]
                    buffer = buffer[chunk_size//2:]  # Keep 50% overlap
                    
                    # Transcribe the chunk
                    segment = await self.transcribe_audio_chunk(chunk_to_process, sample_rate)
                    
                    if segment and segment.text.strip() and not segment.text.startswith('['):
                        self.segments.append(segment)
                        await self.notify_callbacks(segment)
                        
        except Exception as e:
            logger.error(f"Audio stream processing error: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Audio processing stopped")
    
    def stop(self):
        """Stop the transcriber"""
        self.is_running = False
    
    def get_full_transcript(self) -> str:
        """Get complete transcript from all segments"""
        return " ".join([seg.text for seg in self.segments if seg.text and not seg.text.startswith('[')])
    
    def get_segments_json(self) -> List[Dict]:
        """Get all segments as JSON-serializable data"""
        return [asdict(segment) for segment in self.segments]
    
    def clear_segments(self):
        """Clear all transcription segments"""
        self.segments.clear()
        self.current_segment = ""

# Enhanced offline transcription function with better accuracy
def enhanced_offline_transcribe(wav_path, vosk_model_path: Optional[str] = None) -> str:
    """Enhanced offline transcription with multiple fallback options"""
    try:
        # Load audio file
        if HAS_VOSK:
            try:
                import soundfile as sf
                audio_data, sample_rate = sf.read(wav_path)
                # Ensure 16kHz mono
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                if sample_rate != 16000:
                    from scipy import signal
                    audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / sample_rate))
                    sample_rate = 16000
            except ImportError:
                # Fallback to basic loading
                with wave.open(str(wav_path), 'rb') as wav_file:
                    frames = wav_file.readframes(-1)
                    audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    sample_rate = wav_file.getframerate()
        else:
            # Use speech_recognition if available
            if HAS_SPEECH_RECOGNITION:
                recognizer = sr.Recognizer()
                with sr.AudioFile(str(wav_path)) as source:
                    audio = recognizer.record(source)
                try:
                    return recognizer.recognize_google(audio)
                except:
                    pass
            
            return "[ENHANCED OFFLINE TRANSCRIPTION UNAVAILABLE]"
        
        # Use enhanced transcriber
        transcriber = EnhancedRealTimeTranscriber(vosk_model_path)
        
        # Create a simple async context for transcription
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            segment = loop.run_until_complete(transcriber.transcribe_audio_chunk(audio_data, sample_rate))
            return segment.text if segment else "[TRANSCRIPTION FAILED]"
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Enhanced offline transcription error: {e}")
        return f"[TRANSCRIPTION ERROR: {str(e)}]"
