import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../api/client";
import { uploadCsv } from "../api/ingestion";

const UploadPage = () => {
  const navigate = useNavigate();
  const [sourceType, setSourceType] = useState("sap");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setStatus("");

    if (!file) {
      setError("Please choose a CSV file.");
      return;
    }

    try {
      setSubmitting(true);
      setStatus("Uploading file...");
      const response = await uploadCsv({
        file,
        sourceType,
      });
      setStatus("Upload complete. Opening dashboard...");
      navigate("/dashboard", {
        replace: true,
        state: { refresh: true, uploadResult: response.data },
      });
    } catch (uploadError) {
      setError(getErrorMessage(uploadError));
      setStatus("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Ingestion</p>
        <h1>Upload CSV</h1>
        <p className="muted">
          Send SAP, utility, or travel CSVs to the ingestion API. The backend
          will normalize records and flag suspicious rows.
        </p>
      </header>

      <form className="panel form-grid" onSubmit={handleSubmit}>
        <label className="field">
          <span>Source type</span>
          <select
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value)}
          >
            <option value="sap">SAP</option>
            <option value="utility">Utility</option>
            <option value="travel">Travel</option>
          </select>
        </label>

        <label className="field file-field">
          <span>CSV file</span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
          <span className="file-meta">
            {file ? file.name : "No file selected"}
          </span>
        </label>

        <div className="actions">
          <button
            className="primary"
            type="submit"
            disabled={submitting || !file}
          >
            {submitting ? "Uploading..." : "Upload CSV"}
          </button>
          <button
            className="ghost"
            type="button"
            onClick={() => navigate("/dashboard")}
          >
            View dashboard
          </button>
        </div>

        {status ? <p className="status-text">{status}</p> : null}
      </form>

      {error ? <div className="alert error">{error}</div> : null}

      <div className="panel hint-card">
        <h2>What happens next?</h2>
        <p className="muted">
          After upload, records are normalized and suspicious rows are flagged.
          The dashboard will open automatically when the upload finishes.
        </p>
      </div>
    </div>
  );
};

export default UploadPage;
