import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://localhost:8000";

function App() {
  const [screen, setScreen] = useState("start");
  const [sessionId, setSessionId] = useState(null);
  const [language, setLanguage] = useState("en");
  const [transcript, setTranscript] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);

  const transcriptRef = useRef("");
  const reportRef = useRef("");
  const [reportText, setReportText] = useState("");

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (animationFrameRef.current)
        cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  const startAppointment = async () => {
    try {
      const response = await fetch(`${API_URL}/appointment/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language }),
      });
      const data = await response.json();
      setSessionId(data.session_id);
      setScreen("recording");
      await startRecording(data.session_id);
    } catch (error) {
      console.error("Failed to start appointment:", error);
    }
  };

  const startRecording = async (sessionId) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      let mimeType = "audio/webm";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/webm;codecs=opus";
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = "audio/mp4";
          if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = "";
          }
        }
      }
      console.log("Using mimeType:", mimeType);

      const options = mimeType ? { mimeType } : {};

      mediaRecorderRef.current = new MediaRecorder(stream, options);

      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (
          event.data.size > 0 &&
          wsRef.current?.readyState === WebSocket.OPEN
        ) {
          wsRef.current.send(event.data);
        }
      };

      wsRef.current = new WebSocket(`${WS_URL}/ws/audio/${sessionId}`);

      wsRef.current.onopen = () => {
        setIsRecording(true);
        mediaRecorderRef.current.start(1000);
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "transcript") {
          setTranscript((prev) => [
            ...prev,
            { text: data.text, timestamp: data.timestamp },
          ]);
        } else if (data.type === "ack") {
          updateAudioVisualization();
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      wsRef.current.onclose = () => {
        setIsRecording(false);
      };
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  };

  const updateAudioVisualization = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    setAudioLevel(average / 255);

    animationFrameRef.current = requestAnimationFrame(updateAudioVisualization);
  };

  const endAppointment = async () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    setIsRecording(false);

    try {
      const response = await fetch(`${API_URL}/appointment/end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await response.json();
      setTranscript(data.transcript);
      setScreen("transcript");
    } catch (error) {
      console.error("Failed to end appointment:", error);
    }
  };

  const saveTranscriptAndGenerateReport = async () => {
    const editedTranscript = transcript.map((item, index) => ({
      ...item,
      text: transcriptRef.current[index] || item.text,
    }));

    setTranscript(editedTranscript);
    setScreen("report");
    setIsGeneratingReport(true);

    try {
      const response = await fetch(`${API_URL}/report/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: editedTranscript }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let reportContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                reportContent += data.content;
                reportRef.current = reportContent;
              }
            } catch (e) {}
          }
        }
      }

      if (reportRef.current) {
        setReportText(reportRef.current);
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
    }

    setIsGeneratingReport(false);
  };

  const getTranscriptText = () => {
    return transcript.map((item) => item.text).join("\n\n");
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>MARGe - Medical Appointment Report Generator</h1>
      </header>

      <main className="app-main">
        {screen === "start" && (
          <div className="start-screen">
            <div className="language-selector">
              <label>Language:</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
              </select>
            </div>
            <button className="start-button" onClick={startAppointment}>
              Start Recording
            </button>
          </div>
        )}

        {screen === "recording" && (
          <div className="recording-screen">
            <div className="audio-visualizer">
              <div className="visualizer-bars">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className="bar"
                    style={{
                      height: `${Math.max(10, audioLevel * 100 * Math.random())}%`,
                      animationDelay: `${i * 0.05}s`,
                    }}
                  />
                ))}
              </div>
              <p className="listening-text">
                {isRecording ? "Listening..." : "Starting..."}
              </p>
              <p className="transcript-preview">
                {transcript
                  .map((t) => t.text)
                  .join(" ")
                  .slice(-100)}
              </p>
            </div>

            <button className="end-button" onClick={endAppointment}>
              <span className="hangup-icon">📞</span>
              End Appointment
            </button>
          </div>
        )}

        {screen === "transcript" && (
          <div className="transcript-screen">
            <h2>Edit Transcript</h2>
            <p className="hint">
              Review and edit the transcript before generating the report
            </p>
            <div className="editor-container">
              <textarea
                className="editor-textarea"
                defaultValue={getTranscriptText()}
                onChange={(e) => {
                  transcriptRef.current = e.target.value
                    .split("\n\n")
                    .filter((t) => t.trim());
                }}
                rows={15}
              />
            </div>
            <div className="action-buttons">
              <button
                className="generate-button"
                onClick={saveTranscriptAndGenerateReport}
              >
                Generate Report →
              </button>
            </div>
          </div>
        )}

        {screen === "report" && (
          <div className="report-screen">
            <h2>Medical Report</h2>
            <p className="hint">
              {isGeneratingReport
                ? "Generating report..."
                : "Review and edit the medical report"}
            </p>
            <div className="editor-container">
              <textarea
                className="editor-textarea"
                value={reportText}
                onChange={(e) => {
                  reportRef.current = e.target.value;
                  setReportText(e.target.value);
                }}
                rows={20}
              />
            </div>
            <div className="action-buttons">
              <button
                className="save-button"
                onClick={() => {
                  const content = reportRef.current;
                  console.log("Saving report:", content);
                  alert("Report saved!");
                }}
              >
                Save Report
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
