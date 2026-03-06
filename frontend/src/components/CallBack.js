import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiCheckCircle, FiAlertCircle, FiLock, FiFileText } from "react-icons/fi";

const S = {
  page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: 16 },
  card: { background: "white", borderRadius: 24, padding: "48px 40px", maxWidth: 420, width: "100%", boxShadow: "0 24px 80px rgba(0,0,0,0.12)", border: "1px solid #e8edf5", textAlign: "center" },

  brandRow: { display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 32 },
  brandIcon: { width: 40, height: 40, borderRadius: 11, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" },
  brandName: { fontSize: 20, fontWeight: 900, background: "linear-gradient(135deg, #2563eb, #7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },

  spinnerWrap: { position: "relative", width: 80, height: 80, margin: "0 auto 24px" },
  spinnerRing: { width: 80, height: 80, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.9s linear infinite" },
  spinnerIcon: { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" },

  successWrap: { width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg, #f0fdf4, #dcfce7)", border: "2px solid #bbf7d0", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px", animation: "scaleIn 0.4s ease-out" },
  errorWrap: { width: 80, height: 80, borderRadius: "50%", background: "#fef2f2", border: "2px solid #fecaca", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px" },

  title: (color) => ({ margin: "0 0 8px", fontSize: 22, fontWeight: 800, color, letterSpacing: "-0.3px" }),
  subtitle: { margin: "0 0 20px", fontSize: 14, color: "#64748b", lineHeight: 1.5 },

  dots: { display: "flex", justifyContent: "center", gap: 6 },
  dot: (delay, color) => ({ width: 8, height: 8, borderRadius: "50%", background: color, animation: `bounce 1.2s ease-in-out ${delay} infinite` }),

  progressTrack: { width: "100%", height: 6, background: "#e2e8f0", borderRadius: 20, overflow: "hidden", margin: "16px 0 0" },
  progressBar: { height: "100%", background: "linear-gradient(90deg, #16a34a, #22c55e)", borderRadius: 20, animation: "progress 1.5s ease-in-out forwards" },

  errorMsg: { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: "12px 16px", fontSize: 13, color: "#991b1b", fontWeight: 500, marginBottom: 8 },

  securityRow: { display: "flex", alignItems: "center", justifyContent: "center", gap: 5, marginTop: 28, paddingTop: 20, borderTop: "1px solid #f1f5f9", fontSize: 12, color: "#94a3b8" },
};

export default function Callback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("processing");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (accessToken && refreshToken) {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      setStatus("success");
      window.history.replaceState({}, document.title, "/");
      setTimeout(() => navigate("/dashboard", { replace: true }), 1500);
    } else {
      setStatus("error");
      setTimeout(() => navigate("/", { replace: true }), 2000);
    }
  }, [navigate]);

  return (
    <div style={S.page}>
      <div style={S.card}>
        {/* Brand */}
        <div style={S.brandRow}>
          <div style={S.brandIcon}><FiFileText color="white" size={18} /></div>
          <span style={S.brandName}>Zapplic</span>
        </div>

        {/* Icon */}
        {status === "processing" && (
          <div style={S.spinnerWrap}>
            <div style={S.spinnerRing} />
            <div style={S.spinnerIcon}><FiLock color="#2563eb" size={22} /></div>
          </div>
        )}
        {status === "success" && (
          <div style={S.successWrap}><FiCheckCircle color="#16a34a" size={36} /></div>
        )}
        {status === "error" && (
          <div style={S.errorWrap}><FiAlertCircle color="#ef4444" size={36} /></div>
        )}

        {/* Content */}
        {status === "processing" && (
          <>
            <h2 style={S.title("#0f172a")}>Signing You In</h2>
            <p style={S.subtitle}>Processing your authentication...</p>
            <div style={S.dots}>
              <div style={S.dot("0ms", "#2563eb")} />
              <div style={S.dot("160ms", "#7c3aed")} />
              <div style={S.dot("320ms", "#2563eb")} />
            </div>
          </>
        )}
        {status === "success" && (
          <>
            <h2 style={S.title("#16a34a")}>Welcome Back!</h2>
            <p style={S.subtitle}>Signed in successfully. Redirecting to your dashboard...</p>
            <div style={S.progressTrack}><div style={S.progressBar} /></div>
          </>
        )}
        {status === "error" && (
          <>
            <h2 style={S.title("#dc2626")}>Authentication Failed</h2>
            <div style={S.errorMsg}>Missing authentication tokens. Please try logging in again.</div>
            <p style={{ ...S.subtitle, marginBottom: 0 }}>Redirecting to login page...</p>
          </>
        )}

        <div style={S.securityRow}>
          <FiLock size={11} />
          Secured Authentication
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.6); } to { opacity: 1; transform: scale(1); } }
        @keyframes progress { from { width: 0%; } to { width: 100%; } }
      `}</style>
    </div>
  );
}