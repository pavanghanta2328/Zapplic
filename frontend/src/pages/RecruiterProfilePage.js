import React, { useState, useEffect } from "react";
import { FiEdit2, FiMail, FiPhone, FiBriefcase, FiCalendar, FiLogOut, FiArrowRight, FiUser, FiFileText, FiZap } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 960, margin: "0 auto" },

  // Hero
  heroCard: { borderRadius: 20, overflow: "hidden", marginBottom: 20, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", border: "1px solid #e8edf5" },
  heroBanner: { height: 100, background: "linear-gradient(135deg, #1e3a8a 0%, #4c1d95 60%, #0f172a 100%)", position: "relative", overflow: "hidden" },
  bannerPattern: { position: "absolute", inset: 0, opacity: 0.07, backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)", backgroundSize: "28px 28px" },
  heroBody: { background: "white", padding: "0 28px 24px" },
  avatarWrap: { position: "relative", display: "inline-block", marginTop: -48 },
  avatar: { width: 96, height: 96, borderRadius: 24, background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", fontSize: 38, fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center", border: "4px solid white", boxShadow: "0 4px 20px rgba(37,99,235,0.25)" },
  statusDot: { position: "absolute", bottom: 6, right: 6, width: 18, height: 18, borderRadius: "50%", background: "#22c55e", border: "3px solid white" },
  heroInfo: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12, marginTop: 12 },
  heroName: { margin: 0, fontSize: 24, fontWeight: 900, color: "#0f172a", letterSpacing: "-0.4px" },
  heroRole: { display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 600, color: "#16a34a", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 20, padding: "3px 10px", marginTop: 5 },
  editBtn: { display: "flex", alignItems: "center", gap: 7, padding: "9px 18px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 11, fontSize: 13, fontWeight: 700, cursor: "pointer", boxShadow: "0 3px 12px rgba(37,99,235,0.25)", flexShrink: 0 },

  // Stats
  statsGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginTop: 20, paddingTop: 20, borderTop: "1px solid #f1f5f9" },
  statCard: (bg, border, color) => ({ background: bg, border: `1px solid ${border}`, borderRadius: 14, padding: "16px 18px" }),
  statRow: { display: "flex", alignItems: "center", gap: 10 },
  statIcon: (bg) => ({ width: 38, height: 38, borderRadius: 10, background: bg, display: "flex", alignItems: "center", justifyContent: "center" }),
  statNum: (color) => ({ fontSize: 26, fontWeight: 900, color, lineHeight: 1 }),
  statLabel: { fontSize: 12, color: "#64748b", marginTop: 3, fontWeight: 500 },

  // Main grid
  grid: { display: "grid", gridTemplateColumns: "1fr 280px", gap: 16, alignItems: "start" },

  // Info card
  infoCard: { background: "white", borderRadius: 18, padding: "22px 24px", boxShadow: "0 2px 12px rgba(0,0,0,0.05)", border: "1px solid #e8edf5" },
  infoTitle: { fontSize: 13, fontWeight: 800, color: "#0f172a", textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 },
  infoTitleIcon: { width: 26, height: 26, borderRadius: 7, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" },
  infoItems: { display: "flex", flexDirection: "column", gap: 14 },
  infoItem: { display: "flex", alignItems: "flex-start", gap: 12 },
  infoIconWrap: (bg) => ({ width: 38, height: 38, borderRadius: 10, background: bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }),
  infoLabel: { fontSize: 11, color: "#94a3b8", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.3px" },
  infoValue: { fontSize: 14, fontWeight: 700, color: "#1e293b", marginTop: 2 },

  // Quick actions card
  actionsCard: { background: "white", borderRadius: 18, padding: "20px", boxShadow: "0 2px 12px rgba(0,0,0,0.05)", border: "1px solid #e8edf5", position: "sticky", top: 76 },
  actionsTitle: { fontSize: 13, fontWeight: 800, color: "#0f172a", textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 14 },
  actionsBtns: { display: "flex", flexDirection: "column", gap: 8 },
  actionBtn: (primary) => ({ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "11px 14px", borderRadius: 11, border: primary ? "none" : "1px solid #e2e8f0", background: primary ? "linear-gradient(135deg, #2563eb, #7c3aed)" : "white", color: primary ? "white" : "#374151", fontSize: 13, fontWeight: 700, cursor: "pointer", transition: "all 0.15s" }),
  logoutBtn: { width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "11px", borderRadius: 11, border: "1px solid #fecaca", background: "#fef2f2", color: "#ef4444", fontSize: 13, fontWeight: 700, cursor: "pointer", marginTop: 8 },

  // Activity card
  activityCard: { background: "white", borderRadius: 18, padding: "22px 24px", boxShadow: "0 2px 12px rgba(0,0,0,0.05)", border: "1px solid #e8edf5", marginTop: 16 },
  activityEmpty: { textAlign: "center", padding: "32px 0", color: "#94a3b8", fontSize: 14 },

  // Modal
  overlay: { position: "fixed", inset: 0, background: "rgba(15,23,42,0.55)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200, backdropFilter: "blur(4px)" },
  modal: { background: "white", borderRadius: 20, width: "90%", maxWidth: 460, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 24px 80px rgba(0,0,0,0.2)" },
  modalHeader: { background: "linear-gradient(135deg, #1e3a8a, #4c1d95)", padding: "20px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" },
  modalTitle: { margin: 0, fontSize: 18, fontWeight: 800, color: "white" },
  modalClose: { background: "none", border: "none", color: "rgba(255,255,255,0.7)", fontSize: 20, cursor: "pointer", lineHeight: 1 },
  modalBody: { padding: "24px" },
  modalLabel: { display: "block", fontSize: 11, fontWeight: 700, color: "#374151", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.4px" },
  modalInput: (focused) => ({ width: "100%", padding: "10px 12px", border: `2px solid ${focused ? "#2563eb" : "#e2e8f0"}`, borderRadius: 10, fontSize: 14, outline: "none", background: "#f8fafc", boxSizing: "border-box", marginBottom: 14, boxShadow: focused ? "0 0 0 3px rgba(37,99,235,0.1)" : "none" }),
  modalError: { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "10px 13px", color: "#991b1b", fontSize: 13, marginBottom: 14 },
  modalBtns: { display: "flex", gap: 10 },
  modalCancel: { flex: 1, padding: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 11, fontSize: 14, fontWeight: 600, color: "#374151", cursor: "pointer" },
  modalSave: (saving) => ({ flex: 2, padding: "11px", background: saving ? "#e2e8f0" : "linear-gradient(135deg, #2563eb, #7c3aed)", color: saving ? "#94a3b8" : "white", border: "none", borderRadius: 11, fontSize: 14, fontWeight: 700, cursor: saving ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }),

  // Loading
  loadingWrap: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)" },
  spinner: { width: 44, height: 44, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 14px" },
};

export default function RecruiterProfilePage({ setIsAuthenticated }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ full_name: "", phone_number: "", experience: "", age: "" });
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [focused, setFocused] = useState(null);

  useEffect(() => {
    api.get("/auth/profile").then(r => {
      setProfile(r.data);
      setEditForm({ full_name: r.data.full_name || "", phone_number: r.data.phone_number || "", experience: r.data.experience || "", age: r.data.age || "" });
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    if (typeof setIsAuthenticated === "function") setIsAuthenticated(false);
    navigate("/login");
  };

  const openEdit = () => {
    setEditForm({ full_name: profile?.full_name || "", phone_number: profile?.phone_number || "", experience: profile?.experience || "", age: profile?.age || "" });
    setUpdateError("");
    setIsEditing(true);
  };

  const handleSave = async () => {
    setIsUpdating(true); setUpdateError("");
    try {
      const r = await api.put("/auth/profile", {
        full_name: editForm.full_name || null,
        phone_number: editForm.phone_number || null,
        experience: editForm.experience || null,
        age: editForm.age ? parseInt(editForm.age) : null,
      });
      setProfile(r.data);
      setIsEditing(false);
    } catch (err) {
      setUpdateError(err.response?.data?.detail || "Failed to update profile.");
    } finally { setIsUpdating(false); }
  };

  if (loading) return (
    <div style={S.loadingWrap}>
      <div style={{ textAlign: "center" }}>
        <div style={S.spinner} />
        <div style={{ fontSize: 14, color: "#64748b" }}>Loading profile...</div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  const initial = (profile?.full_name || "R").charAt(0).toUpperCase();

  return (
    <div style={S.page}>
      <div style={S.inner}>

        {/* ── Hero card ── */}
        <div style={S.heroCard}>
          <div style={S.heroBanner}>
            <div style={S.bannerPattern} />
          </div>
          <div style={S.heroBody}>
            <div style={S.avatarWrap}>
              <div style={S.avatar}>{initial}</div>
              <div style={S.statusDot} />
            </div>
            <div style={S.heroInfo}>
              <div>
                <h1 style={S.heroName}>{profile?.full_name || "Recruiter"}</h1>
                <div style={S.heroRole}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
                  Recruiter Account
                </div>
              </div>
              <button style={S.editBtn} onClick={openEdit}>
                <FiEdit2 size={14} /> Edit Profile
              </button>
            </div>

            {/* Stats */}
            <div style={S.statsGrid}>
              <div style={S.statCard("#eff6ff", "#bfdbfe", "#2563eb")}>
                <div style={S.statRow}>
                  <div style={S.statIcon("#dbeafe")}><FiFileText color="#2563eb" size={18} /></div>
                  <div>
                    <div style={S.statNum("#2563eb")}>{profile?.resume_count || 0}</div>
                    <div style={S.statLabel}>Total Resumes</div>
                  </div>
                </div>
              </div>
              <div style={S.statCard("#f0fdf4", "#bbf7d0", "#16a34a")}>
                <div style={S.statRow}>
                  <div style={S.statIcon("#dcfce7")}><FiCalendar color="#16a34a" size={18} /></div>
                  <div>
                    <div style={S.statNum("#16a34a")}>{profile?.experience || "—"}</div>
                    <div style={S.statLabel}>Experience</div>
                  </div>
                </div>
              </div>
              <div style={S.statCard("#faf5ff", "#ddd6fe", "#7c3aed")}>
                <div style={S.statRow}>
                  <div style={S.statIcon("#ede9fe")}><FiBriefcase color="#7c3aed" size={18} /></div>
                  <div>
                    <div style={S.statNum("#7c3aed")}>Active</div>
                    <div style={S.statLabel}>Account Status</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Main grid ── */}
        <div style={S.grid}>
          <div>
            {/* Info card */}
            <div style={S.infoCard}>
              <div style={S.infoTitle}>
                <div style={S.infoTitleIcon}><FiUser size={13} color="white" /></div>
                Contact Information
              </div>
              <div style={S.infoItems}>
                {[
                  { icon: <FiMail size={16} color="#2563eb" />, bg: "#eff6ff", label: "Email Address", value: profile?.email || "Not provided" },
                  { icon: <FiPhone size={16} color="#16a34a" />, bg: "#f0fdf4", label: "Phone Number", value: profile?.phone_number || "Not provided" },
                  { icon: <FiBriefcase size={16} color="#7c3aed" />, bg: "#faf5ff", label: "Account Type", value: "Recruiter" },
                  profile?.age && { icon: <FiCalendar size={16} color="#d97706" />, bg: "#fffbeb", label: "Age", value: `${profile.age} years` },
                ].filter(Boolean).map(({ icon, bg, label, value }) => (
                  <div key={label} style={S.infoItem}>
                    <div style={S.infoIconWrap(bg)}>{icon}</div>
                    <div>
                      <div style={S.infoLabel}>{label}</div>
                      <div style={S.infoValue}>{value}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity card */}
            <div style={S.activityCard}>
              <div style={S.infoTitle}>
                <div style={S.infoTitleIcon}><FiFileText size={13} color="white" /></div>
                Recent Activity
              </div>
              <div style={S.activityEmpty}>Resume activity will appear here</div>
            </div>
          </div>

          {/* Quick actions */}
          <div style={S.actionsCard}>
            <div style={S.actionsTitle}>Quick Actions</div>
            <div style={S.actionsBtns}>
              {[
                { label: "View All Resumes", path: "/dashboard", primary: true, icon: <FiFileText size={14} /> },
                { label: "Smart Upload", path: "/smart-upload", primary: false, icon: <FiZap size={14} /> },
                { label: "Advanced Search", path: "/advanced-search", primary: false, icon: null },
                { label: "Bulk Upload", path: "/bulk-upload", primary: false, icon: null },
              ].map(({ label, path, primary }) => (
                <button key={path} style={S.actionBtn(primary)} onClick={() => navigate(path)}
                  onMouseEnter={e => { if (!primary) e.currentTarget.style.background = "#f8fafc"; }}
                  onMouseLeave={e => { if (!primary) e.currentTarget.style.background = "white"; }}
                >
                  <span>{label}</span>
                  <FiArrowRight size={14} />
                </button>
              ))}
              <button style={S.logoutBtn} onClick={handleLogout} disabled={isLoggingOut}
                onMouseEnter={e => e.currentTarget.style.background = "#fee2e2"}
                onMouseLeave={e => e.currentTarget.style.background = "#fef2f2"}
              >
                {isLoggingOut ? (
                  <><div style={{ width: 14, height: 14, border: "2px solid #fca5a5", borderTop: "2px solid #ef4444", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />Logging out...</>
                ) : (
                  <><FiLogOut size={14} />Logout</>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Edit Modal ── */}
      {isEditing && (
        <div style={S.overlay}>
          <div style={S.modal}>
            <div style={S.modalHeader}>
              <h2 style={S.modalTitle}>✏️ Edit Profile</h2>
              <button style={S.modalClose} onClick={() => setIsEditing(false)}>✕</button>
            </div>
            <div style={S.modalBody}>
              {updateError && <div style={S.modalError}>⚠️ {updateError}</div>}

              {[
                { key: "full_name", label: "Full Name", type: "text", placeholder: "Your full name" },
                { key: "phone_number", label: "Phone Number", type: "tel", placeholder: "+91-9876543210" },
                { key: "experience", label: "Experience", type: "text", placeholder: "e.g. 5 years in HR" },
                { key: "age", label: "Age", type: "number", placeholder: "Your age", min: 18, max: 100 },
              ].map(({ key, label, type, placeholder, ...rest }) => (
                <div key={key}>
                  <label style={S.modalLabel}>{label}</label>
                  <input
                    type={type}
                    name={key}
                    value={editForm[key]}
                    onChange={e => setEditForm(p => ({ ...p, [key]: e.target.value }))}
                    onFocus={() => setFocused(key)}
                    onBlur={() => setFocused(null)}
                    style={S.modalInput(focused === key)}
                    placeholder={placeholder}
                    {...rest}
                  />
                </div>
              ))}

              <div style={S.modalBtns}>
                <button style={S.modalCancel} onClick={() => setIsEditing(false)} disabled={isUpdating}>Cancel</button>
                <button style={S.modalSave(isUpdating)} onClick={handleSave} disabled={isUpdating}>
                  {isUpdating ? (
                    <><div style={{ width: 15, height: 15, border: "2px solid rgba(148,163,184,0.3)", borderTop: "2px solid #94a3b8", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />Saving...</>
                  ) : "💾 Save Changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}