import { useRef, useState, useEffect } from "react";
import { TiptapEditor } from "../components/TiptapEditor";

export const ReportScreen = ({
  reportText,
  currentReport,
  setCurrentReport,
  isGeneratingReport,
  onChange,
  onBack,
  onSave,
}) => {
  const reportRef = useRef(reportText);
  const [title, setTitle] = useState(currentReport?.title || "Medical Report");

  useEffect(() => {
    if (currentReport?.title) {
      setTitle(currentReport.title);
    }
  }, [currentReport]);

  const handleSave = () => {
    const content = isGeneratingReport
      ? reportText
      : reportRef.current || reportText;

    const reportData = {
      id: currentReport?.id || Date.now().toString(),
      date: currentReport?.date || new Date().toISOString(),
      title: title,
      content: content,
    };

    try {
      const existingReports = JSON.parse(
        localStorage.getItem("marge_reports") || "[]",
      );

      let updatedReports;
      if (currentReport?.id) {
        // Update existing report
        updatedReports = existingReports.map((r) =>
          r.id === currentReport.id ? reportData : r,
        );
      } else {
        // Add new report
        updatedReports = [reportData, ...existingReports];
      }

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
          disabled={isGeneratingReport}
          style={{ opacity: isGeneratingReport ? 0.5 : 1 }}
        >
          Save Report
        </button>
      </div>
    </div>
  );
};
