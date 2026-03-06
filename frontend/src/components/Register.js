import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiUser, FiMail, FiLock, FiEye, FiEyeOff, FiCheckCircle, FiAlertCircle, FiFileText } from "react-icons/fi";
import api from "../services/api";
import { BASE_URL } from "../config/common";

const S = {
  page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: 16 },
  wrap: { display: "flex", width: "100%", maxWidth: 880, background: "white", borderRadius: 24, overflow: "hidden", boxShadow: "0 24px 80px rgba(0,0,0,0.12)", border: "1px solid #e8edf5" },

  // Left
  leftPanel: { flex: "0 0 300px", background: "linear-gradient(145deg, #064e3b 0%, #065f46 40%, #0f172a 100%)", padding: "48px 36px", display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative", overflow: "hidden" },
  leftPattern: { position: "absolute", inset: 0, opacity: 0.05, backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)", backgroundSize: "28px 28px", pointerEvents: "none" },
  brandRow: { display: "flex", alignItems: "center", gap: 10, position: "relative" },
  brandIcon: { width: 40, height: 40, borderRadius: 11, background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" },
  brandName: { fontSize: 20, fontWeight: 900, color: "white" },
  leftBody: { flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", paddingTop: 36, paddingBottom: 36, position: "relative" },
  leftTitle: { fontSize: 26, fontWeight: 900, color: "white", lineHeight: 1.25, letterSpacing: "-0.5px", marginBottom: 12 },
  leftSub: { fontSize: 14, color: "rgba(255,255,255,0.6)", lineHeight: 1.6, marginBottom: 28 },
  stepList: { display: "flex", flexDirection: "column", gap: 14 },
  stepItem: { display: "flex", alignItems: "flex-start", gap: 10 },
  stepNum: { width: 22, height: 22, borderRadius: "50%", background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: "rgba(255,255,255,0.9)", flexShrink: 0, marginTop: 1 },
  stepText: { fontSize: 13, color: "rgba(255,255,255,0.75)", lineHeight: 1.4 },
  leftFooter: { fontSize: 11, color: "rgba(255,255,255,0.3)", position: "relative" },

  // Right
  rightPanel: { flex: 1, padding: "40px 40px", display: "flex", flexDirection: "column", justifyContent: "center", overflowY: "auto" },
  formTitle: { margin: "0 0 4px", fontSize: 24, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.4px" },
  formSub: { margin: "0 0 24px", fontSize: 13, color: "#64748b" },

  fieldGroup: { marginBottom: 14 },
  label: { display: "block", fontSize: 11, fontWeight: 700, color: "#374151", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.4px" },
  inputWrap: { position: "relative" },
  inputIcon: (focused) => ({ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: focused ? "#2563eb" : "#94a3b8", transition: "color 0.15s", pointerEvents: "none" }),
  input: (focused) => ({ width: "100%", paddingLeft: 38, paddingRight: 14, paddingTop: 10, paddingBottom: 10, border: `2px solid ${focused ? "#2563eb" : "#e2e8f0"}`, borderRadius: 10, fontSize: 14, outline: "none", background: "#f8fafc", boxSizing: "border-box", transition: "all 0.15s", boxShadow: focused ? "0 0 0 3px rgba(37,99,235,0.1)" : "none" }),
  inputIconRight: { position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#94a3b8", display: "flex", padding: 0 },

  pwdStrength: (strong) => ({ display: "flex", alignItems: "center", gap: 5, marginTop: 5, fontSize: 12, color: strong ? "#16a34a" : "#d97706", fontWeight: 500 }),

  errorBox: { display: "flex", alignItems: "flex-start", gap: 8, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "10px 13px", marginBottom: 14, fontSize: 13, color: "#991b1b", fontWeight: 500 },

  submitBtn: (loading) => ({ width: "100%", padding: "12px", background: loading ? "#e2e8f0" : "linear-gradient(135deg, #059669, #2563eb)", color: loading ? "#94a3b8" : "white", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 6, boxShadow: loading ? "none" : "0 4px 14px rgba(5,150,105,0.3)" }),

  loginRow: { textAlign: "center", marginTop: 16, fontSize: 13, color: "#64748b" },
  loginBtn: { background: "none", border: "none", color: "#2563eb", fontWeight: 700, cursor: "pointer", fontSize: 13, padding: 0, marginLeft: 4 },

  spinner: { width: 17, height: 17, border: "3px solid rgba(148,163,184,0.3)", borderTop: "3px solid #94a3b8", borderRadius: "50%", animation: "spin 0.8s linear infinite" },
};

function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [pwdStrength, setPwdStrength] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [focused, setFocused] = useState(null);
  const navigate = useNavigate();

  const checkStrength = (pwd) => {
    if (pwd.length < 8) { setPwdStrength("Weak: min 8 characters"); return false; }
    if (!/[A-Z]/.test(pwd)) { setPwdStrength("Weak: add uppercase letter"); return false; }
    if (!/[0-9]/.test(pwd)) { setPwdStrength("Weak: add a number"); return false; }
    if (!/[^a-zA-Z0-9]/.test(pwd)) { setPwdStrength("Weak: add a special character"); return false; }
    setPwdStrength("Strong password ✓"); return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fullName || !email || !password || !confirmPassword) { setError("All fields are required"); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("Enter a valid email address"); return; }
    if (!checkStrength(password)) { setError(pwdStrength); return; }
    if (password !== confirmPassword) { setError("Passwords do not match"); return; }
    try {
      setLoading(true); setError("");
      await api.post(`${BASE_URL}/signup`, { full_name: fullName, email, password, confirm_password: confirmPassword });
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally { setLoading(false); }
  };

  const isStrong = pwdStrength.includes("Strong");

  return (
    <div style={S.page}>
      <div style={S.wrap}>
        {/* Left */}
        <div style={S.leftPanel}>
          <div style={S.leftPattern} />
          <div style={S.brandRow}>
            <div style={S.brandIcon}><FiFileText color="white" size={18} /></div>
            <span style={S.brandName}>Zapplic</span>
          </div>
          <div style={S.leftBody}>
            <h2 style={S.leftTitle}>Start hiring smarter today</h2>
            <p style={S.leftSub}>Join recruiters who use AI to find the best candidates faster.</p>
            <div style={S.stepList}>
              {[["1", "Create your account"], ["2", "Upload your first resume"], ["3", "Search & match candidates"], ["4", "Grow your talent pipeline"]].map(([n, t]) => (
                <div key={n} style={S.stepItem}>
                  <span style={S.stepNum}>{n}</span>
                  <span style={S.stepText}>{t}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={S.leftFooter}>© 2025 Zapplic</div>
        </div>

        {/* Right */}
        <div style={S.rightPanel}>
          <h2 style={S.formTitle}>Create your account</h2>
          <p style={S.formSub}>Join Zapplic and start parsing resumes</p>

          {error && (
            <div style={S.errorBox}>
              <FiAlertCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Full Name */}
            <div style={S.fieldGroup}>
              <label style={S.label}>Full Name</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "name")}><FiUser size={15} /></div>
                <input type="text" value={fullName} onChange={e => { setFullName(e.target.value); setError(""); }}
                  onFocus={() => setFocused("name")} onBlur={() => setFocused(null)}
                  style={S.input(focused === "name")} placeholder="John Doe" />
              </div>
            </div>

            {/* Email */}
            <div style={S.fieldGroup}>
              <label style={S.label}>Email Address</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "email")}><FiMail size={15} /></div>
                <input type="email" value={email} onChange={e => { setEmail(e.target.value); setError(""); }}
                  onFocus={() => setFocused("email")} onBlur={() => setFocused(null)}
                  style={S.input(focused === "email")} placeholder="you@example.com" />
              </div>
            </div>

            {/* Password */}
            <div style={S.fieldGroup}>
              <label style={S.label}>Password</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "pwd")}><FiLock size={15} /></div>
                <input type={showPwd ? "text" : "password"} value={password}
                  onChange={e => { setPassword(e.target.value); checkStrength(e.target.value); setError(""); }}
                  onFocus={() => setFocused("pwd")} onBlur={() => setFocused(null)}
                  style={{ ...S.input(focused === "pwd"), paddingRight: 38 }} placeholder="Min 8 characters" />
                <button type="button" style={S.inputIconRight} onClick={() => setShowPwd(!showPwd)}>
                  {showPwd ? <FiEyeOff size={15} /> : <FiEye size={15} />}
                </button>
              </div>
              {pwdStrength && (
                <div style={S.pwdStrength(isStrong)}>
                  {isStrong ? <FiCheckCircle size={13} /> : <FiAlertCircle size={13} />}
                  {pwdStrength}
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div style={S.fieldGroup}>
              <label style={S.label}>Confirm Password</label>
              <div style={S.inputWrap}>
                <div style={S.inputIcon(focused === "confirm")}><FiLock size={15} /></div>
                <input type={showConfirm ? "text" : "password"} value={confirmPassword}
                  onChange={e => { setConfirmPassword(e.target.value); setError(""); }}
                  onFocus={() => setFocused("confirm")} onBlur={() => setFocused(null)}
                  style={{ ...S.input(focused === "confirm"), paddingRight: 38 }} placeholder="Repeat password" />
                <button type="button" style={S.inputIconRight} onClick={() => setShowConfirm(!showConfirm)}>
                  {showConfirm ? <FiEyeOff size={15} /> : <FiEye size={15} />}
                </button>
              </div>
            </div>

            <button type="submit" style={S.submitBtn(loading)} disabled={loading}>
              {loading ? <><div style={S.spinner} />Creating account...</> : "Create Account →"}
            </button>
          </form>

          <div style={S.loginRow}>
            Already have an account?
            <button style={S.loginBtn} onClick={() => navigate("/")}>Sign In</button>
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default Register;