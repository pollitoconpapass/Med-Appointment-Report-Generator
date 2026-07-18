import React, { useState, useEffect, useRef, useCallback } from "react";
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
import { SignInScreen } from "./screens/SignInScreen";
import { RegisterScreen } from "./screens/RegisterScreen";

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
  const [currentReport, setCurrentReport] = useState(null);

  // Auth state
  const [token, setToken] = useState(localStorage.getItem("marge_token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("marge_user");
    return raw ? JSON.parse(raw) : null;
  });

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

  const PROTECTED_PATHS = ["/", "/recording", "/transcript", "/report"];

  useEffect(() => {
    if (location.pathname === "/recording" && !sessionId && !isRecording) {
      navigate("/");
    }
  }, [location.pathname, sessionId, isRecording, navigate]);

  // Auth guard — redirect to /login if not authenticated
  useEffect(() => {
    if (!token && PROTECTED_PATHS.includes(location.pathname)) {
      navigate("/login", { replace: true });
    }
  }, [token, location.pathname, navigate]);

  // Redirect already-authenticated users away from login/register
  useEffect(() => {
    if (token && ["/login", "/register"].includes(location.pathname)) {
      navigate("/", { replace: true });
    }
  }, [token, location.pathname, navigate]);

  const authHeaders = useCallback(() => {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }, [token]);

  const handleLogin = async (username, password) => {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("marge_token", data.token);
    localStorage.setItem("marge_user", JSON.stringify(data.user));
    setToken(data.token);
    setUser(data.user);
    navigate("/", { replace: true });
  };

  const handleRegister = async (username, email, password) => {
    const res = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  };

  const handleLogout = () => {
    if (token) {
      fetch(`${API_URL}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    localStorage.removeItem("marge_token");
    localStorage.removeItem("marge_user");
    setToken(null);
    setUser(null);
    navigate("/");
  };

  const startAppointment = async () => {
    setTranscript([]);
    setReportText("");
    reportRef.current = "";
    setCurrentReport(null);

    try {
      const response = await fetch(`${API_URL}/api/appointments/start`, {
        method: "POST",
        headers: authHeaders(),
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

  const handleViewReport = async (report) => {
    try {
      const res = await fetch(`${API_URL}/api/reports/${report.id}`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const full = await res.json();
        setReportText(full.content);
        reportRef.current = full.content;
        setCurrentReport(full);
        navigate("/report", { state: { from: "start" } });
      }
    } catch (err) {
      console.error("Failed to fetch report:", err);
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
      const response = await fetch(`${API_URL}/api/appointments/end`, {
        method: "POST",
        headers: authHeaders(),
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
    setCurrentReport({
      title: "Medical Report",
      content: "",
    });

    try {
      const response = await fetch(`${API_URL}/api/reports/generate`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          transcript: finalTranscriptContent,
          session_id: sessionId,
        }),
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
              if (data.done && data.report_id) {
                setCurrentReport((prev) => ({
                  ...prev,
                  id: data.report_id,
                  content: reportContent,
                }));
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
        {user && (
          <span
            className="user-badge"
            onClick={handleLogout}
            title="Click to logout"
          >
            {user.username} ⏻
          </span>
        )}
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
                authHeaders={authHeaders}
              />
            }
          />
          <Route
            path="/login"
            element={
              <SignInScreen
                onLogin={handleLogin}
                onNavigateRegister={() => navigate("/register")}
              />
            }
          />
          <Route
            path="/register"
            element={
              <RegisterScreen
                onRegister={handleRegister}
                onNavigateSignIn={() => navigate("/login")}
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
                currentReport={currentReport}
                setCurrentReport={setCurrentReport}
                isGeneratingReport={isGeneratingReport}
                onChange={setReportText}
                onSave={() => navigate("/")}
                authHeaders={authHeaders}
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
