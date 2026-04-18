// mental_health_companion/frontend/src/App.jsx

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";

// ── Helper: check if user is logged in ───────────────────────────────────────
const isAuthenticated = () => {
  return localStorage.getItem("token") !== null;
};

// ── Protected Route: redirects to login if not authenticated ─────────────────
const ProtectedRoute = ({ children }) => {
  return isAuthenticated() ? children : <Navigate to="/login" />;
};

// ── Public Route: redirects to dashboard if already logged in ────────────────
const PublicRoute = ({ children }) => {
  return !isAuthenticated() ? children : <Navigate to="/dashboard" />;
};

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Default route → redirect to login */}
        <Route path="/" element={<Navigate to="/login" />} />

        {/* Public routes — only for non-logged-in users */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected route — only for logged-in users */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}
