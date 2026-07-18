import React, { useEffect, useState } from "react";
import { API_URL } from "../constants";

export const StartScreen = ({
  language,
  setLanguage,
  onStart,
  onViewReport,
  authHeaders,
}) => {
  const [reports, setReports] = useState([]);
  const [showLanguageModal, setShowLanguageModal] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/reports/`, {
          headers: authHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          setReports(data.reports);
        }
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    })();
  }, [authHeaders]);

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

  const handleDelete = async (e, reportId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this report?")) return;
    try {
      const res = await fetch(`${API_URL}/api/reports/${reportId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setReports((prev) => prev.filter((r) => r.id !== reportId));
      }
    } catch (err) {
      console.error("Failed to delete report:", err);
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
              <span className="report-date">
                {formatDate(report.created_at)}
              </span>
              <span
                className={`report-status status-${report.status || "draft"}`}
              >
                {report.status || "draft"}
              </span>
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
