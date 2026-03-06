import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 960, margin: "0 auto" },

  // Header
  pageHeader: { display: "flex", alignItems: "center", gap: 14, marginBottom: 24 },
  pageIcon: { width: 52, height: 52, borderRadius: 14, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: 24 },
  pageTitle: { margin: 0, fontSize: 26, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" },
  pageSub: { margin: "4px 0 0", fontSize: 13, color: "#64748b" },

  // Filter card
  filterCard: { background: "white", borderRadius: 20, padding: "24px 28px", marginBottom: 20, boxShadow: "0 4px 24px rgba(0,0,0,0.07)", border: "1px solid #e8edf5" },
  filterGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 },
  filterGrid3: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 16 },
  filterLabel: { display: "block", fontSize: 12, fontWeight: 700, color: "#374151", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.3px" },
  filterInput: (focused) => ({
    width: "100%", padding: "10px 14px", border: `2px solid ${focused ? "#2563eb" : "#e2e8f0"}`,
    borderRadius: 10, fontSize: 14, outline: "none", background: "#f8fafc",
    boxSizing: "border-box", transition: "border-color 0.15s",
    boxShadow: focused ? "0 0 0 3px rgba(37,99,235,0.1)" : "none",
  }),

  // Skills section
  skillsWrap: { marginBottom: 16 },
  chipContainer: { display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 },
  chipSelected: { display: "inline-flex", alignItems: "center", gap: 5, background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600 },
  chipRemove: { background: "none", border: "none", color: "rgba(255,255,255,0.8)", cursor: "pointer", fontSize: 14, padding: 0, lineHeight: 1, display: "flex" },
  suggestionsWrap: { marginTop: 8, display: "flex", flexWrap: "wrap", gap: 5 },
  chipSuggest: { background: "#eff6ff", color: "#2563eb", border: "1px solid #bfdbfe", padding: "3px 10px", borderRadius: 20, fontSize: 12, cursor: "pointer", fontWeight: 500, transition: "all 0.1s" },

  // Button row
  btnRow: { display: "flex", gap: 10, marginTop: 4 },
  searchBtn: { flex: 1, padding: "12px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: "pointer" },
  resetBtn: { padding: "12px 20px", background: "white", border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 14, fontWeight: 600, color: "#374151", cursor: "pointer" },

  // Results header
  resultsHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 },
  resultsCount: { fontSize: 16, fontWeight: 800, color: "#0f172a" },
  activeTags: { display: "flex", flexWrap: "wrap", gap: 6 },
  tag: (color) => ({ display: "inline-flex", alignItems: "center", gap: 4, background: `${color}15`, color, border: `1px solid ${color}30`, padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600 }),

  // Result card
  card: { background: "white", border: "1px solid #e8edf5", borderRadius: 16, padding: "18px 20px", marginBottom: 12, boxShadow: "0 2px 12px rgba(0,0,0,0.05)", transition: "box-shadow 0.2s" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 },
  avatar: { width: 44, height: 44, borderRadius: 12, background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", fontSize: 18, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  candidateName: { margin: 0, fontSize: 17, fontWeight: 800, color: "#0f172a" },
  metaRow: { display: "flex", gap: 14, marginTop: 5, flexWrap: "wrap" },
  meta: { fontSize: 12, color: "#64748b", display: "flex", alignItems: "center", gap: 4 },

  scoreBadge: (score) => {
    const color = score >= 75 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";
    const bg = score >= 75 ? "#f0fdf4" : score >= 50 ? "#fffbeb" : "#fef2f2";
    const border = score >= 75 ? "#bbf7d0" : score >= 50 ? "#fde68a" : "#fecaca";
    return { width: 56, height: 56, borderRadius: "50%", border: `3px solid ${border}`, background: bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexShrink: 0, color };
  },
  scoreNum: { fontSize: 16, fontWeight: 900, lineHeight: 1 },
  scoreLabel: { fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.3px", opacity: 0.7 },

  matchRow: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, marginTop: 12 },
  matchLabel: { fontSize: 11, fontWeight: 700, color: "#374151", textTransform: "uppercase", letterSpacing: "0.3px" },
  matchedSkill: { background: "#dcfce7", color: "#166534", border: "1px solid #bbf7d0", padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600 },
  missingSkill: { background: "#fee2e2", color: "#991b1b", border: "1px solid #fecaca", padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600 },

  cardFooter: { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12, paddingTop: 12, borderTop: "1px solid #f1f5f9" },
  indicators: { display: "flex", gap: 8, flexWrap: "wrap" },
  indicator: (match) => ({ fontSize: 11, color: match ? "#16a34a" : "#cbd5e1", fontWeight: 600, display: "flex", alignItems: "center", gap: 3 }),

  viewBtn: { display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 14px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, color: "#2563eb", fontSize: 12, fontWeight: 700, cursor: "pointer" },
  expandBtn: { background: "none", border: "none", color: "#2563eb", fontSize: 12, fontWeight: 700, cursor: "pointer" },

  // Score breakdown
  breakdown: { marginTop: 14, background: "#f8fafc", border: "1px solid #e8edf5", borderRadius: 12, padding: 14 },
  barRow: { marginBottom: 8 },
  barLabelRow: { display: "flex", justifyContent: "space-between", fontSize: 12, color: "#64748b", marginBottom: 3, fontWeight: 500 },
  barTrack: { height: 6, background: "#e2e8f0", borderRadius: 20, overflow: "hidden" },
  barFill: (pct) => ({ height: "100%", width: `${pct}%`, background: "linear-gradient(90deg, #2563eb, #7c3aed)", borderRadius: 20, transition: "width 0.4s" }),
  totalScore: { textAlign: "right", fontWeight: 800, color: "#0f172a", marginTop: 10, fontSize: 14 },

  // Empty / no results
  empty: { textAlign: "center", padding: "48px 20px", background: "white", borderRadius: 20, border: "1px solid #e8edf5" },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: 700, color: "#0f172a", marginBottom: 6 },
  emptyText: { fontSize: 14, color: "#64748b" },

  spinner: { width: 44, height: 44, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "40px auto" },
};

