import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiSave, FiUser, FiMail, FiPhone, FiMapPin, FiHome, FiFileText } from 'react-icons/fi';
import { getResume, updateResume } from '../services/api';

const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 620, margin: "0 auto" },

  backBtn: { display: "inline-flex", alignItems: "center", gap: 8, padding: "9px 16px", background: "white", border: "1px solid #e2e8f0", borderRadius: 12, color: "#374151", fontSize: 13, fontWeight: 600, cursor: "pointer", marginBottom: 20, boxShadow: "0 2px 8px rgba(0,0,0,0.05)" },

  card: { background: "white", borderRadius: 20, boxShadow: "0 4px 24px rgba(0,0,0,0.07)", border: "1px solid #e8edf5", overflow: "hidden" },

  cardHeader: { background: "linear-gradient(135deg, #1e3a8a, #4c1d95)", padding: "24px 28px" },
  headerRow: { display: "flex", alignItems: "center", gap: 14 },
  headerIcon: { width: 48, height: 48, borderRadius: 14, background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center" },
  headerTitle: { margin: 0, fontSize: 22, fontWeight: 800, color: "white", letterSpacing: "-0.3px" },
  headerSub: { margin: "4px 0 0", fontSize: 13, color: "rgba(255,255,255,0.65)" },

  form: { padding: "28px 32px" },
  fieldGroup: { marginBottom: 20 },
  label: { display: "block", fontSize: 12, fontWeight: 700, color: "#374151", marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.4px" },
  inputWrap: { position: "relative" },
  inputIcon: (focused, hasError) => ({
    position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)",
    color: hasError ? "#ef4444" : focused ? "#2563eb" : "#94a3b8",
    pointerEvents: "none", transition: "color 0.15s",
  }),
  input: (focused, hasError) => ({
    width: "100%", paddingLeft: 44, paddingRight: 16, paddingTop: 11, paddingBottom: 11,
    border: `2px solid ${hasError ? "#ef4444" : focused ? "#2563eb" : "#e2e8f0"}`,
    borderRadius: 12, fontSize: 14, outline: "none", background: "#f8fafc",
    boxSizing: "border-box", transition: "all 0.15s",
    boxShadow: focused && !hasError ? "0 0 0 3px rgba(37,99,235,0.1)" : hasError ? "0 0 0 3px rgba(239,68,68,0.1)" : "none",
  }),
  textarea: (focused) => ({
    width: "100%", paddingLeft: 44, paddingRight: 16, paddingTop: 12, paddingBottom: 12,
    border: `2px solid ${focused ? "#2563eb" : "#e2e8f0"}`,
    borderRadius: 12, fontSize: 14, outline: "none", background: "#f8fafc",
    boxSizing: "border-box", transition: "all 0.15s", resize: "none",
    boxShadow: focused ? "0 0 0 3px rgba(37,99,235,0.1)" : "none",
  }),
  textareaIcon: (focused) => ({
    position: "absolute", left: 14, top: 13,
    color: focused ? "#2563eb" : "#94a3b8", pointerEvents: "none", transition: "color 0.15s",
  }),
  fieldError: { fontSize: 12, color: "#ef4444", marginTop: 5, fontWeight: 500 },

  divider: { height: 1, background: "#f1f5f9", margin: "24px 0" },

  alertBox: (type) => ({
    display: "flex", alignItems: "flex-start", gap: 10, padding: "12px 16px", borderRadius: 12, marginBottom: 20,
    background: type === "error" ? "#fef2f2" : "#f0fdf4",
    border: `1px solid ${type === "error" ? "#fecaca" : "#bbf7d0"}`,
    color: type === "error" ? "#991b1b" : "#166534",
    fontSize: 13, fontWeight: 500,
  }),

  btnRow: { display: "flex", gap: 12, flexWrap: "wrap" },
  cancelBtn: { flex: 1, padding: "12px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 14, fontWeight: 600, color: "#374151", cursor: "pointer" },
  saveBtn: (saving) => ({
    flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "12px",
    background: saving ? "#e2e8f0" : "linear-gradient(135deg, #2563eb, #7c3aed)",
    color: saving ? "#94a3b8" : "white", border: "none", borderRadius: 12,
    fontSize: 14, fontWeight: 700, cursor: saving ? "not-allowed" : "pointer",
    boxShadow: saving ? "none" : "0 4px 14px rgba(37,99,235,0.3)",
  }),

  tipCard: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 14, padding: "14px 18px", marginTop: 16, display: "flex", gap: 10, alignItems: "flex-start", fontSize: 13, color: "#166534" },

  loadingWrap: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)" },
  spinner: { width: 44, height: 44, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 14px" },
};

const formatError = (err) => {
  if (!err) return '';
  if (typeof err === 'string') return err;
  if (Array.isArray(err)) return err.map(e => e?.msg || String(e)).join(', ');
  if (err?.detail) return formatError(err.detail);
  return err?.message || err?.msg || JSON.stringify(err);
};

