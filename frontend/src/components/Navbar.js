import React, { useState, useEffect, useRef } from "react";
import { FiList, FiUpload, FiFileText, FiChevronDown, FiUser, FiZap, FiFilter, FiLogOut } from "react-icons/fi";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";

const S = {
  nav: { background: "white", borderBottom: "1px solid #e8edf5", position: "sticky", top: 0, zIndex: 50, boxShadow: "0 1px 12px rgba(0,0,0,0.06)" },
  inner: { maxWidth: 1200, margin: "0 auto", padding: "0 20px", display: "flex", alignItems: "center", justifyContent: "space-between", height: 60 },

  // Logo
  logoRow: { display: "flex", alignItems: "center", gap: 10, textDecoration: "none" },
  logoIcon: { width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" },
  logoText: { fontSize: 20, fontWeight: 900, background: "linear-gradient(135deg, #2563eb, #7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", letterSpacing: "-0.3px" },

  // Nav links
  navLinks: { display: "flex", alignItems: "center", gap: 2 },
  navLink: (active) => ({
    display: "flex", alignItems: "center", gap: 6, padding: "7px 13px", borderRadius: 9, fontSize: 13, fontWeight: 600, textDecoration: "none", transition: "all 0.15s", whiteSpace: "nowrap",
    background: active ? "linear-gradient(135deg, #2563eb, #7c3aed)" : "transparent",
    color: active ? "white" : "#64748b",
    boxShadow: active ? "0 2px 10px rgba(37,99,235,0.25)" : "none",
  }),
  newBadge: { fontSize: 9, fontWeight: 800, background: "#22c55e", color: "white", padding: "2px 5px", borderRadius: 6, letterSpacing: "0.3px", textTransform: "uppercase" },

  // Right side
  rightRow: { display: "flex", alignItems: "center", gap: 8 },

  // Profile button
  profileBtn: (open) => ({ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px", borderRadius: 10, border: `1px solid ${open ? "#bfdbfe" : "#e2e8f0"}`, background: open ? "#eff6ff" : "white", cursor: "pointer", transition: "all 0.15s", fontSize: 13, fontWeight: 600, color: "#374151" }),
  profileAvatar: { width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg, #2563eb, #7c3aed)", color: "white", fontSize: 12, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center" },
  chevron: (open) => ({ transition: "transform 0.2s", transform: open ? "rotate(180deg)" : "rotate(0deg)", color: "#94a3b8" }),

  // Dropdown
  dropdown: { position: "absolute", top: "calc(100% + 8px)", right: 0, width: 240, background: "white", borderRadius: 14, border: "1px solid #e8edf5", boxShadow: "0 12px 40px rgba(0,0,0,0.12)", overflow: "hidden", zIndex: 100 },
  dropHeader: { padding: "14px 16px", background: "linear-gradient(135deg, #f0f4ff, #faf5ff)", borderBottom: "1px solid #e8edf5" },
  dropName: { fontSize: 14, fontWeight: 800, color: "#0f172a", marginBottom: 2 },
  dropEmail: { fontSize: 12, color: "#64748b" },
  dropItem: (danger) => ({ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "10px 16px", background: "none", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, color: danger ? "#ef4444" : "#374151", textAlign: "left", transition: "background 0.1s", borderTop: danger ? "1px solid #f1f5f9" : "none" }),

  // Mobile nav
  mobileNav: { borderTop: "1px solid #f1f5f9", padding: "8px 20px 10px", display: "flex", gap: 4, overflowX: "auto" },
  mobileLink: (active) => ({ display: "flex", alignItems: "center", gap: 5, padding: "6px 11px", borderRadius: 8, fontSize: 12, fontWeight: 600, textDecoration: "none", whiteSpace: "nowrap", flexShrink: 0, background: active ? "linear-gradient(135deg, #2563eb, #7c3aed)" : "#f8fafc", color: active ? "white" : "#64748b" }),
};

const NAV_ITEMS = [
  { path: "/smart-upload",    label: "Smart Upload",    icon: <FiZap size={15} />,    mobile: "Smart",    isNew: true },
  { path: "/dashboard",       label: "All Resumes",     icon: <FiList size={15} />,   mobile: "Resumes",  isNew: false },
  { path: "/advanced-search", label: "Advanced Search", icon: <FiFilter size={15} />, mobile: "Search",   isNew: true },
  { path: "/bulk-upload",     label: "Bulk Upload",     icon: <FiUpload size={15} />, mobile: "Bulk",     isNew: false },
];

export default function Navbar({ setIsAuthenticated }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [profile, setProfile] = useState(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    api.get("/auth/profile").then(r => setProfile(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const handler = (e) => { if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setDropdownOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setIsAuthenticated(false);
    navigate("/login");
  };

  const isActive = (path) => location.pathname.startsWith(path);
  const firstName = profile?.full_name?.split(" ")[0] || "User";
  const initial = firstName.charAt(0).toUpperCase();

  return (
    <nav style={S.nav}>
      <div style={S.inner}>
        {/* Logo */}
        <Link to="/dashboard" style={S.logoRow}>
          <div style={S.logoIcon}><FiFileText color="white" size={18} /></div>
          <span style={S.logoText}>Zapplic</span>
        </Link>

        {/* Desktop Nav */}
        <div style={S.navLinks} className="hidden md:flex">
          {NAV_ITEMS.map(({ path, label, icon, isNew }) => (
            <Link key={path} to={path} style={S.navLink(isActive(path))}>
              {icon}
              {label}
              {isNew && <span style={S.newBadge}>NEW</span>}
            </Link>
          ))}
        </div>

        {/* Right — profile dropdown */}
        <div style={S.rightRow}>
          <div style={{ position: "relative" }} ref={dropdownRef}>
            <button style={S.profileBtn(dropdownOpen)} onClick={() => setDropdownOpen(!dropdownOpen)}>
              <div style={S.profileAvatar}>{initial}</div>
              <span>{firstName}</span>
              <FiChevronDown size={14} style={S.chevron(dropdownOpen)} />
            </button>

            {dropdownOpen && (
              <div style={S.dropdown}>
                <div style={S.dropHeader}>
                  <div style={S.dropName}>{profile?.full_name || "Recruiter"}</div>
                  <div style={S.dropEmail}>{profile?.email}</div>
                  {profile?.phone_number && <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>{profile.phone_number}</div>}
                </div>
                <button style={S.dropItem(false)} onClick={() => { setDropdownOpen(false); navigate("/profile"); }}
                  onMouseEnter={e => e.currentTarget.style.background = "#f8fafc"}
                  onMouseLeave={e => e.currentTarget.style.background = "none"}
                >
                  <FiUser size={15} color="#64748b" /> View Profile
                </button>
                <button style={S.dropItem(true)} onClick={handleLogout}
                  onMouseEnter={e => e.currentTarget.style.background = "#fef2f2"}
                  onMouseLeave={e => e.currentTarget.style.background = "none"}
                >
                  <FiLogOut size={15} /> Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Nav
      <div style={S.mobileNav} className="md:hidden">
        {NAV_ITEMS.map(({ path, icon, mobile, isNew }) => (
          <Link key={path} to={path} style={S.mobileLink(isActive(path))}>
            {React.cloneElement(icon, { size: 13 })}
            {mobile}
            {isNew && <span style={{ ...S.newBadge, fontSize: 8 }}>N</span>}
          </Link>
        ))}
      </div> */}
    </nav>
  );
}