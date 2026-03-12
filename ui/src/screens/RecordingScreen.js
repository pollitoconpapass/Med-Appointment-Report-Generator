export const RecordingScreen = ({
  isRecording,
  isPaused,
  setIsPaused,
  audioLevel,
  transcript,
  onEnd,
  onBack,
}) => {
  const handleBack = () => {
    if (
      isRecording &&
      !window.confirm(
        "Are you sure you want to go back? The recording will be lost.",
      )
    ) {
      return;
    }
    onBack();
  };

  return (
    <div className="recording-screen">
      <div className="screen-header">
        <button className="back-button" onClick={handleBack}>
          ← Back
        </button>
        <h2>Recording Session</h2>
      </div>

      <div className="audio-visualizer">
        <div className="visualizer-bars">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="bar"
              style={{
                height: `${Math.max(10, audioLevel * 100 * Math.random())}%`,
                animationDelay: `${i * 0.05}s`,
                background: isPaused
                  ? "#9e9e9e"
                  : "linear-gradient(to top, var(--primary), var(--primary-light))",
              }}
            />
          ))}
        </div>
        <p className={`listening-text ${isPaused ? "paused" : ""}`}>
          {isPaused ? "Paused" : isRecording ? "Listening..." : "Starting..."}
        </p>
        <p className="transcript-preview">
          {transcript
            .map((t) => t.text)
            .join(" ")
            .slice(-100)}
        </p>
      </div>

      <div className="recording-controls">
        <button
          className={`pause-button ${isPaused ? "resuming" : ""}`}
          onClick={() => setIsPaused(!isPaused)}
          disabled={!isRecording}
        >
          {isPaused ? "▶ Resume" : "⏸ Pause"}
        </button>

        <button className="end-button" onClick={onEnd}>
          <span className="hangup-icon"> 📞</span>
          End Appointment
        </button>
      </div>
    </div>
  );
};
