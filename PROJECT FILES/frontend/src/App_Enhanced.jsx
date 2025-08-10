import React, { useEffect, useRef, useState } from 'react';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function beep(duration=120, freq=700) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine"; 
    o.frequency.value = freq;
    g.gain.value = 0.06;
    o.connect(g); 
    g.connect(ctx.destination); 
    o.start();
    setTimeout(() => { o.stop(); ctx.close(); }, duration);
  } catch (e) {}
}

export default function App() {
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [reports, setReports] = useState([]);
  const [selected, setSelected] = useState(null);
  const [textAnalysis, setTextAnalysis] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, scam: 0, suspicious: 0, safe: 0 });
  const wsRef = useRef(null);

  // Load existing reports on mount
  useEffect(() => {
    loadReports();
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    wsRef.current = new WebSocket((API_BASE.startsWith('https')?'wss':'ws')+'://'+(new URL(API_BASE).host)+'/ws');
    wsRef.current.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'alert' && msg.report) {
          setReports(r => [msg.report, ...r]);
          updateStats([msg.report, ...reports]);
        }
      } catch (e) {}
    };
    return () => { try { wsRef.current.close(); } catch {} }
  }, [reports]);

  const loadReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/reports`);
      if (res.ok) {
        const data = await res.json();
        setReports(data.reports || []);
        updateStats(data.reports || []);
      }
    } catch (e) {
      console.error('Failed to load reports:', e);
    }
  };

  const updateStats = (reportList) => {
    const total = reportList.length;
    const scam = reportList.filter(r => r.label === 'Scam').length;
    const suspicious = reportList.filter(r => r.label === 'Suspicious').length;
    const safe = reportList.filter(r => r.label === 'Safe').length;
    setStats({ total, scam, suspicious, safe });
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks = [];

      mr.ondataavailable = e => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mr.onstop = async () => {
        setLoading(true);
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const arrayBuffer = await blob.arrayBuffer();
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

        // Convert PCM to WAV
        const wavBuffer = encodeWAV(audioBuffer);
        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });

        const fd = new FormData();
        fd.append('file', wavBlob, `recording_${Date.now()}.wav`);

        try {
          const res = await fetch(`${API_BASE}/upload-audio`, { method: 'POST', body: fd });
          const data = await res.json();
          if (res.ok) {
            setReports(r => [data, ...r]);
            setSelected(data.id);
            updateStats([data, ...reports]);
            
            // Alert sound based on detection
            if (data.scam_detection?.label === 'Scam') {
              beep(200, 1000); // High pitch for scam
              setTimeout(() => beep(200, 1000), 300);
            } else if (data.scam_detection?.label === 'Suspicious') {
              beep(150, 600); // Medium pitch for suspicious
            } else {
              beep(100, 400); // Low pitch for safe
            }
          } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
          }
        } catch (err) {
          alert('Network error: ' + err.message);
        } finally {
          setLoading(false);
        }
      };

      mr.start();
      setMediaRecorder(mr);
      setRecording(true);
      beep(90, 800);
    } catch (e) {
      alert('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setRecording(false);
      beep(80, 600);
    }
  };

  const analyzeText = async () => {
    if (!textAnalysis.trim()) return;
    
    setAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/analyze-transcript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: textAnalysis })
      });
      
      if (res.ok) {
        const data = await res.json();
        const mockReport = {
          id: 'text-' + Date.now(),
          created_at: data.timestamp,
          transcript: data.transcript,
          scam_detection: data.analysis,
          analysis_version: 'text_analysis'
        };
        setReports(r => [mockReport, ...r]);
        setSelected(mockReport.id);
        updateStats([mockReport, ...reports]);
        setTextAnalysis('');
      } else {
        const error = await res.json();
        alert('Analysis failed: ' + (error.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Network error: ' + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  // WAV encoder functions
  function encodeWAV(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0);
    const buffer = new ArrayBuffer(44 + channelData.length * 2);
    const view = new DataView(buffer);

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + channelData.length * 2, true);
    writeString(view, 8, 'WAVE');

    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, audioBuffer.sampleRate, true);
    view.setUint32(28, audioBuffer.sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);

    writeString(view, 36, 'data');
    view.setUint32(40, channelData.length * 2, true);

    floatTo16BitPCM(view, 44, channelData);
    return buffer;
  }

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  function floatTo16BitPCM(view, offset, input) {
    let pos = offset;
    for (let i = 0; i < input.length; i++, pos += 2) {
      let s = Math.max(-1, Math.min(1, input[i]));
      view.setInt16(pos, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
  }

  const formatTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getRiskLevel = (report) => {
    const label = report.scam_detection?.label || report.analysis?.label || 'Unknown';
    const confidence = report.scam_detection?.confidence || report.analysis?.confidence || 0;
    
    if (label === 'Scam' && confidence > 0.7) return 'HIGH RISK';
    if (label === 'Scam') return 'MEDIUM-HIGH RISK';
    if (label === 'Suspicious') return 'MEDIUM RISK';
    if (label === 'Safe') return 'LOW RISK';
    return 'UNKNOWN RISK';
  };

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <div>
          <div className="title">🛡️ Voice Scam Shield</div>
          <div className="subtitle">Advanced Fraud Detection System</div>
        </div>
        <div className="header-actions">
          {loading && <div className="status loading">Analyzing...</div>}
          {!recording && !loading && (
            <button className="btn primary" onClick={startRecording}>
              🎤 Record Audio
            </button>
          )}
          {recording && (
            <button className="btn danger" onClick={stopRecording}>
              ⏹️ Stop & Analyze
            </button>
          )}
        </div>
      </div>

      {/* Stats Dashboard */}
      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-number">{stats.total}</div>
          <div className="stat-label">Total Analyzed</div>
        </div>
        <div className="stat-card scam">
          <div className="stat-number">{stats.scam}</div>
          <div className="stat-label">Scam Detected</div>
        </div>
        <div className="stat-card suspicious">
          <div className="stat-number">{stats.suspicious}</div>
          <div className="stat-label">Suspicious</div>
        </div>
        <div className="stat-card safe">
          <div className="stat-number">{stats.safe}</div>
          <div className="stat-label">Safe</div>
        </div>
      </div>

      {/* Text Analysis */}
      <div className="card">
        <h3>📝 Text Analysis</h3>
        <div className="text-analyzer">
          <textarea
            value={textAnalysis}
            onChange={(e) => setTextAnalysis(e.target.value)}
            placeholder="Enter or paste text to analyze for fraud indicators..."
            className="text-input"
          />
          <button 
            className="btn secondary" 
            onClick={analyzeText} 
            disabled={!textAnalysis.trim() || analyzing}
          >
            {analyzing ? '⏳ Analyzing...' : '🔍 Analyze Text'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-grid">
        {/* Reports List */}
        <div className="reports-section">
          <h3>📊 Analysis Reports</h3>
          <div className="reports">
            {reports.length === 0 && (
              <div className="empty-state">
                <div>🎯 No reports yet</div>
                <div className="small">Record audio or analyze text to get started</div>
              </div>
            )}
            {reports.map(r => (
              <div 
                key={r.id} 
                className={`report ${selected === r.id ? 'selected' : ''}`} 
                onClick={() => setSelected(r.id)}
              >
                <div className="report-header">
                  <div className="report-title">
                    {r.scam_detection?.label || r.analysis?.label || r.label || 'Unknown'}
                  </div>
                  <div className={`badge ${(r.scam_detection?.label || r.analysis?.label || r.label || '').toLowerCase()}`}>
                    {getRiskLevel(r)}
                  </div>
                </div>
                <div className="report-meta">
                  <span className="small">{formatTime(r.created_at)}</span>
                  {r.analysis_version === 'text_analysis' && <span className="text-badge">TEXT</span>}
                </div>
                <div className="report-preview">
                  {(r.transcript || '').slice(0, 100)}
                  {(r.transcript || '').length > 100 && '...'}
                </div>
                {(r.scam_detection?.confidence || r.analysis?.confidence) && (
                  <div className="confidence-bar">
                    <div 
                      className="confidence-fill"
                      style={{ width: `${((r.scam_detection?.confidence || r.analysis?.confidence || 0) * 100)}%` }}
                    />
                    <span className="confidence-text">
                      {Math.round((r.scam_detection?.confidence || r.analysis?.confidence || 0) * 100)}% confidence
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Detail View */}
        <div className="detail-section">
          <h3>🔍 Analysis Details</h3>
          <div className="detail">
            {!selected && (
              <div className="empty-state">
                <div>👈 Select a report to view details</div>
                <div className="small">Click on any report from the list to see full analysis</div>
              </div>
            )}
            {selected && (() => {
              const r = reports.find(x => x.id === selected);
              if (!r) return <div className="small">Report not found</div>;
              
              const detection = r.scam_detection || r.analysis || {};
              
              return (
                <div className="report-detail">
                  <div className="detail-header">
                    <h4>{detection.label || 'Unknown'}</h4>
                    <div className={`badge large ${(detection.label || '').toLowerCase()}`}>
                      {getRiskLevel(r)}
                    </div>
                  </div>

                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Confidence Score</label>
                      <div className="value">{Math.round((detection.confidence || 0) * 100)}%</div>
                    </div>
                    
                    {detection.fraud_score && (
                      <div className="detail-item">
                        <label>Fraud Score</label>
                        <div className="value">{detection.fraud_score}</div>
                      </div>
                    )}
                    
                    <div className="detail-item">
                      <label>Analysis Time</label>
                      <div className="value small">{formatTime(r.created_at)}</div>
                    </div>
                  </div>

                  <div className="transcript-section">
                    <label>📝 Transcript</label>
                    <div className="transcript">{r.transcript || 'No transcript available'}</div>
                  </div>

                  {detection.rationale && (
                    <div className="detail-section">
                      <label>🤔 Analysis Reasoning</label>
                      <div className="value">{detection.rationale}</div>
                    </div>
                  )}

                  {detection.keywords && detection.keywords.length > 0 && (
                    <div className="detail-section">
                      <label>🚩 Fraud Keywords Found</label>
                      <div className="keywords">
                        {detection.keywords.map((kw, i) => (
                          <span key={i} className="keyword-tag">{kw}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {detection.pattern_matches && detection.pattern_matches.length > 0 && (
                    <div className="detail-section">
                      <label>🎯 Suspicious Patterns</label>
                      <div className="patterns">
                        {detection.pattern_matches.map((pattern, i) => (
                          <div key={i} className="pattern-item">{pattern}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {r.audio_file && (
                    <div className="actions">
                      <a href={`${API_BASE}/audio/${r.audio_file}`} target="_blank" className="btn secondary">
                        🎧 Play Audio
                      </a>
                      <a href={`${API_BASE}/reports/${r.id}`} target="_blank" className="btn secondary">
                        📋 View JSON
                      </a>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}
