import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiEye, FiEdit, FiX, FiSave, FiZap, FiUpload } from "react-icons/fi";
import api from "../services/api";

// ─────────────────────────────────────────────
// DESIGN TOKENS
// ─────────────────────────────────────────────
const T = {
  blue:   "#2563eb",
  purple: "#7c3aed",
  green:  "#16a34a",
  gray:   "#6b7280",
  grad:   "linear-gradient(135deg, #2563eb, #7c3aed)",
};

const qualityConfig = (q) => {
  const map = {
    high:    { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0", dot: "#22c55e", label: "High" },
    good:    { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0", dot: "#22c55e", label: "Good" },
    medium:  { bg: "#fffbeb", text: "#d97706", border: "#fde68a", dot: "#f59e0b", label: "Medium" },
    partial: { bg: "#fffbeb", text: "#d97706", border: "#fde68a", dot: "#f59e0b", label: "Partial" },
    low:     { bg: "#fef2f2", text: "#dc2626", border: "#fecaca", dot: "#ef4444", label: "Low" },
    poor:    { bg: "#fef2f2", text: "#dc2626", border: "#fecaca", dot: "#ef4444", label: "Poor" },
  };
  return map[q?.toLowerCase()] || { bg: "#f8fafc", text: "#64748b", border: "#e2e8f0", dot: "#94a3b8", label: q || "Unknown" };
};


// ─────────────────────────────────────────────
// VERSION CONFLICT MODAL
// ─────────────────────────────────────────────
export function VersionConflictModal({ conflict, file, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState(null);
  const existing = conflict.existing_resume;

  const handleAction = async (selectedAction) => {
    setAction(selectedAction);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const params = new URLSearchParams({ action: selectedAction });
      if (existing?.id && selectedAction !== "skip") params.append("existing_resume_id", existing.id);
      const res = await api.post(`/resumes/upload-with-action?${params}`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      onSuccess(res.data);
    } catch (err) {
      console.error("Upload action failed:", err);
      alert("Upload failed. Please try again.");
    } finally { setLoading(false); }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(4px)" }}>
      <div style={{ background: "white", borderRadius: 20, width: "90%", maxWidth: 600, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 24px 80px rgba(0,0,0,0.2)", border: "1px solid #e8edf5" }}>
        {/* Header */}
        <div style={{ background: "linear-gradient(135deg, #1e3a8a, #4c1d95)", padding: "20px 24px", display: "flex", alignItems: "center", gap: 12, borderRadius: "20px 20px 0 0" }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>📋</div>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: "white" }}>Resume Already Exists</h3>
            <p style={{ margin: "3px 0 0", fontSize: 13, color: "rgba(255,255,255,0.65)" }}>A resume for this candidate was found in the system.</p>
          </div>
        </div>

        <div style={{ padding: "24px" }}>
          {/* Comparison */}
          <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24 }}>
            <div style={{ flex: 1, border: "2px solid #e2e8f0", borderRadius: 14, padding: "14px 16px", background: "#f8fafc" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 6 }}>📁 Existing Resume</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#0f172a", marginBottom: 6 }}>{existing?.name || "Unknown"}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 3 }}>📅 {existing?.uploaded_at ? new Date(existing.uploaded_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "Unknown date"}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 3 }}>📄 {existing?.filename || "Unknown file"}</div>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4, marginTop: 6, background: "#64748b", color: "white", padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700 }}>v{existing?.version || 1}</span>
            </div>
            <div style={{ fontSize: 20, color: "#94a3b8", flexShrink: 0 }}>→</div>
            <div style={{ flex: 1, border: `2px solid ${T.blue}`, borderRadius: 14, padding: "14px 16px", background: "#eff6ff" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.blue, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 6 }}>✨ New Upload</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#0f172a", marginBottom: 6 }}>{existing?.name || "Same Candidate"}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 3 }}>📅 Today: {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 3 }}>📄 {file?.name || "New file"}</div>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4, marginTop: 6, background: T.blue, color: "white", padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700 }}>v{(existing?.version || 1) + 1}</span>
            </div>
          </div>

          <div style={{ fontSize: 13, fontWeight: 700, color: "#374151", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.4px" }}>What would you like to do?</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
            <ActionCard icon="🔄" title="Replace with New Version" description="Archive the old resume and save this as the latest version." color={T.blue} selected={action === "replace"} loading={loading && action === "replace"} onClick={() => handleAction("replace")} />
            <ActionCard icon="📚" title="Keep Both Versions" description="Save new resume alongside the old one. New one marked as latest." color={T.green} selected={action === "keep_both"} loading={loading && action === "keep_both"} onClick={() => handleAction("keep_both")} />
            <ActionCard icon="⏭️" title="Skip Upload" description="Keep the existing resume as-is. Discard this new upload." color={T.gray} selected={action === "skip"} loading={loading && action === "skip"} onClick={() => handleAction("skip")} />
          </div>
          <button onClick={onClose} disabled={loading} style={{ width: "100%", padding: "11px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 14, cursor: "pointer", color: "#64748b", fontWeight: 600 }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

function ActionCard({ icon, title, description, color, selected, loading, onClick }) {
  return (
    <button onClick={onClick} disabled={loading}
      style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "14px 16px", borderRadius: 12, border: `2px solid ${selected ? color : "#e2e8f0"}`, background: selected ? `${color}10` : "white", cursor: loading ? "not-allowed" : "pointer", textAlign: "left", width: "100%", transition: "all 0.15s", opacity: loading ? 0.7 : 1 }}
    >
      <span style={{ fontSize: 22, flexShrink: 0, marginTop: 2 }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color, marginBottom: 3 }}>{loading ? "Processing..." : title}</div>
        <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.45 }}>{description}</div>
      </div>
      {selected && !loading && <div style={{ marginLeft: "auto", color, fontSize: 18, flexShrink: 0 }}>✓</div>}
    </button>
  );
}


// ─────────────────────────────────────────────
// POST-UPLOAD RESUME PREVIEW PANEL
// ─────────────────────────────────────────────
function ResumePreviewPanel({ resumeData, onClose, onSaved }) {
  const navigate = useNavigate();
  const resumeId = resumeData?.resume?.id;
  const resume = resumeData?.resume || {};

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [focusedField, setFocusedField] = useState(null);

  const [formData, setFormData] = useState({
    name: resume.name || "",
    email: resume.email || "",
    mobile_number: resume.mobile_number || "",
    location: resume.location || "",
  });

  const handleChange = (e) => { setFormData((p) => ({ ...p, [e.target.name]: e.target.value })); setSaveError(""); };

  const handleSave = async () => {
    if (!resumeId) return;
    setSaving(true); setSaveError("");
    try {
      await api.put(`/resumes/${resumeId}`, formData);
      setSaveSuccess(true); setEditing(false);
      if (onSaved) onSaved({ ...resume, ...formData });
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setSaveError(typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : "Failed to save changes.");
    } finally { setSaving(false); }
  };

  const qc = qualityConfig(resume.parsing_quality);
  const hasMissing = !resume.email || !resume.mobile_number;

  const FIELDS = [
    { key: "name",          label: "Full Name", type: "text",  placeholder: "Candidate's full name" },
    { key: "email",         label: "Email",     type: "email", placeholder: "email@example.com" },
    { key: "mobile_number", label: "Phone",     type: "text",  placeholder: "+91-9876543210" },
    { key: "location",      label: "Location",  type: "text",  placeholder: "City, State" },
  ];

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1100, backdropFilter: "blur(4px)" }}>
      <div style={{ background: "white", borderRadius: 20, width: "90%", maxWidth: 560, maxHeight: "92vh", overflowY: "auto", boxShadow: "0 24px 80px rgba(0,0,0,0.2)", border: "1px solid #e8edf5" }}>

        {/* Header */}
        <div style={{ padding: "20px 24px 0", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 20, padding: "3px 10px", fontSize: 12, fontWeight: 600, color: "#16a34a", marginBottom: 4 }}>✅ Upload Successful</div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: "#0f172a" }}>Resume Preview</h2>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "1px solid #e2e8f0", borderRadius: 8, width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "#94a3b8" }}>
            <FiX size={16} />
          </button>
        </div>

        {/* Avatar */}
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start", padding: "18px 24px", borderBottom: "1px solid #f1f5f9" }}>
          <div style={{ width: 62, height: 62, borderRadius: 16, background: T.grad, color: "white", fontSize: 26, fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            {(formData.name || "?").charAt(0).toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: "#0f172a", marginBottom: 4 }}>{formData.name || "Unknown Candidate"}</div>
            <div style={{ fontSize: 13, color: "#64748b" }}>{formData.email}{formData.location && ` · ${formData.location}`}</div>
            <div style={{ display: "flex", gap: 7, marginTop: 8, flexWrap: "wrap" }}>
              <span style={{ fontSize: 11, fontWeight: 700, background: "#eff6ff", color: T.blue, border: "1px solid #bfdbfe", borderRadius: 20, padding: "2px 10px" }}>v{resume.version || 1}</span>
              <span style={{ fontSize: 11, fontWeight: 700, background: qc.bg, color: qc.text, border: `1px solid ${qc.border}`, borderRadius: 20, padding: "2px 10px", display: "inline-flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: qc.dot, display: "inline-block" }} />
                {qc.label} quality
              </span>
            </div>
          </div>
        </div>

        {/* Fields */}
        <div style={{ padding: "18px 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "#374151", textTransform: "uppercase", letterSpacing: "0.5px" }}>Parsed Information</span>
            {!editing
              ? <button onClick={() => setEditing(true)} style={{ fontSize: 13, fontWeight: 600, color: T.blue, background: "none", border: "1px solid #bfdbfe", borderRadius: 8, padding: "5px 12px", cursor: "pointer" }}>✏️ Quick Edit</button>
              : <button onClick={() => { setEditing(false); setSaveError(""); }} style={{ fontSize: 13, fontWeight: 600, color: "#64748b", background: "none", border: "1px solid #e2e8f0", borderRadius: 8, padding: "5px 12px", cursor: "pointer" }}>✕ Cancel</button>
            }
          </div>

          {!editing ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {FIELDS.map((f) => (
                <div key={f.key} style={{ background: "#f8fafc", border: "1px solid #f1f5f9", borderRadius: 10, padding: "10px 13px" }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>{f.label}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", wordBreak: "break-word" }}>
                    {formData[f.key] || <span style={{ color: "#cbd5e1", fontStyle: "italic", fontSize: 13 }}>Not detected</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {FIELDS.map((f) => (
                <div key={f.key}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#374151", textTransform: "uppercase", letterSpacing: "0.3px", marginBottom: 5 }}>{f.label}</label>
                  <input
                    type={f.type} name={f.key} value={formData[f.key]}
                    onChange={handleChange} onFocus={() => setFocusedField(f.key)} onBlur={() => setFocusedField(null)}
                    placeholder={f.placeholder}
                    style={{ width: "100%", padding: "9px 12px", border: `2px solid ${focusedField === f.key ? T.blue : "#e2e8f0"}`, borderRadius: 9, fontSize: 14, outline: "none", boxSizing: "border-box", background: "#f8fafc", transition: "all 0.15s", boxShadow: focusedField === f.key ? "0 0 0 3px rgba(37,99,235,0.1)" : "none" }}
                  />
                </div>
              ))}
              {saveError && <div style={{ gridColumn: "1 / -1", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 9, padding: "9px 12px", fontSize: 13, color: "#991b1b", fontWeight: 500 }}>⚠️ {saveError}</div>}
              <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
                <button onClick={handleSave} disabled={saving} style={{ padding: "9px 20px", background: saving ? "#e2e8f0" : T.grad, color: saving ? "#94a3b8" : "white", border: "none", borderRadius: 9, fontSize: 14, fontWeight: 700, cursor: saving ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: 7 }}>
                  <FiSave size={14} />{saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          )}
          {saveSuccess && <div style={{ marginTop: 10, background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 9, padding: "8px 13px", fontSize: 13, color: "#16a34a", fontWeight: 600 }}>✅ Changes saved successfully!</div>}
        </div>

        {/* Missing data warning */}
        {hasMissing && (
          <div style={{ margin: "0 24px 16px", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 12, padding: "12px 14px", display: "flex", gap: 10, alignItems: "flex-start" }}>
            <span style={{ fontSize: 16, flexShrink: 0 }}>⚠️</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#92400e", marginBottom: 2 }}>Some fields weren't detected</div>
              <div style={{ fontSize: 12, color: "#a16207", lineHeight: 1.5 }}>
                {[!resume.email && "Email", !resume.mobile_number && "Phone number"].filter(Boolean).join(" and ")} could not be parsed. Use Quick Edit above to fill them in.
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 8, padding: "16px 24px 20px", borderTop: "1px solid #f1f5f9" }}>
          <button onClick={() => resumeId && navigate(`/resume/${resumeId}`)} style={{ flex: 1, padding: "10px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 10, fontSize: 13, fontWeight: 700, color: T.blue, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
            <FiEye size={14} /> View Full
          </button>
          <button onClick={() => resumeId && navigate(`/resume/${resumeId}/edit`)} style={{ flex: 1, padding: "10px", background: "#faf5ff", border: "1px solid #ddd6fe", borderRadius: 10, fontSize: 13, fontWeight: 700, color: T.purple, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
            <FiEdit size={14} /> Edit Detail
          </button>
          <button onClick={onClose} style={{ flex: 1, padding: "10px", background: T.grad, border: "none", borderRadius: 10, fontSize: 13, fontWeight: 700, color: "white", cursor: "pointer" }}>✓ Done</button>
        </div>
      </div>
    </div>
  );
}


// ─────────────────────────────────────────────
// SMART UPLOAD
// ─────────────────────────────────────────────
export function SmartUpload({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [checking, setChecking] = useState(false);
  const [conflict, setConflict] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (selected) => {
    if (!selected) return;
    setFile(selected); setConflict(null); setUploadedData(null); setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelect(dropped);
  };

  const handleUpload = async () => {
    if (!file) return;
    setChecking(true); setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const checkRes = await api.post(`/resumes/check-version`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      const status = checkRes.data.status;
      if (status === "exact_duplicate") {
        setError({ type: "duplicate", message: checkRes.data.message, existing: checkRes.data.existing_resume });
      } else if (status === "new_version") {
        setConflict(checkRes.data);
      } else {
        await uploadNew(file);
      }
    } catch {
      setError({ type: "error", message: "Upload check failed. Please try again." });
    } finally { setChecking(false); }
  };

  const uploadNew = async (fileToUpload) => {
    const formData = new FormData();
    formData.append("file", fileToUpload);
    const res = await api.post(`/resumes/upload-with-action?action=new`, formData, { headers: { "Content-Type": "multipart/form-data" } });
    setUploadedData(res.data); setFile(null);
    if (onUploadComplete) onUploadComplete(res.data);
  };

  const handleVersionSuccess = (data) => {
    setConflict(null); setUploadedData(data); setFile(null);
    if (onUploadComplete) onUploadComplete(data);
  };

  const resetUpload = () => { setFile(null); setError(null); setUploadedData(null); setConflict(null); };
  const getExt = (f) => f?.name?.split(".").pop()?.toLowerCase() || "";
  const ext = getExt(file);

  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "32px 16px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 28 }}>
        <div style={{ width: 52, height: 52, borderRadius: 14, background: T.grad, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <FiZap color="white" size={24} />
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" }}>Smart Upload</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>AI-powered parsing with automatic duplicate detection</p>
        </div>
      </div>

      {/* Card */}
      <div style={{ background: "white", border: "1px solid #e8edf5", borderRadius: 20, padding: 24, boxShadow: "0 4px 24px rgba(0,0,0,0.07)" }}>
        {/* Dropzone */}
        <div
          style={{ border: `2px dashed ${dragOver ? T.blue : file ? "#16a34a" : "#d1d5db"}`, borderRadius: 14, background: dragOver ? "#eff6ff" : file ? "#f0fdf4" : "#fafafa", transition: "all 0.2s", marginBottom: 16, cursor: "pointer" }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input type="file" accept=".pdf,.docx" onChange={(e) => handleFileSelect(e.target.files[0])} style={{ display: "none" }} id="resume-upload" />
          <label htmlFor="resume-upload" style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 24px", cursor: "pointer", gap: 8, userSelect: "none" }}>
            {file ? (
              <>
                <div style={{ width: 44, height: 44, borderRadius: 11, background: ext === "pdf" ? "#fef2f2" : "#eff6ff", color: ext === "pdf" ? "#dc2626" : T.blue, fontSize: 12, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", textTransform: "uppercase", marginBottom: 4 }}>{ext}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#1e293b", textAlign: "center" }}>{file.name}</div>
                <div style={{ fontSize: 12, color: "#94a3b8" }}>{(file.size / 1024).toFixed(0)} KB · {ext.toUpperCase()}</div>
                <div style={{ fontSize: 12, color: T.blue, marginTop: 4 }}>Click to change file</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 42, marginBottom: 4 }}>{dragOver ? "🎯" : "☁️"}</div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#374151" }}>{dragOver ? "Drop it here!" : "Drag & drop or click to upload"}</div>
                <div style={{ fontSize: 12, color: "#9ca3af" }}>PDF or DOCX · Max 10MB</div>
              </>
            )}
          </label>
        </div>

        {/* Upload button */}
        {file && !checking && (
          <button onClick={handleUpload} style={{ width: "100%", padding: "13px", background: T.grad, color: "white", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <FiUpload size={16} /> Upload & Analyse
          </button>
        )}

        {/* Checking */}
        {checking && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, padding: "14px 0" }}>
            <div style={{ width: 20, height: 20, border: "3px solid #e2e8f0", borderTop: `3px solid ${T.blue}`, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
            <span style={{ fontSize: 14, color: "#64748b", fontWeight: 500 }}>Analysing resume...</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: "16px 18px", marginTop: 4 }}>
            {error.type === "duplicate" ? (
              <>
                <div style={{ fontSize: 14, fontWeight: 800, color: "#991b1b", marginBottom: 4 }}>⚠️ Duplicate Resume Detected</div>
                <div style={{ fontSize: 13, color: "#b91c1c", marginBottom: 4 }}>{error.message}</div>
                {error.existing && <div style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>Originally uploaded as: <strong>{error.existing.filename}</strong></div>}
                <button onClick={resetUpload} style={{ padding: "7px 16px", background: "white", border: "1px solid #fca5a5", borderRadius: 9, fontSize: 13, color: "#991b1b", cursor: "pointer", fontWeight: 600 }}>Try Another File</button>
              </>
            ) : (
              <>
                <div style={{ fontSize: 14, fontWeight: 800, color: "#991b1b", marginBottom: 4 }}>❌ Upload Failed</div>
                <div style={{ fontSize: 13, color: "#b91c1c", marginBottom: 12 }}>{error.message}</div>
                <button onClick={resetUpload} style={{ padding: "7px 16px", background: "white", border: "1px solid #fca5a5", borderRadius: 9, fontSize: 13, color: "#991b1b", cursor: "pointer", fontWeight: 600 }}>Try Again</button>
              </>
            )}
          </div>
        )}

        {/* Feature hints */}
        {!file && !error && (
          <div style={{ display: "flex", justifyContent: "center", gap: 20, marginTop: 14 }}>
            {[{ icon: "🔍", text: "Duplicate detection" }, { icon: "🤖", text: "AI parsing" }, { icon: "📋", text: "Version control" }].map((h) => (
              <div key={h.text} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#94a3b8" }}>
                <span>{h.icon}</span><span>{h.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Conflict modal */}
      {conflict && <VersionConflictModal conflict={conflict} file={file} onClose={() => setConflict(null)} onSuccess={handleVersionSuccess} />}

      {/* Preview panel */}
      {uploadedData?.resume && <ResumePreviewPanel resumeData={uploadedData} onClose={() => setUploadedData(null)} onSaved={() => {}} />}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default SmartUpload;