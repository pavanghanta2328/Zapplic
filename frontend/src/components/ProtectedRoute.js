import { Navigate } from "react-router-dom";
import { FiLock, FiFileText } from "react-icons/fi";
import { useState, useEffect } from "react";

const S = {
  page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)" },
  wrap: { textAlign: "center" },
  brandRow: { display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 32 },
  brandIcon: { width: 40, height: 40, borderRadius: 11, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" },
  brandName: { fontSize: 20, fontWeight: 900, background: "linear-gradient(135deg, #2563eb, #7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  spinnerWrap: { position: "relative", width: 56, height: 56, margin: "0 auto 16px" },
  spinnerRing: { width: 56, height: 56, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.9s linear infinite" },
  spinnerIcon: { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" },
  label: { fontSize: 14, color: "#64748b", fontWeight: 500 },
};

function ProtectedRoute({ children }) {
  const [isChecking, setIsChecking] = useState(true);
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    const t = setTimeout(() => setIsChecking(false), 300);
    return () => clearTimeout(t);
  }, []);

  if (isChecking) {
    return (
      <div style={S.page}>
        <div style={S.wrap}>
          <div style={S.brandRow}>
            <div style={S.brandIcon}><FiFileText color="white" size={18} /></div>
            <span style={S.brandName}>Zapplic</span>
          </div>
          <div style={S.spinnerWrap}>
            <div style={S.spinnerRing} />
            <div style={S.spinnerIcon}><FiLock color="#2563eb" size={18} /></div>
          </div>
          <div style={S.label}>Verifying access...</div>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!token) return <Navigate to="/" replace />;

  return children;
}

export default ProtectedRoute;