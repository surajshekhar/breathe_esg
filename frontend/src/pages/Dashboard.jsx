import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getErrorMessage } from "../api/client";
import { approveRecord, getRecords, rejectRecord } from "../api/ingestion";

const Dashboard = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);
  const [uploadSummary, setUploadSummary] = useState(null);
  const [dataSourceFilter, setDataSourceFilter] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const isFetching = useRef(false);

  const loadRecords = async (dataSourceId = null) => {
    if (isFetching.current) {
      return records.length;
    }

    isFetching.current = true;
    setError("");
    setLoading(true);

    try {
      const params = { limit: 500 };
      if (dataSourceId) {
        params.data_source_id = dataSourceId;
      }
      const response = await getRecords({
        timeout: 12000,
        params,
      });
      const data = response.data || [];
      setRecords(data);
      return data.length;
    } catch (loadError) {
      setError(getErrorMessage(loadError));
      return 0;
    } finally {
      setLoading(false);
      isFetching.current = false;
    }
  };

  const resetDashboard = () => {
    setError("");
    setUploadSummary(null);
    setDataSourceFilter(null);
    setRecords([]);
  };

  useEffect(() => {
    const incomingSummary = location.state?.uploadResult;
    if (incomingSummary) {
      setUploadSummary(incomingSummary);
      setDataSourceFilter(incomingSummary.data_source_id);
      loadRecords(incomingSummary.data_source_id);
    } else {
      setUploadSummary(null);
      setDataSourceFilter(null);
      setRecords([]);
    }

    if (!location.state?.refresh) {
      return;
    }

    let isMounted = true;
    const refreshWithRetry = async () => {
      for (let attempt = 0; attempt < 4; attempt += 1) {
        const count = await loadRecords(incomingSummary?.data_source_id);
        if (!isMounted) {
          return;
        }
        if (count > 0) {
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 900));
      }
    };

    refreshWithRetry();
    navigate("/dashboard", { replace: true, state: {} });

    return () => {
      isMounted = false;
    };
  }, [location.state, navigate]);

  const suspiciousRows = useMemo(
    () => records.filter((record) => record.status === "suspicious"),
    [records]
  );

  const summary = useMemo(() => {
    const counts = records.reduce(
      (accumulator, record) => {
        accumulator.total += 1;
        accumulator[record.status] = (accumulator[record.status] || 0) + 1;
        return accumulator;
      },
      { total: 0 }
    );

    return counts;
  }, [records]);

  const handleReview = async (recordId, action) => {
    setActionId(recordId);
    setError("");

    try {
      if (action === "approved") {
        await approveRecord(recordId);
      } else {
        await rejectRecord(recordId);
      }

      setRecords((current) =>
        current.map((record) =>
          record.id === recordId
            ? { ...record, status: action, locked_for_audit: true }
            : record
        )
      );
    } catch (reviewError) {
      setError(getErrorMessage(reviewError));
    } finally {
      setActionId(null);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Review</p>
        <h1>Emissions dashboard</h1>
        <p className="muted">
          Track normalized records, review suspicious rows, and approve or
          reject entries.
        </p>
      </header>

      <section className="panel summary">
        <div>
          <p className="stat-label">Total records</p>
          <p className="stat-value">{summary.total || 0}</p>
        </div>
        <div>
          <p className="stat-label">Pending</p>
          <p className="stat-value">{summary.pending || 0}</p>
        </div>
        <div>
          <p className="stat-label">Suspicious</p>
          <p className="stat-value">{summary.suspicious || 0}</p>
        </div>
        <div>
          <p className="stat-label">Approved</p>
          <p className="stat-value">{summary.approved || 0}</p>
        </div>
        <div>
          <p className="stat-label">Rejected</p>
          <p className="stat-value">{summary.rejected || 0}</p>
        </div>
      </section>

      {uploadSummary ? (
        <section className="panel banner">
          <div>
            <p className="stat-label">Upload complete</p>
            <p className="stat-value">
              Source #{uploadSummary.data_source_id}
            </p>
          </div>
          <div>
            <p className="stat-label">Rows processed</p>
            <p className="stat-value">{uploadSummary.rows}</p>
          </div>
          <div>
            <p className="stat-label">Suspicious rows</p>
            <p className="stat-value">
              {uploadSummary.suspicious_rows}
            </p>
          </div>
        </section>
      ) : null}

      {error ? <div className="alert error">{error}</div> : null}

      <section className="panel">
        <div className="section-heading">
          <h2>Suspicious rows</h2>
          <button
            className="ghost"
            type="button"
            onClick={resetDashboard}
          >
            Refresh
          </button>
        </div>
        {loading ? (
          <p className="muted">Loading records...</p>
        ) : suspiciousRows.length === 0 ? (
          <p className="muted">No suspicious rows detected.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Source</th>
                  <th>Scope</th>
                  <th>Category</th>
                  <th>Activity</th>
                  <th>Quantity</th>
                  <th>Unit</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {suspiciousRows.map((record) => (
                  <tr key={record.id} className="row-suspicious">
                    <td>{record.id}</td>
                    <td>{record.source_type || "-"}</td>
                    <td>{record.scope}</td>
                    <td>{record.category}</td>
                    <td>{record.activity_type}</td>
                    <td>{record.quantity}</td>
                    <td>{record.original_unit || "-"}</td>
                    <td>{record.suspicious_reason || "-"}</td>
                    <td>{record.status}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="primary"
                          type="button"
                          onClick={() => handleReview(record.id, "approved")}
                          disabled={actionId === record.id}
                        >
                          Approve
                        </button>
                        <button
                          className="danger"
                          type="button"
                          onClick={() => handleReview(record.id, "rejected")}
                          disabled={actionId === record.id}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>All records</h2>
          <span className="muted">{records.length} total</span>
        </div>
        {loading ? (
          <p className="muted">Loading records...</p>
        ) : records.length === 0 ? (
          <p className="muted">No records yet. Upload a CSV to get started.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Source</th>
                  <th>Scope</th>
                  <th>Category</th>
                  <th>Activity</th>
                  <th>Quantity</th>
                  <th>Unit</th>
                  <th>CO2e</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.id}</td>
                    <td>{record.source_type || "-"}</td>
                    <td>{record.scope}</td>
                    <td>{record.category}</td>
                    <td>{record.activity_type}</td>
                    <td>{record.quantity}</td>
                    <td>{record.normalized_unit || record.original_unit || "-"}</td>
                    <td>{record.co2e}</td>
                    <td>
                      <span className={`status-pill status-${record.status}`}>
                        {record.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
