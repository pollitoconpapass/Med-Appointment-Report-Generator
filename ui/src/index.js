import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import "./App.css";
import { API_URL, WS_URL } from "./constants";
import { StartScreen } from "./screens/StartScreen";
import { RecordingScreen } from "./screens/RecordingScreen";
import { TranscriptScreen } from "./screens/TranscriptScreen";
import { ReportScreen } from "./screens/ReportScreen";

// Suppress the ResizeObserver loop error which is a common, harmless issue in some editors
window.addEventListener("error", (e) => {
  if (
    e.message ===
    "ResizeObserver loop completed with undelivered notifications."
  ) {
    const resizeObserverErrDiv = document.getElementById(
      "webpack-dev-server-client-overlay-div",
    );
    const resizeObserverErr = document.getElementById(
      "webpack-dev-server-client-overlay",
    );
    if (resizeObserverErrDiv) {
      resizeObserverErrDiv.setAttribute("style", "display: none");
    }
    if (resizeObserverErr) {
      resizeObserverErr.setAttribute("style", "display: none");
    }
    // Prevent the error from showing up in the console
    e.stopImmediatePropagation();
  }
});

function App() {
  const [screen, setScreen] = useState("start");
  const [sessionId, setSessionId] = useState(null);
  const [language, setLanguage] = useState("en");
  const [transcript, setTranscript] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportText, setReportText] = useState("");

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);

  const reportRef = useRef("");

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
            {
              text: data.text,
              timestamp: data.timestamp,
              speaker: data.speaker,
            },
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

  const handleGenerateReport = async (finalTranscriptContent) => {
    setScreen("report");
    setIsGeneratingReport(true);
    setReportText("");
    reportRef.current = "";

    try {
      const response = await fetch(`${API_URL}/report/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: finalTranscriptContent }),
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
                setReportText(reportContent);
              }
            } catch (e) {
              console.error("Failed to parse JSON:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
    }

    setIsGeneratingReport(false);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>MARGe - Medical Appointment Report Generator</h1>
      </header>

      <main className="app-main">
        {screen === "start" && (
          <StartScreen
            language={language}
            setLanguage={setLanguage}
            onStart={startAppointment}
          />
        )}

        {screen === "recording" && (
          <RecordingScreen
            isRecording={isRecording}
            audioLevel={audioLevel}
            transcript={transcript}
            onEnd={endAppointment}
          />
        )}

        {screen === "transcript" && (
          <TranscriptScreen
            transcript={transcript}
            onGenerate={handleGenerateReport}
          />
        )}

        {screen === "report" && (
          <ReportScreen
            reportText={reportText}
            isGeneratingReport={isGeneratingReport}
            onChange={setReportText}
          />
        )}
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
