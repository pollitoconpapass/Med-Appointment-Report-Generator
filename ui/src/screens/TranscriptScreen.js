import { useState, useEffect } from "react";

export const TranscriptScreen = ({ transcript, onGenerate, onBack }) => {
  const [items, setItems] = useState([]);

  // Initialize items from transcript prop
  useEffect(() => {
    setItems(
      transcript.map((item) => ({
        ...item,
        id: Math.random().toString(36).substr(2, 9),
      })),
    );
  }, [transcript]);

  const getSpeakerLabel = (speaker) => {
    if (!speaker || speaker === "Unknown") return "Speaker A";

    // Simple mapping: SPEAKER_00 -> Speaker A, SPEAKER_01 -> Speaker B, etc.
    const match = speaker.match(/\d+/);
    if (match) {
      const index = parseInt(match[0]);
      return `Speaker ${String.fromCharCode(65 + index)}`;
    }
    return speaker;
  };

  const getSpeakerClass = (speaker) => {
    const label = getSpeakerLabel(speaker);
    return label === "Speaker A" ? "speaker-a" : "speaker-b";
  };

  const handleTextChange = (id, newText) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, text: newText } : item)),
    );
  };

  const handleGenerate = () => {
    // Format items back into a single string for the LLM
    const finalContent = items
      .map((item) => `${getSpeakerLabel(item.speaker)}: ${item.text}`)
      .join("\n\n");
    onGenerate(finalContent);
  };

  return (
    <div className="transcript-screen">
      <div className="screen-header">
        <button className="back-button" onClick={onBack}>
          ← Back
        </button>
        <h2>Edit Transcript</h2>
      </div>
      <p className="hint">
        Review and edit the conversation blocks before generating the report
      </p>

      <div className="editor-container">
        <div className="transcript-list">
          {items.map((item) => (
            <div
              key={item.id}
              className={`transcript-item ${getSpeakerClass(item.speaker)}`}
            >
              <div className="speaker-label">
                {getSpeakerLabel(item.speaker)}
              </div>
              <textarea
                className="bubble-editor"
                value={item.text}
                onChange={(e) => handleTextChange(item.id, e.target.value)}
                rows={Math.max(1, Math.ceil(item.text.length / 50))}
                onInput={(e) => {
                  e.target.style.height = "auto";
                  e.target.style.height = e.target.scrollHeight + "px";
                }}
              />
            </div>
          ))}
          {items.length === 0 && (
            <p className="loading">No transcript available.</p>
          )}
        </div>
      </div>

      <div className="action-buttons">
        <button className="generate-button" onClick={handleGenerate}>
          Generate Report →
        </button>
      </div>
    </div>
  );
};
