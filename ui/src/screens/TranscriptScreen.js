import { useRef } from "react";

export const TranscriptScreen = ({ transcript, onGenerate }) => {
  const transcriptRef = useRef("");

  const getTranscriptText = () => {
    return transcript.map((item) => item.text).join("\n\n");
  };

  return (
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
        <button className="generate-button" onClick={onGenerate}>
          Generate Report →
        </button>
      </div>
    </div>
  );
};
