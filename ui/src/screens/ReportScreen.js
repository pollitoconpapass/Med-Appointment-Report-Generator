import { useRef } from "react";
import { TiptapEditor } from "../components/TiptapEditor";

export const ReportScreen = ({
  reportText,
  isGeneratingReport,
  onChange,
  onBack,
  onSave,
}) => {
  const reportRef = useRef("");

  const handleSave = () => {
    const content = isGeneratingReport
      ? reportText
      : reportRef.current || reportText;

    const newReport = {
      id: Date.now().toString(),
      date: new Date().toISOString(),
      content: content,
    };

    try {
      const existingReports = JSON.parse(
        localStorage.getItem("marge_reports") || "[]",
      );
      const updatedReports = [newReport, ...existingReports];
      localStorage.setItem("marge_reports", JSON.stringify(updatedReports));

      alert("Report saved successfully!");
      if (onSave) onSave();
    } catch (error) {
      console.error("Failed to save report:", error);
      alert("Failed to save report.");
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
        <h2>Medical Report</h2>
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
          disabled={isGeneratingReport}
          style={{ opacity: isGeneratingReport ? 0.5 : 1 }}
        >
          Save Report
        </button>
      </div>
    </div>
  );
};
