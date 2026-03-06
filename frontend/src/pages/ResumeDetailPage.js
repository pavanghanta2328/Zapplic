import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiEdit, FiMail, FiPhone, FiMapPin, FiFileText, FiBriefcase, FiAward, FiCode, FiBook, FiUser } from 'react-icons/fi';
import { getResume } from '../services/api';

const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 1000, margin: "0 auto" },

  // Nav bar
  topNav: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 },
  backBtn: { display: "flex", alignItems: "center", gap: 8, padding: "9px 16px", background: "white", border: "1px solid #e2e8f0", borderRadius: 12, color: "#374151", fontSize: 13, fontWeight: 600, cursor: "pointer", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" },
  editBtn: { display: "flex", alignItems: "center", gap: 8, padding: "10px 22px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 12, fontSize: 14, fontWeight: 700, cursor: "pointer", boxShadow: "0 4px 14px rgba(37,99,235,0.3)" },

  // Hero card
  hero: { background: "linear-gradient(135deg, #1e3a8a 0%, #4c1d95 100%)", borderRadius: 20, padding: "28px 32px", marginBottom: 20, position: "relative", overflow: "hidden" },
  heroOverlay: { position: "absolute", inset: 0, background: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='30'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")", pointerEvents: "none" },
  heroContent: { position: "relative", zIndex: 1 },
  heroTop: { display: "flex", alignItems: "flex-start", gap: 20, flexWrap: "wrap" },
  heroAvatar: { width: 80, height: 80, borderRadius: 20, background: "rgba(255,255,255,0.15)", backdropFilter: "blur(8px)", border: "2px solid rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 34, fontWeight: 900, color: "white", flexShrink: 0 },
  heroName: { margin: 0, fontSize: 28, fontWeight: 900, color: "white", letterSpacing: "-0.5px", marginBottom: 10 },
  heroContacts: { display: "flex", flexWrap: "wrap", gap: 10 },
  heroPill: { display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 14px", background: "rgba(255,255,255,0.12)", backdropFilter: "blur(4px)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 20, color: "rgba(255,255,255,0.9)", fontSize: 13 },
  heroBadges: { display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" },
  heroBadge: (bg, color, border) => ({ display: "inline-flex", alignItems: "center", gap: 5, padding: "4px 12px", background: bg, border: `1px solid ${border}`, borderRadius: 20, color, fontSize: 12, fontWeight: 700 }),

  // Section grid
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 },
  gridFull: { marginBottom: 16 },

  // Section card
  section: { background: "white", border: "1px solid #e8edf5", borderRadius: 16, overflow: "hidden", boxShadow: "0 2px 12px rgba(0,0,0,0.04)" },
  sectionHeader: { display: "flex", alignItems: "center", gap: 10, padding: "14px 18px", borderBottom: "1px solid #f1f5f9", background: "#f8fafc" },
  sectionIcon: { width: 32, height: 32, borderRadius: 9, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  sectionTitle: { fontSize: 13, fontWeight: 800, color: "#0f172a", textTransform: "uppercase", letterSpacing: "0.4px" },
  sectionBody: { padding: "16px 18px", fontSize: 14, color: "#374151", lineHeight: 1.65, whiteSpace: "pre-wrap" },
  sectionEmpty: { padding: "16px 18px", fontSize: 13, color: "#cbd5e1", fontStyle: "italic" },

  // Array items (experience etc)
  itemCard: { background: "#f8fafc", border: "1px solid #f1f5f9", borderRadius: 10, padding: "12px 14px", marginBottom: 8 },

  // Metadata grid
  metaCard: { background: "white", border: "1px solid #e8edf5", borderRadius: 16, padding: "22px 24px", marginBottom: 16, boxShadow: "0 2px 12px rgba(0,0,0,0.04)" },
  metaTitle: { fontSize: 13, fontWeight: 800, color: "#0f172a", textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 },
  metaGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 },
  metaItem: (bg, border, labelColor) => ({ background: bg, border: `1px solid ${border}`, borderRadius: 12, padding: "12px 14px" }),
  metaLabel: (color) => ({ fontSize: 10, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }),
  metaValue: { fontSize: 13, fontWeight: 700, color: "#0f172a", overflow: "hidden", textOverflow: "ellipsis" },

  // Loading / error
  loadingWrap: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)" },
  spinner: { width: 48, height: 48, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 14px" },
  loadingText: { fontSize: 14, color: "#64748b", fontWeight: 500 },
  errorCard: { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 16, padding: "20px 24px" },
  infoFooter: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 14, padding: "12px 18px", display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "#166534" },
};

const qualityColor = (q) => {
  const map = {
    good: { bg: "rgba(34,197,94,0.15)", color: "#22c55e", border: "rgba(34,197,94,0.3)", dot: "#22c55e" },
    high: { bg: "rgba(34,197,94,0.15)", color: "#22c55e", border: "rgba(34,197,94,0.3)", dot: "#22c55e" },
    partial: { bg: "rgba(245,158,11,0.15)", color: "#fbbf24", border: "rgba(245,158,11,0.3)", dot: "#f59e0b" },
    medium: { bg: "rgba(245,158,11,0.15)", color: "#fbbf24", border: "rgba(245,158,11,0.3)", dot: "#f59e0b" },
    poor: { bg: "rgba(239,68,68,0.15)", color: "#f87171", border: "rgba(239,68,68,0.3)", dot: "#ef4444" },
    low: { bg: "rgba(239,68,68,0.15)", color: "#f87171", border: "rgba(239,68,68,0.3)", dot: "#ef4444" },
  };
  return map[q?.toLowerCase()] || { bg: "rgba(148,163,184,0.15)", color: "#94a3b8", border: "rgba(148,163,184,0.3)", dot: "#94a3b8" };
};

const SECTIONS = [
  { key: "summary", label: "Summary", icon: <FiUser size={14} color="white" /> },
  { key: "objective", label: "Objective", icon: <FiUser size={14} color="white" /> },
  { key: "skills", label: "Skills", icon: <FiCode size={14} color="white" /> },
  { key: "experience", label: "Experience", icon: <FiBriefcase size={14} color="white" /> },
  { key: "education", label: "Education", icon: <FiBook size={14} color="white" /> },
  { key: "projects", label: "Projects", icon: <FiCode size={14} color="white" /> },
  { key: "certifications", label: "Certifications", icon: <FiAward size={14} color="white" /> },
  { key: "internships", label: "Internships", icon: <FiBriefcase size={14} color="white" /> },
  { key: "languages", label: "Languages", icon: <FiBook size={14} color="white" /> },
  { key: "awards", label: "Awards", icon: <FiAward size={14} color="white" /> },
  { key: "hobbies", label: "Hobbies", icon: <FiUser size={14} color="white" /> },
];

function renderContent(content) {
  if (!content) return null;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map((item, i) => (
      <div key={i} style={S.itemCard}>
        {typeof item === "object" ? (item.raw || JSON.stringify(item, null, 2)) : item}
      </div>
    ));
  }
  if (content.all) return content.all;
  if (content.raw) return content.raw;
  return JSON.stringify(content, null, 2);
}

