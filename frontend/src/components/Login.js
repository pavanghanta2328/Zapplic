import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FcGoogle } from "react-icons/fc";
import { FiMail, FiLock, FiEye, FiEyeOff, FiFileText } from "react-icons/fi";
import api from "../services/api";
import { BASE_URL } from "../config/common";

const S = {
  page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: 16 },

  // Left panel (branding)
  wrap: { display: "flex", width: "100%", maxWidth: 880, background: "white", borderRadius: 24, overflow: "hidden", boxShadow: "0 24px 80px rgba(0,0,0,0.12)", border: "1px solid #e8edf5" },
  leftPanel: { flex: 1, background: "linear-gradient(145deg, #1e3a8a 0%, #4c1d95 60%, #0f172a 100%)", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative", overflow: "hidden", minWidth: 0 },
  leftPattern: { position: "absolute", inset: 0, opacity: 0.06, backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)", backgroundSize: "32px 32px", pointerEvents: "none" },
  brandRow: { display: "flex", alignItems: "center", gap: 12 },
  brandIcon: { width: 44, height: 44, borderRadius: 12, background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center" },
  brandName: { fontSize: 22, fontWeight: 900, color: "white", letterSpacing: "-0.3px" },
  leftBody: { flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", paddingTop: 40, paddingBottom: 40 },
  leftTitle: { fontSize: 32, fontWeight: 900, color: "white", lineHeight: 1.2, letterSpacing: "-0.8px", marginBottom: 14 },
  leftSub: { fontSize: 15, color: "rgba(255,255,255,0.65)", lineHeight: 1.6 },
  featureList: { marginTop: 32, display: "flex", flexDirection: "column", gap: 12 },
  featureItem: { display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "rgba(255,255,255,0.8)" },
  featureDot: { width: 7, height: 7, borderRadius: "50%", background: "#4ade80", flexShrink: 0 },
  leftFooter: { fontSize: 12, color: "rgba(255,255,255,0.35)" },

  // Right panel (form)
  rightPanel: { flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", minWidth: 0 },
  formTitle: { margin: "0 0 4px", fontSize: 26, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" },
  formSub: { margin: "0 0 28px", fontSize: 14, color: "#64748b" },

  // Fields
  fieldGroup: { marginBottom: 18 },
  label: { display: "block", fontSize: 12, fontWeight: 700, color: "#374151", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.4px" },
  inputWrap: { position: "relative" },
  inputIcon: (focused) => ({ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", color: focused ? "#2563eb" : "#94a3b8", transition: "color 0.15s", pointerEvents: "none" }),
  input: (focused) => ({ width: "100%", paddingLeft: 40, paddingRight: 14, paddingTop: 11, paddingBottom: 11, border: `2px solid ${focused ? "#2563eb" : "#e2e8f0"}`, borderRadius: 11, fontSize: 14, outline: "none", background: "#f8fafc", boxSizing: "border-box", transition: "all 0.15s", boxShadow: focused ? "0 0 0 3px rgba(37,99,235,0.1)" : "none" }),
  inputIconRight: { position: "absolute", right: 13, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#94a3b8", display: "flex", padding: 0 },

  // Error
  errorBox: { display: "flex", alignItems: "flex-start", gap: 8, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "11px 14px", marginBottom: 18, fontSize: 13, color: "#991b1b", fontWeight: 500 },

  // Forgot
  forgotRow: { textAlign: "right", marginBottom: 18 },
  forgotBtn: { background: "none", border: "none", fontSize: 12, color: "#2563eb", cursor: "pointer", fontWeight: 600, padding: 0 },

  // Submit button
  submitBtn: (loading) => ({ width: "100%", padding: "13px", background: loading ? "#e2e8f0" : "linear-gradient(135deg, #2563eb, #7c3aed)", color: loading ? "#94a3b8" : "white", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, letterSpacing: "0.2px", boxShadow: loading ? "none" : "0 4px 14px rgba(37,99,235,0.3)" }),

  // Divider
  divider: { display: "flex", alignItems: "center", gap: 12, margin: "20px 0" },
  dividerLine: { flex: 1, height: 1, background: "#f1f5f9" },
  dividerText: { fontSize: 12, color: "#94a3b8", fontWeight: 600 },

  // Google
  googleBtn: { width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 10, padding: "12px", background: "#f8fafc", border: "2px solid #e2e8f0", borderRadius: 12, cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#374151", transition: "all 0.15s" },

  // Register link
  registerRow: { textAlign: "center", marginTop: 20, fontSize: 13, color: "#64748b" },
  registerBtn: { background: "none", border: "none", color: "#2563eb", fontWeight: 700, cursor: "pointer", fontSize: 13, padding: 0, marginLeft: 4 },

  spinner: { width: 18, height: 18, border: "3px solid rgba(148,163,184,0.3)", borderTop: "3px solid #94a3b8", borderRadius: "50%", animation: "spin 0.8s linear infinite" },
};

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOAuthLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focused, setFocused] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { setError("Email and password are required"); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("Enter a valid email address"); return; }
    try {
      setLoading(true); setError("");
      const res = await api.post("/auth/login", { email, password });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      onLoginSuccess();
      setTimeout(() => navigate("/dashboard"), 100);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password");
    } finally { setLoading(false); }
  };

  const handleGoogleLogin = () => {
    setOAuthLoading(true);
    const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem("oauth_state", state);
    window.location.href = `${BASE_URL}/google/login?state=${encodeURIComponent(state)}`;
  };

  return (
    <div style={S.page}>
      <div style={S.wrap}>
        {/* ── Left branding panel ── */}
        <div style={S.leftPanel}>
          <div style={S.leftPattern} />
          <div style={S.brandRow}>
            <div style={S.brandIcon}><FiFileText color="white" size={20} /></div>
            <span style={S.brandName}>Zapplic</span>
          </div>
          <div style={S.leftBody}>
            <h2 style={S.leftTitle}>AI-Powered<br />Resume Intelligence</h2>
            <p style={S.leftSub}>Parse, search and manage candidate resumes with precision. Built for modern recruitment teams.</p>
            <div style={S.featureList}>
              {["Automatic AI parsing & data extraction", "Duplicate & version detection", "Advanced candidate search", "Bulk upload with ZIP support"].map(f => (
                <div key={f} style={S.featureItem}><span style={S.featureDot} />{f}</div>
              ))}
            </div>
          </div>
          <div style={S.leftFooter}>© 2025 Zapplic · All rights reserved</div>
        </div>

        {/* ── Right form panel ── */}
        <div style={S.rightPanel}>
          <h2 style={S.formTitle}>Welcome back</h2>
          <p style={S.formSub}>Sign in to your recruiter account</p>

          {error && (
            <div style={S.errorBox}>
              <span style={{ fontSize: 16, flexShrink: 0 }}>⚠️</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={S.fieldGroup}>
              <label style={S.label}>Email Address</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "email")}><FiMail size={16} /></div>
                <input type="email" value={email} onChange={e => { setEmail(e.target.value); setError(""); }}
                  onFocus={() => setFocused("email")} onBlur={() => setFocused(null)}
                  style={S.input(focused === "email")} placeholder="you@example.com" />
              </div>
            </div>

            <div style={S.fieldGroup}>
              <label style={S.label}>Password</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "password")}><FiLock size={16} /></div>
                <input type={showPassword ? "text" : "password"} value={password}
                  onChange={e => { setPassword(e.target.value); setError(""); }}
                  onFocus={() => setFocused("password")} onBlur={() => setFocused(null)}
                  style={{ ...S.input(focused === "password"), paddingRight: 40 }} placeholder="••••••••" />
                <button type="button" style={S.inputIconRight} onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <FiEyeOff size={16} /> : <FiEye size={16} />}
                </button>
              </div>
            </div>

            <div style={S.forgotRow}>
              <button type="button" style={S.forgotBtn}>Forgot password?</button>
            </div>

            <button type="submit" style={S.submitBtn(loading)} disabled={loading}>
              {loading ? <><div style={S.spinner} />Signing in...</> : "Sign In"}
            </button>
          </form>

          <div style={S.divider}>
            <div style={S.dividerLine} />
            <span style={S.dividerText}>OR</span>
            <div style={S.dividerLine} />
          </div>

          <button style={S.googleBtn} onClick={handleGoogleLogin} disabled={oauthLoading}
            onMouseEnter={e => e.currentTarget.style.background = "#f0f4ff"}
            onMouseLeave={e => e.currentTarget.style.background = "#f8fafc"}
          >
            <FcGoogle size={20} />
            {oauthLoading ? "Authenticating..." : "Continue with Google"}
          </button>

          <div style={S.registerRow}>
            Don't have an account?
            <button style={S.registerBtn} onClick={() => navigate("/register")}>Create Account</button>
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default Login;