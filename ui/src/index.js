import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from "react-router-dom";
import "./index.css";
import "./App.css";
import { API_URL, WS_URL } from "./constants";
import { StartScreen } from "./screens/StartScreen";
import { RecordingScreen } from "./screens/RecordingScreen";
import { TranscriptScreen } from "./screens/TranscriptScreen";
import { ReportScreen } from "./screens/ReportScreen";

// Suppress the ResizeObserver loop error
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
    e.stopImmediatePropagation();
  }
});

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sessionId, setSessionId] = useState(null);
  const [language, setLanguage] = useState("en");
  const [transcript, setTranscript] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportText, setReportText] = useState("");

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);

  const reportRef = useRef("");
  const isPausedRef = useRef(false);

  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (animationFrameRef.current)
        cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  useEffect(() => {
    if (location.pathname === "/recording" && !sessionId && !isRecording) {
      navigate("/");
    }
  }, [location.pathname, sessionId, isRecording, navigate]);

  const startAppointment = async () => {
    setTranscript([]);
    setReportText("");
    reportRef.current = "";

    try {
      const response = await fetch(`${API_URL}/appointment/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language }),
      });
      const data = await response.json();
      setSessionId(data.session_id);
      navigate("/recording");
      await startRecording(data.session_id);
    } catch (error) {
      console.error("Failed to start appointment:", error);
    }
  };

  const handleViewReport = (report) => {
    setReportText(report.content);
    reportRef.current = report.content;
    navigate("/report", { state: { from: "start" } });
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
          wsRef.current?.readyState === WebSocket.OPEN &&
          !isPausedRef.current
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
    setIsEnding(true);
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
      navigate("/transcript");
    } catch (error) {
      console.error("Failed to end appointment:", error);
    } finally {
      setIsEnding(false);
    }
  };

  const handleGenerateReport = async (finalTranscriptContent) => {
    navigate("/report");
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
        <h1 onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
          MARGe - Medical Appointment Report Generator
        </h1>
      </header>

      <main className="app-main">
        <Routes>
          <Route
            path="/"
            element={
              <StartScreen
                language={language}
                setLanguage={setLanguage}
                onStart={startAppointment}
                onViewReport={handleViewReport}
              />
            }
          />
          <Route
            path="/recording"
            element={
              <RecordingScreen
                isRecording={isRecording}
                isEnding={isEnding}
                isPaused={isPaused}
                setIsPaused={setIsPaused}
                audioLevel={audioLevel}
                transcript={transcript}
                onEnd={endAppointment}
                onBack={() => {
                  // Stop any active recording/WS if we go back
                  if (wsRef.current) wsRef.current.close();
                  if (
                    mediaRecorderRef.current &&
                    mediaRecorderRef.current.state !== "inactive"
                  ) {
                    mediaRecorderRef.current.stop();
                    mediaRecorderRef.current.stream
                      .getTracks()
                      .forEach((track) => track.stop());
                  }
                  setIsPaused(false);
                  navigate("/");
                }}
              />
            }
          />
          <Route
            path="/transcript"
            element={
              <TranscriptScreen
                transcript={transcript}
                onGenerate={handleGenerateReport}
                onBack={() => navigate("/recording")}
              />
            }
          />
          <Route
            path="/report"
            element={
              <ReportScreen
                reportText={reportText}
                isGeneratingReport={isGeneratingReport}
                onChange={setReportText}
                onSave={() => navigate("/")}
                onBack={() => {
                  if (location.state?.from === "start") {
                    navigate("/");
                  } else {
                    navigate("/transcript");
                  }
                }}
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
