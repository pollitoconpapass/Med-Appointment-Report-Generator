import { useRef } from "react";
import { MilkdownProvider } from "@milkdown/react";
import { MilkdownEditor } from "../components/MilkdownEditor";

export const ReportScreen = ({ reportText, isGeneratingReport, onChange }) => {
  const reportRef = useRef("");

  const handleSave = () => {
    const content = isGeneratingReport ? reportText : reportRef.current;
    console.log("Saving report:", content);
    alert("Report saved!");
  };

  return (
    <div className="report-screen">
      <h2>Medical Report</h2>
      <p className="hint">
        {isGeneratingReport
          ? "Generating report..."
          : "Review and edit the medical report"}
      </p>
      <div className="editor-container">
        {isGeneratingReport ? (
          <div className="streaming-content">
            {reportText}
          </div>
        ) : (
          <MilkdownProvider>
            <MilkdownEditor
              content={reportText}
              onChange={(markdown) => {
                reportRef.current = markdown;
                onChange(markdown);
              }}
            />
          </MilkdownProvider>
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
