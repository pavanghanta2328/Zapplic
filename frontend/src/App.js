import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { FiFileText } from "react-icons/fi";

// Auth pages
import Login from "./components/Login";
import Register from "./components/Register";
import ProtectedRoute from "./components/ProtectedRoute";

// App pages
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
// import SearchPage from "./pages/SearchPage";
import ResumeDetailPage from "./pages/ResumeDetailPage";
import EditResumePage from "./pages/EditResumePage";
import OAuthCallback from "./pages/OAuthCallback";
import BulkUploadPage from "./pages/BulkUploadPage";
import RecruiterProfilePage from "./pages/RecruiterProfilePage";
import Navbar from "./components/Navbar";

// ✅ NEW: Comprehensive Search & Version Manager
import ComprehensiveSearch from "./components/Comprehensivesearch";
import { SmartUpload } from "./components/Resumeversionmanager";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const location = useLocation();

  // ✅ Routes where navbar should be displayed
  const navbarRoutes = [
    "/dashboard",
    // "/upload",
    // "/search",
    "/advanced-search",   // ← NEW
    "/smart-upload",      // ← NEW
    "/bulk-upload",
    "/resume",
    "/profile"
  ];

  // Check if current path should show navbar
  const shouldShowNavbar = navbarRoutes.some(route =>
    location.pathname.startsWith(route)
  );

  // ✅ Check token on app load
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  // ✅ Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        {/* Animated Background Blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
          <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
        </div>

        <div className="text-center relative z-10">
          <div className="relative inline-flex mb-6">
            <div className="w-20 h-20 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <FiFileText className="text-blue-600 text-2xl animate-pulse" />
            </div>
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Zapplic
          </h2>
          <p className="text-gray-600 font-medium">Loading your workspace...</p>
        </div>

        <style jsx>{`
          @keyframes blob {
            0% { transform: translate(0px, 0px) scale(1); }
            33% { transform: translate(30px, -50px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
            100% { transform: translate(0px, 0px) scale(1); }
          }
          .animate-blob { animation: blob 7s infinite; }
          .animation-delay-2000 { animation-delay: 2s; }
          .animation-delay-4000 { animation-delay: 4s; }
        `}</style>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ===== NAVBAR (Conditional) ===== */}
      {shouldShowNavbar && isAuthenticated && (
        <Navbar setIsAuthenticated={setIsAuthenticated} />
      )}

      {/* ===== ROUTES ===== */}
      <main className={shouldShowNavbar ? "" : "max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"}>
        <Routes>

          {/* -------- AUTH ROUTES -------- */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          <Route
            path="/login"
            element={<Login onLoginSuccess={() => setIsAuthenticated(true)} />}
          />

          <Route path="/register" element={<Register />} />

          {/* OAuth Callbacks */}
          <Route path="/oauth/callback" element={<OAuthCallback />} />

          {/* -------- PROTECTED ROUTES -------- */}

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />



          {/* ✅ NEW: Comprehensive Search Route */}
          <Route
            path="/advanced-search"
            element={
              <ProtectedRoute>
                <ComprehensiveSearch />
              </ProtectedRoute>
            }
          />

          {/* ✅ NEW: Smart Upload Route (with version management) */}
          <Route
            path="/smart-upload"
            element={
              <ProtectedRoute>
                <SmartUpload
                  onUploadComplete={(data) => {
                    console.log("Upload complete:", data);
                  }}
                />
              </ProtectedRoute>
            }
          />

          <Route
            path="/bulk-upload"
            element={
              <ProtectedRoute>
                <BulkUploadPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/resume/:id"
            element={
              <ProtectedRoute>
                <ResumeDetailPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/resume/:id/edit"
            element={
              <ProtectedRoute>
                <EditResumePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <RecruiterProfilePage />
              </ProtectedRoute>
            }
          />

          {/* -------- FALLBACK ROUTE -------- */}
          <Route path="*" element={<Navigate to="/login" replace />} />

        </Routes>
      </main>
    </div>
  );
}

export default App;