/**
 * App.tsx
 * =========
 * Router configuration for the whole app: public auth routes (Login,
 * Register), and every other route wrapped in <ProtectedRoute> (requires
 * a valid session) with role-specific dashboards additionally gated by
 * <ProtectedRoute allow={[...]}>.
 */

import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { ThemeProvider } from "@/hooks/useTheme";
import { AppLayout } from "@/layouts/AppLayout";
import { PageLoader } from "@/components/Loader";
import type { Role } from "@/types";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Home from "@/pages/Home";
import StudentDashboard from "@/pages/StudentDashboard";
import FacultyDashboard from "@/pages/FacultyDashboard";
import PredictionPage from "@/pages/PredictionPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import Profile from "@/pages/Profile";
import Settings from "@/pages/Settings";

// ---------------------------------------------------------------------------
// Route guards
// ---------------------------------------------------------------------------

/** Requires a valid session. Optionally restricts to a set of roles. */
function ProtectedRoute({ children, allow }: { children: ReactNode; allow?: Role[] }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return <PageLoader label="Checking your session..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allow && user && !allow.includes(user.role)) return <Navigate to="/" replace />;

  return <>{children}</>;
}

/** Redirects an already-authenticated user away from Login/Register. */
function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <PageLoader label="Loading..." />;
  if (isAuthenticated) return <Navigate to="/" replace />;

  return <>{children}</>;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Home />} />
        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute allow={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/dashboard"
          element={
            <ProtectedRoute allow={["faculty", "admin"]}>
              <FacultyDashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/prediction" element={<PredictionPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ---------------------------------------------------------------------------
// Root App
// ---------------------------------------------------------------------------

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
