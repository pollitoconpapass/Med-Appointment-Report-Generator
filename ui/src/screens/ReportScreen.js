import { useRef, useState, useEffect } from "react";
import { TiptapEditor } from "../components/TiptapEditor";
import { API_URL } from "../constants";

export const ReportScreen = ({
  reportText,
  currentReport,
  setCurrentReport,
  isGeneratingReport,
  onChange,
  onBack,
  onSave,
  authHeaders,
}) => {
  const reportRef = useRef(reportText);
  const [title, setTitle] = useState(currentReport?.title || "Medical Report");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (currentReport?.title) {
      setTitle(currentReport.title);
    }
  }, [currentReport]);

  const handleSave = async () => {
    const content = isGeneratingReport
      ? reportText
      : reportRef.current || reportText;

    if (!currentReport?.id) {
      alert("Report was not saved to server. Please generate a report first.");
      return;
    }

    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/reports/${currentReport.id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({ content }),
      });
      if (res.ok) {
        alert("Report saved successfully!");
        if (onSave) onSave();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to save report.");
      }
    } catch (error) {
      console.error("Failed to save report:", error);
      alert("Failed to save report.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="report-screen">
      <div className="screen-header">
        <button
          className="back-button"
          onClick={onBack}
          disabled={isGeneratingReport}
        >
          ← Back
        </button>
        <div className="title-container">
          <input
            type="text"
            className="report-title-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Report Title"
            disabled={isGeneratingReport}
          />
        </div>
      </div>
      <p className="hint">
        {isGeneratingReport
          ? "Generating report..."
          : "Review and edit the medical report"}
      </p>
      <div className="editor-container">
        {isGeneratingReport ? (
          <div className="streaming-content">{reportText}</div>
        ) : (
          <TiptapEditor
            content={reportText}
            onChange={(markdown) => {
              reportRef.current = markdown;
              onChange(markdown);
            }}
          />
        )}
      </div>
      <div className="action-buttons">
        <button
          className="save-button"
          onClick={handleSave}
          disabled={isGeneratingReport || saving}
          style={{ opacity: isGeneratingReport || saving ? 0.5 : 1 }}
        >
          {saving ? "Saving..." : "Save Report"}
        </button>
      </div>
    </div>
  );
};
