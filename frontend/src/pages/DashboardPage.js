import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEye, FiEdit, FiTrash2, FiMail, FiPhone, FiMapPin, FiFileText, FiSearch, FiZap } from 'react-icons/fi';
import { getResumes, deleteResume } from '../services/api';

const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 1100, margin: "0 auto" },

  // Header
  headerCard: { background: "white", borderRadius: 20, padding: "24px 28px", marginBottom: 24, boxShadow: "0 4px 24px rgba(0,0,0,0.07)", border: "1px solid #e8edf5" },
  headerTop: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 },
  titleRow: { display: "flex", alignItems: "center", gap: 14, marginBottom: 4 },
  titleIcon: { width: 48, height: 48, borderRadius: 14, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" },
  h1: { margin: 0, fontSize: 26, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" },
  countBadge: { display: "inline-flex", alignItems: "center", gap: 6, background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 20, padding: "4px 12px", fontSize: 13, fontWeight: 700, color: "#2563eb", marginTop: 6 },
  uploadBtn: { display: "flex", alignItems: "center", gap: 8, padding: "11px 22px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 12, fontSize: 14, fontWeight: 700, cursor: "pointer", letterSpacing: "0.2px", flexShrink: 0 },

  // Search
  searchWrap: { position: "relative", marginTop: 20 },
  searchIcon: { position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#94a3b8", pointerEvents: "none" },
  searchInput: { width: "100%", paddingLeft: 44, paddingRight: 40, paddingTop: 11, paddingBottom: 11, border: "2px solid #e2e8f0", borderRadius: 12, fontSize: 14, outline: "none", transition: "border-color 0.15s", background: "#f8fafc", boxSizing: "border-box" },
  clearBtn: { position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 16, lineHeight: 1 },

  // Table container
  tableCard: { background: "white", borderRadius: 20, boxShadow: "0 4px 24px rgba(0,0,0,0.07)", border: "1px solid #e8edf5", overflow: "hidden" },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  thead: { background: "#f8fafc", borderBottom: "1px solid #e8edf5" },
  th: { padding: "12px 20px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" },
  tr: { borderBottom: "1px solid #f1f5f9", transition: "background 0.1s" },
  td: { padding: "14px 20px", verticalAlign: "middle" },

  // Candidate cell
  avatar: { width: 40, height: 40, borderRadius: 12, background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", fontSize: 16, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  nameText: { fontSize: 14, fontWeight: 700, color: "#0f172a", marginBottom: 2 },
  filenameText: { fontSize: 11, color: "#94a3b8" },
  metaItem: { display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#64748b" },

  // Quality badge
  qualityBadge: (q) => {
    const map = {
      good: { bg: "#f0fdf4", color: "#16a34a", border: "#bbf7d0", dot: "#22c55e", label: "Excellent" },
      high: { bg: "#f0fdf4", color: "#16a34a", border: "#bbf7d0", dot: "#22c55e", label: "High" },
      partial: { bg: "#fffbeb", color: "#d97706", border: "#fde68a", dot: "#f59e0b", label: "Partial" },
      medium: { bg: "#fffbeb", color: "#d97706", border: "#fde68a", dot: "#f59e0b", label: "Medium" },
      poor: { bg: "#fef2f2", color: "#dc2626", border: "#fecaca", dot: "#ef4444", label: "Poor" },
      low: { bg: "#fef2f2", color: "#dc2626", border: "#fecaca", dot: "#ef4444", label: "Low" },
    };
    const c = map[q?.toLowerCase()] || { bg: "#f8fafc", color: "#64748b", border: "#e2e8f0", dot: "#94a3b8", label: q || "Unknown" };
    return { bg: c.bg, color: c.color, border: c.border, dot: c.dot, label: c.label };
  },

  // Action buttons
  actionBtn: (color) => ({ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 8, border: "none", cursor: "pointer", background: `${color}15`, color, transition: "all 0.15s" }),

  // Empty state
  empty: { textAlign: "center", padding: "60px 20px" },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 20, fontWeight: 700, color: "#0f172a", marginBottom: 6 },
  emptyText: { fontSize: 14, color: "#64748b", marginBottom: 24 },
  emptyBtn: { display: "inline-flex", alignItems: "center", gap: 8, padding: "11px 24px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 12, fontSize: 14, fontWeight: 700, cursor: "pointer" },

  // Mobile card
  mobileCard: { padding: "16px 20px", borderBottom: "1px solid #f1f5f9" },
  mobileHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 },
  mobileName: { fontSize: 15, fontWeight: 700, color: "#0f172a" },
  mobileFile: { fontSize: 11, color: "#94a3b8", marginTop: 2 },
  mobileMeta: { display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 },
  mobileActions: { display: "flex", gap: 8, paddingTop: 12, borderTop: "1px solid #f1f5f9" },
  mobileActionBtn: (color) => ({ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "8px", borderRadius: 10, border: "none", cursor: "pointer", background: `${color}15`, color, fontSize: 13, fontWeight: 600 }),

  // Loading
  loadingWrap: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)" },
  loadingBox: { textAlign: "center" },
  spinner: { width: 52, height: 52, border: "4px solid #e2e8f0", borderTop: "4px solid #2563eb", borderRadius: "50%", animation: "dashSpin 0.8s linear infinite", margin: "0 auto 16px" },
  loadingText: { fontSize: 15, color: "#64748b", fontWeight: 500 },

  // Error
  errorBox: { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: "14px 18px", marginBottom: 20, color: "#991b1b", fontSize: 14, fontWeight: 500 },

  // Delete confirm modal
  modalOverlay: { position: "fixed", inset: 0, background: "rgba(15,23,42,0.55)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000, backdropFilter: "blur(4px)" },
  modal: { background: "white", borderRadius: 20, padding: 28, maxWidth: 400, width: "90%", boxShadow: "0 24px 80px rgba(0,0,0,0.2)" },
  modalTitle: { margin: "0 0 8px", fontSize: 18, fontWeight: 800, color: "#0f172a" },
  modalText: { margin: "0 0 24px", fontSize: 14, color: "#64748b", lineHeight: 1.5 },
  modalBtns: { display: "flex", gap: 10 },
  modalCancel: { flex: 1, padding: "10px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: "pointer", color: "#374151" },
  modalConfirm: { flex: 1, padding: "10px", background: "linear-gradient(135deg, #ef4444, #dc2626)", border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: "pointer", color: "white" },
};

function DeleteModal({ name, onCancel, onConfirm, loading }) {
  return (
    <div style={S.modalOverlay}>
      <div style={S.modal}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>🗑️</div>
        <h3 style={S.modalTitle}>Delete Resume?</h3>
        <p style={S.modalText}>
          This will permanently delete <strong>{name || "this resume"}</strong>. This action cannot be undone.
        </p>
        <div style={S.modalBtns}>
          <button style={S.modalCancel} onClick={onCancel} disabled={loading}>Cancel</button>
          <button style={{ ...S.modalConfirm, opacity: loading ? 0.7 : 1 }} onClick={onConfirm} disabled={loading}>
            {loading ? "Deleting..." : "Yes, Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

function QualityBadge({ quality }) {
  const c = S.qualityBadge(quality);
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, background: c.bg, color: c.color, border: `1px solid ${c.border}`, borderRadius: 20, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: c.dot, display: "inline-block" }} />
      {c.label}
    </span>
  );
}

function DashboardPage() {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [total, setTotal] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null); // { id, name }
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);

  useEffect(() => { fetchResumes(); }, []);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const data = await getResumes(0, 100);
      setResumes(data.resumes);
      setTotal(data.total);
      setError('');
    } catch (err) {
      setError('Failed to fetch resumes. Please refresh.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await deleteResume(deleteTarget.id);
      setDeleteTarget(null);
      fetchResumes();
    } catch {
      alert('Failed to delete resume');
    } finally {
      setDeleteLoading(false);
    }
  };

  const filtered = resumes.filter(r => {
    const q = searchTerm.toLowerCase();
    return (
      r.name?.toLowerCase().includes(q) ||
      r.email?.toLowerCase().includes(q) ||
      r.mobile_number?.includes(searchTerm) ||
      r.location?.toLowerCase().includes(q)
    );
  });

  if (loading) {
    return (
      <div style={S.loadingWrap}>
        <div style={S.loadingBox}>
          <div style={S.spinner} />
          <div style={S.loadingText}>Loading resumes...</div>
        </div>
        <style>{`@keyframes dashSpin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={S.page}>
      <div style={S.inner}>

        {/* ── Header ── */}
        <div style={S.headerCard}>
          <div style={S.headerTop}>
            <div>
              <div style={S.titleRow}>
                <div style={S.titleIcon}>
                  <FiFileText color="white" size={22} />
                </div>
                <h1 style={S.h1}>Resume Dashboard</h1>
              </div>
              <div style={S.countBadge}>
                <FiFileText size={13} />
                {total} {total === 1 ? "Resume" : "Resumes"}
              </div>
            </div>
            <button style={S.uploadBtn} onClick={() => navigate('/smart-upload')}>
              <FiZap size={16} />
              Smart Upload
            </button>
          </div>

          {resumes.length > 0 && (
            <div style={S.searchWrap}>
              <div style={S.searchIcon}><FiSearch size={16} /></div>
              <input
                style={{ ...S.searchInput, borderColor: searchFocused ? "#2563eb" : "#e2e8f0" }}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
                placeholder="Search by name, email, phone or location..."
              />
              {searchTerm && (
                <button style={S.clearBtn} onClick={() => setSearchTerm('')}>✕</button>
              )}
            </div>
          )}
        </div>

        {/* ── Error ── */}
        {error && <div style={S.errorBox}>⚠️ {error}</div>}

        {/* ── Empty State ── */}
        {resumes.length === 0 && !error ? (
          <div style={{ ...S.tableCard }}>
            <div style={S.empty}>
              <div style={S.emptyIcon}>📂</div>
              <div style={S.emptyTitle}>No resumes yet</div>
              <div style={S.emptyText}>Upload your first resume to get started with AI-powered parsing.</div>
              <button style={S.emptyBtn} onClick={() => navigate('/smart-upload')}>
                <FiZap size={16} /> Upload First Resume
              </button>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div style={S.tableCard}>
            <div style={S.empty}>
              <div style={S.emptyIcon}>🔍</div>
              <div style={S.emptyTitle}>No matches found</div>
              <div style={S.emptyText}>Try different keywords or clear the search.</div>
              <button style={{ ...S.emptyBtn, background: "#f8fafc", color: "#374151", border: "1px solid #e2e8f0" }} onClick={() => setSearchTerm('')}>
                Clear Search
              </button>
            </div>
          </div>
        ) : (
          <div style={S.tableCard}>

            {/* ── Desktop Table ── */}
            <div style={{ ...S.tableWrap, display: window.innerWidth < 768 ? "none" : "block" }} className="hidden lg:block">
              <table style={S.table}>
                <thead style={S.thead}>
                  <tr>
                    <th style={S.th}>Candidate</th>
                    <th style={S.th}>Contact</th>
                    <th style={S.th}>Location</th>
                    <th style={S.th}>Quality</th>
                    <th style={S.th}>Uploaded</th>
                    <th style={{ ...S.th, textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => (
                    <tr key={r.id} style={S.tr}
                      onMouseEnter={e => e.currentTarget.style.background = "#f8fafc"}
                      onMouseLeave={e => e.currentTarget.style.background = "white"}
                    >
                      {/* Candidate */}
                      <td style={S.td}>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <div style={S.avatar}>{(r.name || "?").charAt(0).toUpperCase()}</div>
                          <div>
                            <div style={S.nameText}>{r.name || "Unknown"}</div>
                            <div style={S.filenameText}>{r.original_filename}</div>
                          </div>
                        </div>
                      </td>

                      {/* Contact */}
                      <td style={S.td}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                          {r.email && <div style={S.metaItem}><FiMail size={12} color="#2563eb" />{r.email}</div>}
                          {r.mobile_number && <div style={S.metaItem}><FiPhone size={12} color="#16a34a" />{r.mobile_number}</div>}
                          {!r.email && !r.mobile_number && <span style={{ fontSize: 12, color: "#cbd5e1" }}>No contact info</span>}
                        </div>
                      </td>

                      {/* Location */}
                      <td style={S.td}>
                        {r.location
                          ? <div style={S.metaItem}><FiMapPin size={12} color="#7c3aed" /><span style={{ maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.location}</span></div>
                          : <span style={{ fontSize: 12, color: "#cbd5e1" }}>—</span>
                        }
                      </td>

                      {/* Quality */}
                      <td style={S.td}><QualityBadge quality={r.parsing_quality} /></td>

                      {/* Date */}
                      <td style={S.td}>
                        <span style={{ fontSize: 12, color: "#64748b" }}>
                          {new Date(r.created_at).toLocaleDateString('en-IN', { day: "numeric", month: "short", year: "numeric" })}
                        </span>
                      </td>

                      {/* Actions */}
                      <td style={{ ...S.td, textAlign: "right" }}>
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: 6 }}>
                          <button style={S.actionBtn("#2563eb")} title="View" onClick={() => navigate(`/resume/${r.id}`)}>
                            <FiEye size={15} />
                          </button>
                          <button style={S.actionBtn("#16a34a")} title="Edit" onClick={() => navigate(`/resume/${r.id}/edit`)}>
                            <FiEdit size={15} />
                          </button>
                          <button style={S.actionBtn("#ef4444")} title="Delete" onClick={() => setDeleteTarget({ id: r.id, name: r.name })}>
                            <FiTrash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ── Mobile Cards ── */}
            <div className="lg:hidden">
              {filtered.map((r) => (
                <div key={r.id} style={S.mobileCard}>
                  <div style={S.mobileHeader}>
                    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                      <div style={S.avatar}>{(r.name || "?").charAt(0).toUpperCase()}</div>
                      <div>
                        <div style={S.mobileName}>{r.name || "Unknown"}</div>
                        <div style={S.mobileFile}>{r.original_filename}</div>
                      </div>
                    </div>
                    <QualityBadge quality={r.parsing_quality} />
                  </div>
                  <div style={S.mobileMeta}>
                    {r.email && <div style={S.metaItem}><FiMail size={12} color="#2563eb" />{r.email}</div>}
                    {r.mobile_number && <div style={S.metaItem}><FiPhone size={12} color="#16a34a" />{r.mobile_number}</div>}
                    {r.location && <div style={S.metaItem}><FiMapPin size={12} color="#7c3aed" />{r.location}</div>}
                    <span style={{ fontSize: 11, color: "#94a3b8" }}>
                      {new Date(r.created_at).toLocaleDateString('en-IN', { day: "numeric", month: "short", year: "numeric" })}
                    </span>
                  </div>
                  <div style={S.mobileActions}>
                    <button style={S.mobileActionBtn("#2563eb")} onClick={() => navigate(`/resume/${r.id}`)}>
                      <FiEye size={14} /> View
                    </button>
                    <button style={S.mobileActionBtn("#16a34a")} onClick={() => navigate(`/resume/${r.id}/edit`)}>
                      <FiEdit size={14} /> Edit
                    </button>
                    <button style={S.mobileActionBtn("#ef4444")} onClick={() => setDeleteTarget({ id: r.id, name: r.name })}>
                      <FiTrash2 size={14} /> Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Footer count */}
            <div style={{ padding: "12px 20px", borderTop: "1px solid #f1f5f9", fontSize: 12, color: "#94a3b8", textAlign: "right" }}>
              Showing {filtered.length} of {total} resumes
              {searchTerm && ` matching "${searchTerm}"`}
            </div>
          </div>
        )}
      </div>

      {/* Delete confirm modal */}
      {deleteTarget && (
        <DeleteModal
          name={deleteTarget.name}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleDeleteConfirm}
          loading={deleteLoading}
        />
      )}

      <style>{`@keyframes dashSpin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default DashboardPage;