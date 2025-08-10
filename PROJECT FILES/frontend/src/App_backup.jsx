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
  const [audioChunks, setAudioChunks] = useState([]);
  const [reports, setReports] = useState([]);
  const [selected, setSelected] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    wsRef.current = new WebSocket((API_BASE.startsWith('https')?'wss':'ws')+'://'+(new URL(API_BASE).host)+'/ws');
    wsRef.current.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'alert' && msg.report) {
          setReports(r => [msg.report, ...r]);
        }
      } catch (e) {}
    };
    return () => { try { wsRef.current.close(); } catch {} }
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' }); // Will capture PCM and convert later
      const chunks = [];

      mr.ondataavailable = e => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mr.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const arrayBuffer = await blob.arrayBuffer();
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

        // Convert PCM to WAV
        const wavBuffer = encodeWAV(audioBuffer);
        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });

        const fd = new FormData();
        fd.append('file', wavBlob, `recording_${Date.now()}.wav`);

        const res = await fetch(`${API_BASE}/upload-audio`, { method: 'POST', body: fd });
        const data = await res.json();
        if (res.ok) {
          setReports(r => [data, ...r]);
          setSelected(data.id);
        } else {
          alert('Upload failed');
        }
      };

      mr.start();
      setMediaRecorder(mr);
      setAudioChunks([]);
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
      beep(80, 400);
    }
  };

  // WAV encoder
  function encodeWAV(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0); // mono
    const buffer = new ArrayBuffer(44 + channelData.length * 2);
    const view = new DataView(buffer);

    // RIFF header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + channelData.length * 2, true);
    writeString(view, 8, 'WAVE');

    // fmt chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, audioBuffer.sampleRate, true);
    view.setUint32(28, audioBuffer.sampleRate * 2, true);
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // bits per sample

    // data chunk
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

  return (
    <div className="app">
      <div className="header">
        <div>
          <div className="title">Voice Scam Shield</div>
          <div className="small">Local demo • OpenAI backend</div>
        </div>
        <div>
          {!recording
            ? <button className="btn" onClick={startRecording}>Start</button>
            : <button className="btn" onClick={stopRecording}>Stop & Analyze</button>}
        </div>
      </div>

      <div className="card list">
        <div className="reports">
          <h3 className="small">Recent Reports</h3>
          {reports.length === 0 && <div className="small">No reports yet</div>}
          {reports.map(r => (
            <div key={r.id} className="report" onClick={() => setSelected(r.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 700 }}>{r.scam_detection?.label || 'Unknown'}</div>
                <div className={'badge ' + ((r.scam_detection?.label || '').toLowerCase())}>{r.scam_detection?.label || ''}</div>
              </div>
              <div className="small">{r.created_at}</div>
              <div className="small">{r.scam_detection?.rationale?.slice(0, 80)}</div>
            </div>
          ))}
        </div>

        <div className="detail">
          {!selected && <div className="small">Select a report to view details</div>}
          {selected && (() => {
            const r = reports.find(x => x.id === selected);
            if (!r) return <div />;
            return (
              <div>
                <h3>{r.id}</h3>
                <div className="small">Label: <strong>{r.scam_detection.label}</strong> | Confidence: {Math.round(r.scam_detection.confidence * 100)}%</div>
                <div style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>{r.transcript}</div>
                <div style={{ marginTop: 10 }}>
                  <a href={`${API_BASE}/audio/${r.audio_file}`} target="_blank">Play audio</a> • <a href={`${API_BASE}/reports/${r.id}`} target="_blank">Open JSON</a>
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
