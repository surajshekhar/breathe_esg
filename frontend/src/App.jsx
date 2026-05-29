import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import Dashboard from "./pages/Dashboard";
import "./App.css";

const App = () => {
  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark"></span>
          <div>
            <p className="brand-title">Breathe ESG</p>
            <p className="brand-subtitle">Ingestion Console</p>
          </div>
        </div>
        <nav className="nav">
          <NavLink
            to="/upload"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Upload
          </NavLink>
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Dashboard
          </NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
