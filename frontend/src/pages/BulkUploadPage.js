import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUpload, FiCheckCircle, FiXCircle, FiAlertCircle, FiFileText, FiTrash2, FiUser } from 'react-icons/fi';
import { bulkUploadResumes } from '../services/api';


const S = {
  page: { minHeight: "100vh", background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)", padding: "32px 16px" },
  inner: { maxWidth: 860, margin: "0 auto" },

  card: { background: "white", borderRadius: 20, padding: "28px 32px", boxShadow: "0 4px 24px rgba(0,0,0,0.07)", border: "1px solid #e8edf5" },

  pageHeader: { display: "flex", alignItems: "center", gap: 14, marginBottom: 28 },
  pageIcon: { width: 52, height: 52, borderRadius: 14, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  pageTitle: { margin: 0, fontSize: 26, fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" },
  pageSub: { margin: "4px 0 0", fontSize: 13, color: "#64748b" },

  // Dropzone
  dropzone: (active, hasFiles) => ({
    border: `2px dashed ${active ? "#2563eb" : hasFiles ? "#16a34a" : "#d1d5db"}`,
    borderRadius: 16,
    background: active ? "#eff6ff" : hasFiles ? "#f0fdf4" : "#fafafa",
    padding: "48px 24px",
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.2s",
    marginBottom: 20,
  }),
  dropIcon: { fontSize: 44, marginBottom: 10 },
  dropTitle: { fontSize: 16, fontWeight: 700, color: "#0f172a", marginBottom: 4 },
  dropSub: { fontSize: 13, color: "#94a3b8" },

  // File list
  fileListCard: { background: "#f8fafc", border: "1px solid #e8edf5", borderRadius: 14, overflow: "hidden", marginBottom: 20 },
  fileListHeader: { padding: "12px 18px", borderBottom: "1px solid #e8edf5", display: "flex", justifyContent: "space-between", alignItems: "center" },
  fileListTitle: { fontSize: 13, fontWeight: 700, color: "#374151", margin: 0 },
  fileListScroll: { maxHeight: 280, overflowY: "auto" },
  fileRow: { display: "flex", alignItems: "center", gap: 12, padding: "10px 18px", borderBottom: "1px solid #f1f5f9" },
  fileExt: (ext) => ({ width: 36, height: 36, borderRadius: 8, background: ext === "pdf" ? "#fef2f2" : "#eff6ff", color: ext === "pdf" ? "#dc2626" : "#2563eb", fontSize: 10, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", textTransform: "uppercase", flexShrink: 0 }),
  fileName: { flex: 1, fontSize: 13, fontWeight: 600, color: "#1e293b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  fileSize: { fontSize: 11, color: "#94a3b8" },
  removeBtn: { width: 28, height: 28, background: "none", border: "1px solid #fecaca", borderRadius: 8, color: "#ef4444", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },

  // Associate section
  associateCard: { background: "#f8fafc", border: "1px solid #e8edf5", borderRadius: 14, padding: "16px 20px", marginBottom: 20 },
  associateTitle: { fontSize: 13, fontWeight: 700, color: "#374151", marginBottom: 10 },
  associateRow: { display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" },
  select: { padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 10, fontSize: 13, background: "white", outline: "none", cursor: "pointer" },

  // Employee dropdown
  empTrigger: (open) => ({ padding: "9px 14px", background: "white", border: `2px solid ${open ? "#2563eb" : "#e2e8f0"}`, borderRadius: 10, cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", minWidth: 200, fontSize: 13, gap: 8 }),
  empDropdown: { position: "absolute", top: "100%", left: 0, right: 0, background: "white", border: "1px solid #e2e8f0", borderRadius: 14, boxShadow: "0 8px 32px rgba(0,0,0,0.12)", zIndex: 100, marginTop: 4, overflow: "hidden" },
  empAddSection: { padding: "12px 14px", borderBottom: "1px solid #f1f5f9", background: "#f8fafc" },
  empAddRow: { display: "flex", gap: 8, marginTop: 6 },
  empAddInput: { flex: 1, padding: "7px 10px", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 13, outline: "none" },
  empAddBtn: { padding: "7px 14px", background: "#2563eb", color: "white", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: "pointer" },
  empList: { maxHeight: 180, overflowY: "auto" },
  empItem: (selected) => ({ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 14px", cursor: "pointer", background: selected ? "#eff6ff" : "white", fontSize: 13, color: selected ? "#2563eb" : "#374151", fontWeight: selected ? 700 : 400 }),

  // Progress
  progressCard: { background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 14, padding: "18px 20px", marginBottom: 20 },
  progressLabel: { display: "flex", justifyContent: "space-between", fontSize: 13, fontWeight: 600, color: "#1d4ed8", marginBottom: 10 },
  progressTrack: { height: 10, background: "#bfdbfe", borderRadius: 20, overflow: "hidden" },
  progressBar: (p) => ({ height: "100%", width: `${p}%`, background: "linear-gradient(90deg, #2563eb, #7c3aed)", borderRadius: 20, transition: "width 0.3s" }),

  // Action row
  actionRow: { display: "flex", gap: 12, flexWrap: "wrap" },
  uploadBtn: (disabled) => ({ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "13px", background: disabled ? "#e2e8f0" : "linear-gradient(135deg, #2563eb, #7c3aed)", color: disabled ? "#94a3b8" : "white", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: disabled ? "not-allowed" : "pointer" }),
  clearBtn: { padding: "13px 24px", background: "white", border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 14, fontWeight: 600, color: "#374151", cursor: "pointer" },

  // Tips
  tipsCard: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 14, padding: "16px 20px", marginTop: 20 },
  tipsTitle: { fontSize: 13, fontWeight: 700, color: "#166534", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 },
  tipItem: { fontSize: 12, color: "#15803d", marginBottom: 5, display: "flex", gap: 6 },

  // Results
  statGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 20 },
  statCard: (color) => ({ background: `${color}10`, border: `1px solid ${color}30`, borderRadius: 14, padding: "18px 20px" }),
  statNum: (color) => ({ fontSize: 32, fontWeight: 800, color, marginBottom: 2 }),
  statLabel: { fontSize: 13, color: "#64748b", fontWeight: 500 },

  resultSection: { border: "1px solid #e8edf5", borderRadius: 14, overflow: "hidden", marginBottom: 16 },
  resultHeader: (color) => ({ padding: "12px 18px", background: `${color}10`, borderBottom: `1px solid ${color}30`, display: "flex", alignItems: "center", gap: 8, fontSize: 14, fontWeight: 700, color }),
  table: { width: "100%", borderCollapse: "collapse" },
  thead: { background: "#f8fafc" },
  th: { padding: "10px 16px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.4px" },
  trResult: { borderTop: "1px solid #f1f5f9" },
  tdResult: { padding: "11px 16px", fontSize: 13, color: "#1e293b" },

  qualityDot: (q) => {
    const c = { good: "#22c55e", high: "#22c55e", partial: "#f59e0b", medium: "#f59e0b", poor: "#ef4444", low: "#ef4444" };
    return c[q?.toLowerCase()] || "#94a3b8";
  },

  bottomActions: { display: "flex", gap: 12, marginTop: 20 },
  dashBtn: { flex: 1, padding: "12px", background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", border: "none", borderRadius: 12, fontSize: 14, fontWeight: 700, cursor: "pointer" },
  moreBtn: { padding: "12px 24px", background: "white", border: "1px solid #e2e8f0", borderRadius: 12, fontSize: 14, fontWeight: 600, color: "#374151", cursor: "pointer" },
};

function BulkUploadPage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [associateOption, setAssociateOption] = useState('none');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [newEmployeeName, setNewEmployeeName] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeList, setEmployeeList] = useState([]);
  const inputRef = useRef(null);

  React.useEffect(() => {
    try {
      const saved = localStorage.getItem('zapplic_employee');
      if (saved) setSelectedEmployee(saved);
      const listRaw = localStorage.getItem('zapplic_employee_list');
      if (listRaw) setEmployeeList(JSON.parse(listRaw));
    } catch (e) {}
  }, []);

  useEffect(() => {
  if (dropdownOpen) {
    inputRef.current?.focus();
  }
}, [dropdownOpen]);
  const validateAndAddFiles = (selectedFiles) => {
    const allowed = ['application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/zip', 'application/x-zip-compressed'];
    const valid = selectedFiles.filter(f => allowed.includes(f.type));
    if (valid.length !== selectedFiles.length)
      alert(`${selectedFiles.length - valid.length} file(s) skipped — only PDF, DOC/DOCX, ZIP allowed.`);
    setFiles(prev => [...prev, ...valid]);
  };

  const handleFileChange = (e) => validateAndAddFiles(Array.from(e.target.files));
  const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(e.type === "dragenter" || e.type === "dragover"); };
  const handleDrop = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); if (e.dataTransfer.files) validateAndAddFiles(Array.from(e.dataTransfer.files)); };
  const removeFile = (i) => setFiles(files.filter((_, idx) => idx !== i));

  const handleUpload = async () => {
    if (!files.length) return;
    if (associateOption === 'employee' && !selectedEmployee) { alert('Please select an employee first'); return; }
    setUploading(true); setProgress(0); setResults(null);
    try {
      const empName = associateOption === 'employee' ? selectedEmployee : null;
      const resp = await bulkUploadResumes(files, empName, (p) => setProgress(p));
      setResults(resp);
    } catch (err) {
      alert('Upload failed. Please try again.');
    } finally { setUploading(false); }
  };

  const handleClear = () => { setFiles([]); setResults(null); setProgress(0); };

  const handleAddEmployee = () => {
    const name = newEmployeeName.trim();
    if (!name) return;
    if (!employeeList.includes(name)) {
      const updated = [...employeeList, name];
      setEmployeeList(updated);
      localStorage.setItem('zapplic_employee_list', JSON.stringify(updated));
    }
    setSelectedEmployee(name);
    localStorage.setItem('zapplic_employee', name);
    setNewEmployeeName('');
    setDropdownOpen(false);
  };

  const handleRemoveEmployee = (emp) => {
    const updated = employeeList.filter(e => e !== emp);
    setEmployeeList(updated);
    localStorage.setItem('zapplic_employee_list', JSON.stringify(updated));
    if (selectedEmployee === emp) { setSelectedEmployee(null); localStorage.removeItem('zapplic_employee'); }
  };

  const isUploadDisabled = !files.length || uploading || (associateOption === 'employee' && !selectedEmployee);
  const getExt = (f) => f.name.split('.').pop().toLowerCase();

  return (
    <div style={S.page}>
      <div style={S.inner}>
        <div style={S.card}>
          {/* Header */}
          <div style={S.pageHeader}>
            <div style={S.pageIcon}><FiUpload color="white" size={24} /></div>
            <div>
              <h1 style={S.pageTitle}>Bulk Upload</h1>
              <p style={S.pageSub}>Upload multiple resumes for batch AI processing</p>
            </div>
          </div>

          {!results ? (
            <>
              {/* Dropzone */}
              <div
                style={S.dropzone(dragActive, files.length > 0)}
                onDragEnter={handleDrag} onDragLeave={handleDrag}
                onDragOver={handleDrag} onDrop={handleDrop}
                onClick={() => document.getElementById('bulk-file-upload').click()}
              >
                <input id="bulk-file-upload" type="file" accept=".pdf,.doc,.docx,.zip" multiple onChange={handleFileChange} style={{ display: "none" }} />
                <div style={S.dropIcon}>{files.length > 0 ? "📦" : dragActive ? "🎯" : "☁️"}</div>
                <div style={S.dropTitle}>
                  {files.length > 0
                    ? `${files.length} file${files.length > 1 ? "s" : ""} selected — click to add more`
                    : dragActive ? "Release to add files" : "Drag & drop files or click to browse"}
                </div>
                <div style={S.dropSub}>PDF, DOC, DOCX, ZIP · Max 10MB each</div>
              </div>

              {/* File list */}
              {files.length > 0 && (
                <div style={S.fileListCard}>
                  <div style={S.fileListHeader}>
                    <h3 style={S.fileListTitle}>Selected Files ({files.length})</h3>
                    <button style={{ background: "none", border: "none", fontSize: 12, color: "#ef4444", cursor: "pointer", fontWeight: 600 }} onClick={() => setFiles([])}>Clear all</button>
                  </div>
                  <div style={S.fileListScroll}>
                    {files.map((file, i) => (
                      <div key={i} style={S.fileRow}>
                        <div style={S.fileExt(getExt(file))}>{getExt(file)}</div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={S.fileName}>{file.name}</div>
                          <div style={S.fileSize}>{(file.size / 1024).toFixed(1)} KB</div>
                        </div>
                        <button style={S.removeBtn} onClick={(e) => { e.stopPropagation(); removeFile(i); }} title="Remove">
                          <FiTrash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Associate section */}
              <div style={S.associateCard}>
                <div style={S.associateTitle}>
                  <FiUser size={14} style={{ marginRight: 6 }} />
                  Associate resumes with
                </div>
                <div style={S.associateRow}>
                  <select style={S.select} value={associateOption} onChange={e => { setAssociateOption(e.target.value); setDropdownOpen(false); }}>
                    <option value="none">No association</option>
                    <option value="employee">Employee / Recruiter</option>
                  </select>

                  {associateOption === 'employee' && (
                    <div style={{ position: "relative" }}>
                      <button style={S.empTrigger(dropdownOpen)} onClick={() => setDropdownOpen(!dropdownOpen)}>
                        <span style={{ color: selectedEmployee ? "#0f172a" : "#94a3b8" }}>
                          {selectedEmployee || "Select employee"}
                        </span>
                        <span style={{ fontSize: 10, color: "#94a3b8" }}>▾</span>
                      </button>
                      {/* {dropdownOpen && (
                        <div style={S.empDropdown}>
                          <div style={S.empAddSection}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.4px" }}>Add New</div>
                            <div style={S.empAddRow}>
                              <input style={S.empAddInput} placeholder="Employee name..." value={newEmployeeName} onChange={e => setNewEmployeeName(e.target.value)} onKeyDown={e => e.key === "Enter" && handleAddEmployee()} />
                              <button style={S.empAddBtn} onClick={handleAddEmployee}>Add</button>
                            </div>
                          </div>
                          <div style={S.empList}>
                            {employeeList.length === 0 && (
                              <div style={{ padding: "12px 14px", fontSize: 13, color: "#94a3b8", textAlign: "center" }}>No employees yet</div>
                            )}
                            {employeeList.map((emp, i) => (
                              <div key={i} style={S.empItem(selectedEmployee === emp)}>
                                <span style={{ flex: 1 }} onClick={() => { setSelectedEmployee(emp); localStorage.setItem('zapplic_employee', emp); setDropdownOpen(false); }}>{emp}</span>
                                <button style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 13 }} onClick={() => handleRemoveEmployee(emp)}>✕</button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )} */}
                      {dropdownOpen && (
  <div className="absolute mt-2 w-full bg-white border border-gray-200 rounded-xl shadow-xl z-50">

    {/* Add new section */}
    <div className="p-3 border-b">
      <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">
        Add New
      </div>

     <div className="relative">
  <input
    ref={inputRef}
    className="w-full pr-16 px-3 py-2 text-sm border border-gray-200 rounded-lg
               focus:outline-none focus:ring-2 focus:ring-blue-500"
    placeholder="Employee name..."
    value={newEmployeeName}
    onChange={e => setNewEmployeeName(e.target.value)}
    onKeyDown={e => e.key === "Enter" && handleAddEmployee()}
  />

  <button
    onClick={handleAddEmployee}
    className="
      absolute right-1 top-1/2 -translate-y-1/2
      px-3 py-1 text-xs font-semibold text-white
      bg-gradient-to-r from-blue-600 to-purple-600
      rounded-md shadow
      hover:scale-105 active:scale-95 transition
    "
  >
    Add
  </button>
</div>
    </div>

    {/* Employee list */}
    <div className="max-h-48 overflow-y-auto">
      {employeeList.length === 0 && (
        <div className="p-3 text-sm text-gray-400 text-center">
          No employees yet
        </div>
      )}

      {employeeList.map((emp, i) => (
        <div
          key={i}
          className={`flex items-center px-3 py-2 text-sm cursor-pointer hover:bg-blue-50 ${
            selectedEmployee === emp ? "bg-blue-100 font-semibold" : ""
          }`}
        >
          <span
            className="flex-1"
            onClick={() => {
              setSelectedEmployee(emp);
              localStorage.setItem("zapplic_employee", emp);
              setDropdownOpen(false);
            }}
          >
            {emp}
          </span>

          <button
            onClick={() => handleRemoveEmployee(emp)}
            className="text-gray-400 hover:text-red-500 ml-2"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  </div>
)}  
                    </div>
                  )}

                  {selectedEmployee && associateOption === 'employee' && (
                    <span style={{ fontSize: 12, color: "#16a34a", fontWeight: 600 }}>✅ {selectedEmployee}</span>
                  )}
                </div>
              </div>

              {/* Progress */}
              {uploading && (
                <div style={S.progressCard}>
                  <div style={S.progressLabel}>
                    <span>⚙️ Processing resumes with AI...</span>
                    <span>{progress}%</span>
                  </div>
                  <div style={S.progressTrack}>
                    <div style={S.progressBar(progress)} />
                  </div>
                </div>
              )}

              {/* Actions */}
              <div style={S.actionRow}>
                <button style={S.uploadBtn(isUploadDisabled)} onClick={handleUpload} disabled={isUploadDisabled}>
                  {uploading ? (
                    <>
                      <div style={{ width: 18, height: 18, border: "3px solid rgba(255,255,255,0.3)", borderTop: "3px solid white", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                      Processing...
                    </>
                  ) : (
                    <><FiUpload size={17} /> Upload {files.length > 0 ? `${files.length} File${files.length > 1 ? "s" : ""}` : "All Resumes"}</>
                  )}
                </button>
                {files.length > 0 && (
                  <button style={S.clearBtn} onClick={handleClear} disabled={uploading}>Clear</button>
                )}
              </div>

              {/* Tips */}
              <div style={S.tipsCard}>
                <div style={S.tipsTitle}>💡 Tips</div>
                {[
                  "Select multiple files with Ctrl+Click or Cmd+Click",
                  "Upload a ZIP to batch-process many resumes at once",
                  "Max 10MB per file · PDF, DOC, DOCX supported",
                  "AI parses each resume automatically after upload",
                ].map((t, i) => (
                  <div key={i} style={S.tipItem}><span style={{ color: "#22c55e" }}>•</span>{t}</div>
                ))}
              </div>
            </>
          ) : (
            /* ── Results ── */
            <div>
              {/* Stat cards */}
              <div style={S.statGrid}>
                <div style={S.statCard("#64748b")}>
                  <div style={S.statNum("#0f172a")}>{results.total}</div>
                  <div style={S.statLabel}>Total Files</div>
                </div>
                <div style={S.statCard("#16a34a")}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <FiCheckCircle color="#16a34a" size={22} />
                    <div style={S.statNum("#16a34a")}>{results.successful}</div>
                  </div>
                  <div style={S.statLabel}>Successful</div>
                </div>
                <div style={S.statCard("#ef4444")}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <FiXCircle color="#ef4444" size={22} />
                    <div style={S.statNum("#ef4444")}>{results.failed}</div>
                  </div>
                  <div style={S.statLabel}>Failed</div>
                </div>
              </div>

              {/* Success table */}
              {results.successful > 0 && (
                <div style={S.resultSection}>
                  <div style={S.resultHeader("#16a34a")}>
                    <FiCheckCircle size={16} />
                    Successfully Uploaded ({results.successful})
                  </div>
                  <div style={{ overflowX: "auto" }}>
                    <table style={S.table}>
                      <thead style={S.thead}>
                        <tr>
                          {["Filename", "Name", "Email", "Employee", "Quality"].map(h => (
                            <th key={h} style={S.th}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(results.resumes || []).map((r, i) => (
                          <tr key={i} style={S.trResult}>
                            <td style={S.tdResult}><span style={{ fontSize: 12, fontWeight: 600 }}>{r.filename}</span></td>
                            <td style={S.tdResult}>{r.name || "—"}</td>
                            <td style={S.tdResult}>{r.email || "—"}</td>
                            <td style={S.tdResult}>{r.employee_name || "—"}</td>
                            <td style={S.tdResult}>
                              <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 700 }}>
                                <span style={{ width: 7, height: 7, borderRadius: "50%", background: S.qualityDot(r.parsing_quality), display: "inline-block" }} />
                                {r.parsing_quality || "—"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Failed table */}
              {results.failed > 0 && (
                <div style={S.resultSection}>
                  <div style={S.resultHeader("#ef4444")}>
                    <FiAlertCircle size={16} />
                    Failed Uploads ({results.failed})
                  </div>
                  <div style={{ overflowX: "auto" }}>
                    <table style={S.table}>
                      <thead style={{ ...S.thead, background: "#fef2f2" }}>
                        <tr>
                          {["Filename", "Error"].map(h => <th key={h} style={S.th}>{h}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {(results.errors || []).map((e, i) => (
                          <tr key={i} style={S.trResult}>
                            <td style={S.tdResult}>{e.filename}</td>
                            <td style={{ ...S.tdResult, color: "#dc2626" }}>{e.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div style={S.bottomActions}>
                <button style={S.dashBtn} onClick={() => navigate('/dashboard')}>View All Resumes →</button>
                <button style={S.moreBtn} onClick={handleClear}>Upload More</button>
              </div>
            </div>
          )}
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default BulkUploadPage;