const FIELDS = [
  { key: "name",          label: "Full Name",       Icon: FiUser,     type: "text",  placeholder: "Candidate's full name" },
  { key: "email",         label: "Email Address",   Icon: FiMail,     type: "email", placeholder: "email@example.com" },
  { key: "mobile_number", label: "Phone Number",    Icon: FiPhone,    type: "text",  placeholder: "+91-9876543210" },
  { key: "location",      label: "Location",        Icon: FiMapPin,   type: "text",  placeholder: "City, State" },
];

function EditResumePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [focused, setFocused] = useState(null);

  const [formData, setFormData] = useState({ name: '', email: '', mobile_number: '', location: '', address: '' });

  useEffect(() => { fetchResume(); }, [id]);

  const fetchResume = async () => {
    try {
      setLoading(true);
      const data = await getResume(id);
      setFormData({
        name: data.name || '',
        email: data.email || '',
        mobile_number: data.mobile_number || '',
        location: data.location || '',
        address: data.parsed_data?.address || '',
      });
      setError('');
    } catch {
      setError('Failed to load resume.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(p => ({ ...p, [e.target.name]: e.target.value }));
    setFieldErrors(p => ({ ...p, [e.target.name]: undefined }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true); setError(''); setSuccess(false);

    const errors = {};
    if (formData.email && !/^\S+@\S+\.\S+$/.test(formData.email.trim())) {
      errors.email = 'Enter a valid email address';
    }
    if (Object.keys(errors).length) {
      setFieldErrors(errors);
      setError('Please fix the highlighted fields.');
      setSaving(false);
      return;
    }

    try {
      await updateResume(id, formData);
      setSuccess(true);
      setTimeout(() => navigate(`/resume/${id}`), 1600);
    } catch (err) {
      const resp = err.response?.data ?? err;
      setError(formatError(resp?.detail || resp) || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div style={S.loadingWrap}>
      <div style={{ textAlign: "center" }}>
        <div style={S.spinner} />
        <div style={{ fontSize: 14, color: "#64748b" }}>Loading resume...</div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return (
    <div style={S.page}>
      <div style={S.inner}>
        <button style={S.backBtn} onClick={() => navigate(`/resume/${id}`)}>
          <FiArrowLeft size={15} /> Back to Resume
        </button>

        <div style={S.card}>
          {/* Header */}
          <div style={S.cardHeader}>
            <div style={S.headerRow}>
              <div style={S.headerIcon}><FiFileText color="white" size={22} /></div>
              <div>
                <h2 style={S.headerTitle}>Edit Resume</h2>
                <p style={S.headerSub}>Update candidate information</p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form style={S.form} onSubmit={handleSubmit}>
            {FIELDS.map(({ key, label, Icon, type, placeholder }) => (
              <div key={key} style={S.fieldGroup}>
                <label style={S.label}>{label}</label>
                <div style={S.inputWrap}>
                  <div style={S.inputIcon(focused === key, !!fieldErrors[key])}>
                    <Icon size={17} />
                  </div>
                  <input
                    type={type}
                    name={key}
                    value={formData[key]}
                    onChange={handleChange}
                    onFocus={() => setFocused(key)}
                    onBlur={() => setFocused(null)}
                    style={S.input(focused === key, !!fieldErrors[key])}
                    placeholder={placeholder}
                  />
                </div>
                {fieldErrors[key] && <div style={S.fieldError}>⚠ {fieldErrors[key]}</div>}
              </div>
            ))}

            {/* Address textarea */}
            <div style={S.fieldGroup}>
              <label style={S.label}>Full Address</label>
              <div style={S.inputWrap}>
                <div style={S.textareaIcon(focused === "address")}>
                  <FiHome size={17} />
                </div>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  onFocus={() => setFocused("address")}
                  onBlur={() => setFocused(null)}
                  rows={4}
                  style={S.textarea(focused === "address")}
                  placeholder="Enter full address (optional)"
                />
              </div>
            </div>

            <div style={S.divider} />

            {/* Error */}
            {error && (
              <div style={S.alertBox("error")}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>⚠️</span>
                {formatError(error)}
              </div>
            )}

            {/* Success */}
            {success && (
              <div style={S.alertBox("success")}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>✅</span>
                Changes saved! Redirecting to resume view...
              </div>
            )}

            {/* Buttons */}
            <div style={S.btnRow}>
              <button type="button" style={S.cancelBtn} onClick={() => navigate(`/resume/${id}`)} disabled={saving}>
                Cancel
              </button>
              <button type="submit" style={S.saveBtn(saving)} disabled={saving}>
                {saving ? (
                  <>
                    <div style={{ width: 16, height: 16, border: "2px solid rgba(148,163,184,0.3)", borderTop: "2px solid #94a3b8", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                    Saving...
                  </>
                ) : (
                  <><FiSave size={16} /> Save Changes</>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Tip */}
        <div style={S.tipCard}>
          <span style={{ fontSize: 18, flexShrink: 0 }}>💡</span>
          <span>All changes are saved to the Zapplic database and can be updated at any time. Only the fields above are editable here — for deeper edits, use the full resume editor.</span>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default EditResumePage;