"""
Enhanced Real-Time Fraud Monitoring System
Provides live audio transcription with immediate fraud detection and warnings
"""

import asyncio
import json
import uuid
import time
import base64
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import numpy as np
import logging

# Import existing components
try:
    from real_time_transcriber import RealTimeTranscriber, TranscriptionSegment
    from enhanced_fraud_classifier import get_global_classifier, FraudAnalysisResult
    from mic_audio_processor import get_global_mic_processor
except ImportError as e:
    print(f"⚠️ Import warning: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FraudAlert:
    """Represents a fraud alert generated during live monitoring"""
    alert_id: str
    session_id: str
    timestamp: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    alert_type: str  # "SCAM_KEYWORDS", "URGENCY_PATTERN", "FINANCIAL_REQUEST", etc.
    confidence: float
    risk_score: float
    message: str
    transcript_segment: str
    indicators: List[str]
    recommended_action: str

@dataclass 
class LiveSession:
    """Represents a live monitoring session"""
    session_id: str
    start_time: str
    accumulated_transcript: str = ""
    alerts: List[FraudAlert] = None
    risk_level: str = "LOW"
    total_risk_score: float = 0.0
    is_active: bool = True
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []

class RealTimeFraudMonitor:
    """Enhanced real-time fraud monitoring system"""
    
    def __init__(self, alert_threshold: float = 0.3):
        self.sessions: Dict[str, LiveSession] = {}
        self.alert_threshold = alert_threshold
        self.fraud_keywords = [
            "urgent", "immediate", "limited time", "act now", "verify account",
            "suspended", "blocked", "security breach", "unauthorized", "confirm identity",
            "send money", "wire transfer", "gift card", "cryptocurrency", "bitcoin",
            "social security", "bank account", "credit card", "password", "PIN",
            "IRS", "government agency", "arrest warrant", "legal action", "refund",
            "prize", "lottery", "winner", "congratulations", "inheritance"
        ]
        
        self.urgency_patterns = [
            r"within.*(?:hours?|minutes?|days?)",
            r"(?:expires?|expire).*(?:today|tonight|soon)",
            r"(?:must|need).*(?:immediately|right now|asap)",
            r"(?:final|last).*(?:notice|warning|chance)"
        ]
        
    async def start_session(self, websocket) -> str:
        """Start a new live monitoring session"""
        session_id = uuid.uuid4().hex
        session = LiveSession(
            session_id=session_id,
            start_time=datetime.utcnow().isoformat()
        )
        self.sessions[session_id] = session
        
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "message": "🎤 Live fraud monitoring started",
            "timestamp": session.start_time
        })
        
        return session_id
    
    async def process_transcript_segment(self, session_id: str, segment, websocket) -> None:
        """Process a new transcript segment and check for fraud indicators"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        if not session.is_active:
            return
        
        # Handle different segment formats
        text = ""
        if hasattr(segment, 'text'):
            text = segment.text
        elif isinstance(segment, dict) and 'text' in segment:
            text = segment['text']
        elif isinstance(segment, str):
            text = segment
        else:
            return  # Can't process this segment
            
        # Add to accumulated transcript
        session.accumulated_transcript += " " + text
        
        # Analyze the current segment for immediate threats
        await self._analyze_segment_immediate(session_id, segment, websocket)
        
        # Analyze full conversation context every few segments
        await self._analyze_full_context(session_id, websocket)
        
    async def _analyze_segment_immediate(self, session_id: str, segment, websocket):
        """Immediate analysis of transcript segment for urgent threats"""
        session = self.sessions[session_id]
        
        # Handle different segment formats
        text = ""
        if hasattr(segment, 'text'):
            text = segment.text
        elif isinstance(segment, dict) and 'text' in segment:
            text = segment['text']
        elif isinstance(segment, str):
            text = segment
        else:
            return  # Can't process this segment
            
        text_lower = text.lower()
        
        # Check for critical fraud keywords
        detected_keywords = [keyword for keyword in self.fraud_keywords if keyword in text_lower]
        
        if detected_keywords:
            severity = self._calculate_severity(detected_keywords, text)
            
            if severity in ["HIGH", "CRITICAL"]:
                alert = FraudAlert(
                    alert_id=uuid.uuid4().hex,
                    session_id=session_id,
                    timestamp=datetime.utcnow().isoformat(),
                    severity=severity,
                    alert_type="SCAM_KEYWORDS",
                    confidence=0.8,
                    risk_score=0.7 if severity == "HIGH" else 0.9,
                    message=f"⚠️ {severity} RISK: Fraud keywords detected",
                    transcript_segment=text,
                    indicators=detected_keywords,
                    recommended_action="IMMEDIATE ATTENTION REQUIRED - Possible scam call"
                )
                
                session.alerts.append(alert)
                await self._send_alert(alert, websocket)
    
    async def _analyze_full_context(self, session_id: str, websocket):
        """Analyze full conversation context using enhanced classifier"""
        session = self.sessions[session_id]
        
        if len(session.accumulated_transcript.strip()) < 50:  # Wait for enough context
            return
            
        try:
            # Use enhanced classifier for full analysis
            classifier = get_global_classifier()
            result = classifier.classify(session.accumulated_transcript.strip())
            
            # Update session risk level
            previous_risk = session.total_risk_score
            session.total_risk_score = result.risk_score
            session.risk_level = self._determine_risk_level(result.risk_score)
            
            # Send detailed context analysis update
            await websocket.send_json({
                "type": "context_analysis",
                "session_id": session_id,
                "risk_level": session.risk_level,
                "risk_score": result.risk_score,
                "confidence": result.confidence,
                "label": result.label,
                "key_indicators": result.fraud_indicators[:5],
                "recommendation": result.recommendation,
                "transcript_length": len(session.accumulated_transcript.split()),
                "linguistic_features": result.linguistic_features,
                "pattern_matches": result.pattern_matches,
                "detailed_analysis": getattr(result, 'detailed_analysis', {}),
                "rationale": result.rationale,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Generate alert if risk significantly increased
            if result.risk_score > self.alert_threshold and result.risk_score > previous_risk + 0.2:
                alert = FraudAlert(
                    alert_id=uuid.uuid4().hex,
                    session_id=session_id,
                    timestamp=datetime.utcnow().isoformat(),
                    severity=self._determine_risk_level(result.risk_score),
                    alert_type="CONTEXT_ANALYSIS",
                    confidence=result.confidence,
                    risk_score=result.risk_score,
                    message=f"🚨 Risk escalation detected: {result.label}",
                    transcript_segment=session.accumulated_transcript[-200:],  # Last 200 chars
                    indicators=result.fraud_indicators[:3],
                    recommended_action=result.recommendation
                )
                
                session.alerts.append(alert)
                await self._send_alert(alert, websocket)
                
        except Exception as e:
            logger.error(f"Context analysis error: {e}")
    
    async def _send_alert(self, alert: FraudAlert, websocket):
        """Send fraud alert through websocket"""
        alert_data = {
            "type": "fraud_alert",
            "alert": asdict(alert),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add visual/audio cues based on severity
        if alert.severity == "CRITICAL":
            alert_data["ui_action"] = "FLASH_RED"
            alert_data["sound"] = "URGENT_BEEP"
        elif alert.severity == "HIGH":
            alert_data["ui_action"] = "HIGHLIGHT_ORANGE"
            alert_data["sound"] = "WARNING_BEEP"
        
        await websocket.send_json(alert_data)
        logger.warning(f"FRAUD ALERT: {alert.severity} - {alert.message}")
    
    def _calculate_severity(self, keywords: List[str], text: str) -> str:
        """Calculate alert severity based on detected keywords and context"""
        high_risk_keywords = ["send money", "wire transfer", "gift card", "bitcoin", "social security", "arrest warrant"]
        critical_keywords = ["suspended", "blocked", "verify account", "confirm identity", "IRS"]
        
        if any(keyword in keywords for keyword in critical_keywords):
            return "CRITICAL"
        elif any(keyword in keywords for keyword in high_risk_keywords):
            return "HIGH"
        elif len(keywords) >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from numeric risk score"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def end_session(self, session_id: str, websocket) -> Dict:
        """End monitoring session and generate final report"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
            
        session = self.sessions[session_id]
        session.is_active = False
        
        # Generate comprehensive final report
        final_report = {
            "session_id": session_id,
            "duration": self._calculate_duration(session.start_time),
            "final_transcript": session.accumulated_transcript.strip(),
            "total_alerts": len(session.alerts),
            "final_risk_level": session.risk_level,
            "final_risk_score": session.total_risk_score,
            "alerts_by_severity": self._group_alerts_by_severity(session.alerts),
            "key_fraud_indicators": self._extract_key_indicators(session.alerts),
            "recommendations": self._generate_final_recommendations(session),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_json({
            "type": "session_ended",
            "final_report": final_report,
            "message": "📊 Monitoring session completed"
        })
        
        # Clean up session
        del self.sessions[session_id]
        
        return final_report
    
    def _calculate_duration(self, start_time: str) -> str:
        """Calculate session duration"""
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        duration = datetime.utcnow() - start.replace(tzinfo=None)
        return str(duration).split('.')[0]  # Remove microseconds
    
    def _group_alerts_by_severity(self, alerts: List[FraudAlert]) -> Dict:
        """Group alerts by severity level"""
        groups = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for alert in alerts:
            groups[alert.severity] += 1
        return groups
    
    def _extract_key_indicators(self, alerts: List[FraudAlert]) -> List[str]:
        """Extract most common fraud indicators from alerts"""
        all_indicators = []
        for alert in alerts:
            all_indicators.extend(alert.indicators)
        
        # Count frequency and return top indicators
        from collections import Counter
        counter = Counter(all_indicators)
        return [indicator for indicator, _ in counter.most_common(10)]
    
    def _generate_final_recommendations(self, session: LiveSession) -> List[str]:
        """Generate final recommendations based on session analysis"""
        recommendations = []
        
        if session.total_risk_score >= 0.8:
            recommendations.append("🚨 HIGH FRAUD RISK: Immediately hang up and report this call")
            recommendations.append("Do not provide any personal or financial information")
            recommendations.append("Contact the organization directly using official phone numbers")
        elif session.total_risk_score >= 0.6:
            recommendations.append("⚠️ SUSPICIOUS CALL: Exercise extreme caution")
            recommendations.append("Verify caller identity through official channels")
            recommendations.append("Do not make immediate decisions or payments")
        elif session.total_risk_score >= 0.4:
            recommendations.append("🔍 POTENTIAL RISK: Stay vigilant during this call")
            recommendations.append("Be cautious about sharing personal information")
        else:
            recommendations.append("✅ LOW RISK: Call appears legitimate but remain cautious")
            
        return recommendations

# Enhanced WebSocket endpoint for live fraud monitoring
async def enhanced_live_monitoring_endpoint(websocket, fraud_monitor: RealTimeFraudMonitor):
    """Enhanced WebSocket endpoint for comprehensive fraud monitoring"""
    await websocket.accept()
    
    session_id = None
    transcriber = None
    
    try:
        # Start monitoring session
        session_id = await fraud_monitor.start_session(websocket)
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "start_transcription":
                # Initialize transcriber with fraud monitoring callback
                async def transcription_callback(segment):
                    # Process transcript segment for fraud analysis
                    await fraud_monitor.process_transcript_segment(session_id, segment, websocket)
                    
                    # Send live transcription update
                    await websocket.send_json({
                        "type": "live_transcription",
                        "session_id": session_id,
                        "segment": {
                            "text": segment.text,
                            "confidence": segment.confidence,
                            "timestamp": segment.timestamp
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                try:
                    transcriber = RealTimeTranscriber()
                    transcriber.add_callback(transcription_callback)
                    
                    await websocket.send_json({
                        "type": "transcription_started",
                        "session_id": session_id,
                        "message": "🎤 Live transcription and fraud monitoring active"
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to start transcription: {str(e)}"
                    })
            
            elif data.get("type") == "audio_chunk":
                # Process real microphone audio chunk
                try:
                    base64_audio = data.get("data", "")
                    if base64_audio and session_id:
                        # Use microphone audio processor to transcribe
                        processor = get_global_mic_processor()
                        transcript_text = await processor.process_audio_chunk(base64_audio, session_id)
                        
                        if transcript_text and transcript_text.strip():
                            # Create a segment from the transcribed text
                            segment = {
                                "text": transcript_text,
                                "confidence": 0.8,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            # Process the transcribed segment for fraud analysis
                            await fraud_monitor.process_transcript_segment(session_id, segment, websocket)
                            
                            # Send live transcription update
                            await websocket.send_json({
                                "type": "live_transcription",
                                "session_id": session_id,
                                "segment": segment,
                                "accumulated_transcript": fraud_monitor.sessions[session_id].accumulated_transcript.strip() if session_id in fraud_monitor.sessions else "",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Audio processing error: {str(e)}"
                    })
            
            elif data.get("type") == "simulated_transcript":
                # Handle simulated transcript for testing
                if data.get("segment"):
                    segment = data["segment"]
                    
                    # Process the simulated segment for fraud analysis
                    await fraud_monitor.process_transcript_segment(session_id, segment, websocket)
                    
                    # Send live transcription update
                    await websocket.send_json({
                        "type": "live_transcription",
                        "session_id": session_id,
                        "segment": segment,
                        "accumulated_transcript": fraud_monitor.sessions[session_id].accumulated_transcript.strip() if session_id in fraud_monitor.sessions else "",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif data.get("type") == "stop":
                # End session and generate final report
                if session_id:
                    final_report = await fraud_monitor.end_session(session_id, websocket)
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if session_id:
            await fraud_monitor.end_session(session_id, websocket)
    
    finally:
        if transcriber:
            transcriber.stop()
