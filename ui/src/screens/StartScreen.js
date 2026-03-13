import React, { useEffect, useState } from "react";

export const StartScreen = ({
  language,
  setLanguage,
  onStart,
  onViewReport,
}) => {
  const [reports, setReports] = useState([]);
  const [showLanguageModal, setShowLanguageModal] = useState(false);

  useEffect(() => {
    const savedReports = JSON.parse(
      localStorage.getItem("marge_reports") || "[]",
    );
    setReports(savedReports);
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleStartClick = () => {
    setShowLanguageModal(true);
  };

  const handleConfirmLanguage = () => {
    setShowLanguageModal(false);
    onStart();
  };

  const handleDelete = (e, reportId) => {
    e.stopPropagation(); // Prevent opening the report when clicking delete
    if (window.confirm("Are you sure you want to delete this report?")) {
      const updatedReports = reports.filter((r) => r.id !== reportId);
      localStorage.setItem("marge_reports", JSON.stringify(updatedReports));
      setReports(updatedReports);
    }
  };

  return (
    <div className="start-screen">
      <div className="start-screen-header">
        <h2>Saved Reports</h2>
        <button className="start-appointment-btn" onClick={handleStartClick}>
          + Start an Appointment
        </button>
      </div>

      {reports.length === 0 ? (
        <p className="no-reports">No reports available yet</p>
      ) : (
        <div className="reports-list">
          {reports.map((report) => (
            <div
              key={report.id}
              className="report-card"
              onClick={() => onViewReport && onViewReport(report)}
            >
              <div className="report-card-header">
                <h3>{report.title || "Medical Report"}</h3>
                <button
                  className="delete-report-btn"
                  onClick={(e) => handleDelete(e, report.id)}
                  title="Delete Report"
                >
                  &times;
                </button>
              </div>
              <span className="report-date">{formatDate(report.date)}</span>
              <div className="report-preview">
                {report.content.substring(0, 150)}...
              </div>
            </div>
          ))}
        </div>
      )}

      {showLanguageModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowLanguageModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Select Appointment Language</h3>
            <p>Please choose the primary language for the consultation:</p>

            <div className="language-options">
              <button
                className={`lang-option ${language === "en" ? "active" : ""}`}
                onClick={() => setLanguage("en")}
              >
                <span className="lang-emoji">🇺🇸</span>
                <span className="lang-text">English</span>
              </button>

              <button
                className={`lang-option ${language === "es" ? "active" : ""}`}
                onClick={() => setLanguage("es")}
              >
                <span className="lang-emoji">🇪🇸</span>
                <span className="lang-text">Spanish</span>
              </button>
            </div>

            <div className="modal-actions">
              <button
                className="cancel-btn"
                onClick={() => setShowLanguageModal(false)}
              >
                Cancel
              </button>
              <button className="confirm-btn" onClick={handleConfirmLanguage}>
                Start Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