const SKILL_SUGGESTIONS = [
  "Java", "Python", "JavaScript", "React", "Node.js",
  "Spring Boot", "AWS", "Docker", "Kubernetes", "SQL",
  "MongoDB", "Microservices", "REST API", "Git", "Angular",
  "Photoshop", "Figma", "TypeScript", "Flutter", "Machine Learning",
];

function ScoreBar({ label, score, max }) {
  const pct = max > 0 ? Math.min((score / max) * 100, 100) : 0;
  return (
    <div style={S.barRow}>
      <div style={S.barLabelRow}><span>{label}</span><span style={{ fontWeight: 700, color: "#374151" }}>{score}/{max}</span></div>
      <div style={S.barTrack}><div style={S.barFill(pct)} /></div>
    </div>
  );
}

function ResumeCard({ resume }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const score = resume.match_percentage || 0;
  const details = resume.match_details || {};
  const s = S.scoreBadge(score);

  return (
    <div style={S.card}
      onMouseEnter={e => e.currentTarget.style.boxShadow = "0 6px 24px rgba(37,99,235,0.12)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.05)"}
    >
      <div style={S.cardHeader}>
        <div style={{ display: "flex", gap: 14, flex: 1, minWidth: 0 }}>
          <div style={S.avatar}>{(resume.name || "?").charAt(0).toUpperCase()}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h4 style={S.candidateName}>{resume.name || "Unknown"}</h4>
            <div style={S.metaRow}>
              {resume.email && <span style={S.meta}>✉️ {resume.email}</span>}
              {resume.mobile_number && <span style={S.meta}>📞 {resume.mobile_number}</span>}
              {resume.location && <span style={S.meta}>📍 {resume.location}</span>}
            </div>
          </div>
        </div>
        <div style={s}>
          <div style={S.scoreNum}>{score}%</div>
          <div style={S.scoreLabel}>match</div>
        </div>
      </div>

      {/* Matched / Missing skills */}
      {(details.skills_matched?.length > 0 || details.skills_missing?.length > 0) && (
        <div style={S.matchRow}>
          {details.skills_matched?.length > 0 && (
            <>
              <span style={S.matchLabel}>✅ Matched:</span>
              {details.skills_matched.map(s => <span key={s} style={S.matchedSkill}>{s}</span>)}
            </>
          )}
          {details.skills_missing?.length > 0 && (
            <>
              <span style={{ ...S.matchLabel, marginLeft: 8 }}>❌ Missing:</span>
              {details.skills_missing.map(s => <span key={s} style={S.missingSkill}>{s}</span>)}
            </>
          )}
        </div>
      )}

      {/* Footer */}
      <div style={S.cardFooter}>
        <div style={S.indicators}>
          {[
            { key: "role_match", label: "Role" },
            { key: "location_match", label: "Location" },
            { key: "experience_match", label: "Experience" },
            { key: "education_match", label: "Education" },
          ].map(({ key, label }) => (
            <span key={key} style={S.indicator(details[key])}>
              {details[key] ? "✅" : "○"} {label}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={S.expandBtn} onClick={() => setExpanded(!expanded)}>
            {expanded ? "▲ Less" : "▼ Details"}
          </button>
          {resume.id && (
            <button style={S.viewBtn} onClick={() => navigate(`/resume/${resume.id}`)}>
              View →
            </button>
          )}
        </div>
      </div>

      {/* Expandable score breakdown */}
      {expanded && (
        <div style={S.breakdown}>
          <ScoreBar label="Skills" score={details.skills_score || 0} max={40} />
          <ScoreBar label="Role" score={details.role_score || 0} max={25} />
          <ScoreBar label="Location" score={details.location_score || 0} max={20} />
          <ScoreBar label="Experience" score={details.experience_score || 0} max={10} />
          <ScoreBar label="Education" score={details.education_score || 0} max={5} />
          <div style={S.totalScore}>Total: {resume.relevance_score || score}/100</div>
        </div>
      )}
    </div>
  );
}

export default function ComprehensiveSearch() {
  const [filters, setFilters] = useState({ role: "", skills: "", location: "", min_experience: "", max_experience: "", education: "" });
  const [focused, setFocused] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [activeFilters, setActiveFilters] = useState({});

  const currentSkills = filters.skills ? filters.skills.split(",").map(s => s.trim()).filter(Boolean) : [];

  const addSkill = (skill) => {
    if (!currentSkills.includes(skill))
      setFilters(prev => ({ ...prev, skills: [...currentSkills, skill].join(", ") }));
  };

  const removeSkill = (skill) =>
    setFilters(prev => ({ ...prev, skills: currentSkills.filter(s => s !== skill).join(", ") }));

  const handleSearch = async () => {
    setLoading(true); setSearched(true);
    const params = {};
    if (filters.role) params.role = filters.role;
    if (filters.skills) params.skills = filters.skills;
    if (filters.location) params.location = filters.location;
    if (filters.min_experience) params.min_experience = parseInt(filters.min_experience);
    if (filters.max_experience) params.max_experience = parseInt(filters.max_experience);
    if (filters.education) params.education = filters.education;
    setActiveFilters(params);
    try {
      const res = await api.get(`/resumes/search/comprehensive`, { params });
      setResults(res.data.results || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFilters({ role: "", skills: "", location: "", min_experience: "", max_experience: "", education: "" });
    setResults([]); setSearched(false); setActiveFilters({});
  };

  const input = (key, placeholder, type = "text", extra = {}) => (
    <div>
      <label style={S.filterLabel}>{placeholder}</label>
      <input
        type={type}
        style={S.filterInput(focused === key)}
        placeholder={placeholder}
        value={filters[key]}
        onFocus={() => setFocused(key)}
        onBlur={() => setFocused(null)}
        onChange={e => setFilters(p => ({ ...p, [key]: e.target.value }))}
        onKeyDown={e => e.key === "Enter" && handleSearch()}
        {...extra}
      />
    </div>
  );

  return (
    <div style={S.page}>
      <div style={S.inner}>
        {/* Header */}
        <div style={S.pageHeader}>
          <div style={S.pageIcon}>🔍</div>
          <div>
            <h1 style={S.pageTitle}>Advanced Search</h1>
            <p style={S.pageSub}>Filter resumes by role, skills, location, experience and education</p>
          </div>
        </div>

        {/* Filter card */}
        <div style={S.filterCard}>
          <div style={S.filterGrid}>
            {input("role", "Job Title / Role")}
            {input("location", "Location (City)")}
          </div>
          <div style={S.filterGrid3}>
            {input("min_experience", "Min Experience (yrs)", "number", { min: 0, max: 30 })}
            {input("max_experience", "Max Experience (yrs)", "number", { min: 0, max: 30 })}
            {input("education", "Education (e.g. B.Tech)")}
          </div>

          {/* Skills */}
          <div style={S.skillsWrap}>
            <label style={S.filterLabel}>Skills</label>
            <input
              style={S.filterInput(focused === "skills")}
              placeholder="e.g. Java, AWS, React — or use quick-add below"
              value={filters.skills}
              onFocus={() => setFocused("skills")}
              onBlur={() => setFocused(null)}
              onChange={e => setFilters(p => ({ ...p, skills: e.target.value }))}
              onKeyDown={e => e.key === "Enter" && handleSearch()}
            />
            {currentSkills.length > 0 && (
              <div style={S.chipContainer}>
                {currentSkills.map(skill => (
                  <span key={skill} style={S.chipSelected}>
                    {skill}
                    <button style={S.chipRemove} onClick={() => removeSkill(skill)}>×</button>
                  </span>
                ))}
              </div>
            )}
            <div style={S.suggestionsWrap}>
              <span style={{ fontSize: 11, color: "#94a3b8", alignSelf: "center", marginRight: 4, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.3px" }}>Quick add:</span>
              {SKILL_SUGGESTIONS.filter(s => !currentSkills.includes(s)).slice(0, 12).map(skill => (
                <button key={skill} style={S.chipSuggest} onClick={() => addSkill(skill)}
                  onMouseEnter={e => { e.target.style.background = "#dbeafe"; e.target.style.borderColor = "#93c5fd"; }}
                  onMouseLeave={e => { e.target.style.background = "#eff6ff"; e.target.style.borderColor = "#bfdbfe"; }}
                >
                  + {skill}
                </button>
              ))}
            </div>
          </div>

          <div style={S.btnRow}>
            <button style={S.searchBtn} onClick={handleSearch} disabled={loading}>
              {loading ? "Searching..." : "🔍 Search Resumes"}
            </button>
            <button style={S.resetBtn} onClick={handleReset}>Reset</button>
          </div>
        </div>

        {/* Results */}
        {loading && <div style={S.spinner} />}

        {searched && !loading && (
          <>
            <div style={S.resultsHeader}>
              <div style={S.resultsCount}>
                {results.length} Resume{results.length !== 1 ? "s" : ""} Found
              </div>
              <div style={S.activeTags}>
                {activeFilters.role && <span style={S.tag("#7c3aed")}>💼 {activeFilters.role}</span>}
                {activeFilters.location && <span style={S.tag("#0891b2")}>📍 {activeFilters.location}</span>}
                {activeFilters.min_experience && (
                  <span style={S.tag("#d97706")}>
                    ⏱ {activeFilters.min_experience}{activeFilters.max_experience ? `–${activeFilters.max_experience}` : "+"} yrs
                  </span>
                )}
                {activeFilters.education && <span style={S.tag("#059669")}>🎓 {activeFilters.education}</span>}
                {activeFilters.skills?.split(",").map(s => (
                  <span key={s} style={S.tag("#2563eb")}>🛠 {s.trim()}</span>
                ))}
              </div>
            </div>

            {results.length === 0 ? (
              <div style={S.empty}>
                <div style={S.emptyIcon}>😕</div>
                <div style={S.emptyTitle}>No matches found</div>
                <div style={S.emptyText}>Try broadening your filters — fewer skills, wider experience range, or different location.</div>
              </div>
            ) : (
              results.map(r => <ResumeCard key={r.id} resume={r} />)
            )}
          </>
        )}

        {!searched && !loading && (
          <div style={{ ...S.empty, background: "transparent", border: "2px dashed #e2e8f0" }}>
            <div style={S.emptyIcon}>🎯</div>
            <div style={S.emptyTitle}>Set your filters above</div>
            <div style={S.emptyText}>Use any combination of role, skills, location or experience to find the best candidates.</div>
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}