function ResumeSection({ label, content, icon }) {
  const rendered = renderContent(content);
  if (!rendered && rendered !== 0) return null;
  return (
    <div style={S.section}>
      <div style={S.sectionHeader}>
        <div style={S.sectionIcon}>{icon}</div>
        <span style={S.sectionTitle}>{label}</span>
      </div>
      <div style={S.sectionBody}>{rendered}</div>
    </div>
  );
}

function ResumeDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { fetchResume(); }, [id]);

  const fetchResume = async () => {
    try {
      setLoading(true);
      const data = await getResume(id);
      setResume(data);
      setError('');
    } catch {
      setError('Failed to load resume details.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div style={S.loadingWrap}>
      <div style={{ textAlign: "center" }}>
        <div style={S.spinner} />
        <div style={S.loadingText}>Loading resume...</div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  if (error || !resume) return (
    <div style={S.page}>
      <div style={{ ...S.inner, maxWidth: 600 }}>
        <div style={S.errorCard}>
          <p style={{ color: "#991b1b", fontWeight: 700, marginBottom: 10 }}>⚠️ {error || "Resume not found"}</p>
          <button style={S.backBtn} onClick={() => navigate('/dashboard')}>← Back to Dashboard</button>
        </div>
      </div>
    </div>
  );

  const parsed = resume.parsed_data || {};
  const qc = qualityColor(resume.parsing_quality);
  const availableSections = SECTIONS.filter(({ key }) => parsed[key]);
  const leftSections = availableSections.slice(0, Math.ceil(availableSections.length / 2));
  const rightSections = availableSections.slice(Math.ceil(availableSections.length / 2));

  const META = [
    { label: "File Name", value: resume.original_filename, bg: "#f8fafc", border: "#e8edf5", lc: "#64748b" },
    { label: "File Type", value: resume.file_type?.toUpperCase(), bg: "#eff6ff", border: "#bfdbfe", lc: "#2563eb" },
    { label: "Parsing Quality", value: resume.parsing_quality, bg: "#f0fdf4", border: "#bbf7d0", lc: "#16a34a" },
    { label: "Extraction Method", value: parsed.extraction_method || "N/A", bg: "#faf5ff", border: "#ddd6fe", lc: "#7c3aed" },
    { label: "Uploaded", value: new Date(resume.created_at).toLocaleDateString('en-IN', { day: "numeric", month: "short", year: "numeric" }), bg: "#fffbeb", border: "#fde68a", lc: "#d97706" },
    resume.updated_at && { label: "Last Updated", value: new Date(resume.updated_at).toLocaleDateString('en-IN', { day: "numeric", month: "short", year: "numeric" }), bg: "#fff7ed", border: "#fed7aa", lc: "#ea580c" },
    { label: "Manually Edited", value: resume.is_edited ? "Yes" : "No", bg: "#fdf4ff", border: "#f0abfc", lc: "#a21caf" },
  ].filter(Boolean);

  return (
    <div style={S.page}>
      <div style={S.inner}>

        {/* Top nav */}
        <div style={S.topNav}>
          <button style={S.backBtn} onClick={() => navigate('/dashboard')}>
            <FiArrowLeft size={15} /> Back to Dashboard
          </button>
          <button style={S.editBtn} onClick={() => navigate(`/resume/${id}/edit`)}>
            <FiEdit size={16} /> Edit Resume
          </button>
        </div>

        {/* Hero */}
        <div style={S.hero}>
          <div style={S.heroOverlay} />
          <div style={S.heroContent}>
            <div style={S.heroTop}>
              <div style={S.heroAvatar}>{(resume.name || "?").charAt(0).toUpperCase()}</div>
              <div style={{ flex: 1 }}>
                <h1 style={S.heroName}>{resume.name || "Unknown Candidate"}</h1>
                <div style={S.heroContacts}>
                  {resume.email && <span style={S.heroPill}><FiMail size={13} />{resume.email}</span>}
                  {resume.mobile_number && <span style={S.heroPill}><FiPhone size={13} />{resume.mobile_number}</span>}
                  {resume.location && <span style={S.heroPill}><FiMapPin size={13} />{resume.location}</span>}
                </div>
                <div style={S.heroBadges}>
                  {resume.parsing_quality && (
                    <span style={S.heroBadge(qc.bg, qc.color, qc.border)}>
                      <span style={{ width: 6, height: 6, borderRadius: "50%", background: qc.dot, display: "inline-block" }} />
                      {resume.parsing_quality} quality
                    </span>
                  )}
                  {resume.version && (
                    <span style={S.heroBadge("rgba(255,255,255,0.12)", "rgba(255,255,255,0.7)", "rgba(255,255,255,0.25)")}>
                      v{resume.version}
                    </span>
                  )}
                  {resume.is_edited && (
                    <span style={S.heroBadge("rgba(34,197,94,0.15)", "#4ade80", "rgba(34,197,94,0.3)")}>
                      ✏️ Edited
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content sections */}
        {availableSections.length > 0 ? (
          <div style={S.grid}>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {leftSections.map(({ key, label, icon }) => (
                <ResumeSection key={key} label={label} content={parsed[key]} icon={icon} />
              ))}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {rightSections.map(({ key, label, icon }) => (
                <ResumeSection key={key} label={label} content={parsed[key]} icon={icon} />
              ))}
            </div>
          </div>
        ) : (
          <div style={{ ...S.section, marginBottom: 16 }}>
            <div style={S.sectionEmpty}>No parsed content available. Try editing this resume to add information manually.</div>
          </div>
        )}

        {/* Metadata */}
        <div style={S.metaCard}>
          <div style={S.metaTitle}>
            <div style={{ ...S.sectionIcon, width: 28, height: 28 }}><FiFileText size={13} color="white" /></div>
            Document Metadata
          </div>
          <div style={S.metaGrid}>
            {META.map(({ label, value, bg, border, lc }) => (
              <div key={label} style={S.metaItem(bg, border, lc)}>
                <div style={S.metaLabel(lc)}>{label}</div>
                <div style={S.metaValue}>{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Info footer */}
        <div style={S.infoFooter}>
          <span style={{ fontSize: 16 }}>🤖</span>
          <span>This resume was automatically parsed by Zapplic AI. Click <strong>Edit Resume</strong> to correct any fields.</span>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default ResumeDetailPage;