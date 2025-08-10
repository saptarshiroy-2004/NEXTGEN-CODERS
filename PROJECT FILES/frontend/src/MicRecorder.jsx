import { useState, useRef } from "react";

export default function MicRecorder() {
  const [recording, setRecording] = useState(false);
  const [result, setResult] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("file", blob, "mic_recording.webm");

      const res = await fetch("http://127.0.0.1:8000/upload-audio", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResult(data);
    };

    mediaRecorderRef.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
  };

  return (
    <div style={{ marginTop: "20px" }}>
      <button
        onClick={recording ? stopRecording : startRecording}
        style={{
          backgroundColor: "#0ea5e9",
          color: "white",
          padding: "10px 20px",
          borderRadius: "8px",
          border: "none",
          cursor: "pointer"
        }}
      >
        {recording ? "Stop" : "Start"} Mic Recording
      </button>

      {result && (
        <div style={{ marginTop: "15px", background: "#111", padding: "10px", borderRadius: "6px" }}>
          <p><b>Label:</b> {result.scam_detection?.label}</p>
          <p><b>Confidence:</b> {result.scam_detection?.confidence}</p>
          <p><b>Transcript:</b> {result.transcript}</p>
        </div>
      )}
    </div>
  );
}
