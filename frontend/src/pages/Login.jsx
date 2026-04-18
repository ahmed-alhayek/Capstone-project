// mental_health_companion/frontend/src/pages/Login.jsx

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { loginUser } from "../api/api";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ── Handle input changes ───────────────────────────────────────────────────
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  // ── Handle form submission ─────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Basic validation
    if (!form.email || !form.password) {
      setError("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      const data = await loginUser(form.email, form.password);
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Left Panel — Branding */}
      <motion.div
        style={styles.leftPanel}
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Animated Robot */}
        <motion.div
          style={styles.robotContainer}
          animate={{ y: [0, -15, 0] }}
          transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        >
          <svg width="160" height="160" viewBox="0 0 160 160">
            {/* Robot Head */}
            <rect
              x="30"
              y="30"
              width="100"
              height="80"
              rx="20"
              fill="#3b82f6"
            />
            {/* Eyes */}
            <motion.circle
              cx="60"
              cy="60"
              r="12"
              fill="white"
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            />
            <motion.circle
              cx="100"
              cy="60"
              r="12"
              fill="white"
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            />
            <circle cx="60" cy="60" r="6" fill="#1e40af" />
            <circle cx="100" cy="60" r="6" fill="#1e40af" />
            {/* Mouth */}
            <rect
              x="50"
              y="85"
              width="60"
              height="10"
              rx="5"
              fill="white"
              opacity="0.8"
            />
            {/* Antenna */}
            <line
              x1="80"
              y1="30"
              x2="80"
              y2="10"
              stroke="#3b82f6"
              strokeWidth="4"
            />
            <circle cx="80" cy="8" r="6" fill="#60a5fa" />
            {/* Body */}
            <rect
              x="40"
              y="115"
              width="80"
              height="35"
              rx="10"
              fill="#2563eb"
            />
            {/* Arms */}
            <rect x="10" y="118" width="28" height="12" rx="6" fill="#3b82f6" />
            <rect
              x="122"
              y="118"
              width="28"
              height="12"
              rx="6"
              fill="#3b82f6"
            />
            {/* Chest light */}
            <motion.circle
              cx="80"
              cy="132"
              r="8"
              fill="#60a5fa"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
          </svg>
        </motion.div>

        <h1 style={styles.brandTitle}>MindCompanion</h1>
        <p style={styles.brandSubtitle}>
          Your AI-powered mental health companion. <br />
          We listen. We understand. We care.
        </p>

        {/* Feature bullets */}
        <div style={styles.features}>
          {[
            "🧠 Emotion Detection",
            "💬 AI Companion",
            "📊 Wellness Tracking",
          ].map((f, i) => (
            <motion.div
              key={i}
              style={styles.featureItem}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.2 }}
            >
              {f}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Right Panel — Login Form */}
      <motion.div
        style={styles.rightPanel}
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={styles.formCard}>
          <h2 style={styles.formTitle}>Welcome Back</h2>
          <p style={styles.formSubtitle}>Sign in to continue your journey</p>

          {/* Error message */}
          {error && (
            <motion.div
              style={styles.errorBox}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              ⚠️ {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div style={styles.inputGroup}>
              <label style={styles.label}>Email Address</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                style={styles.input}
                required
              />
            </div>

            {/* Password */}
            <div style={styles.inputGroup}>
              <label style={styles.label}>Password</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="••••••••"
                style={styles.input}
                required
              />
            </div>

            {/* Submit Button */}
            <motion.button
              type="submit"
              style={{
                ...styles.submitBtn,
                opacity: loading ? 0.7 : 1,
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={loading}
            >
              {loading ? "⏳ Signing in..." : "Sign In →"}
            </motion.button>
          </form>

          {/* Register link */}
          <p style={styles.switchText}>
            Don't have an account?{" "}
            <Link to="/register" style={styles.link}>
              Create one here
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

// ── STYLES ────────────────────────────────────────────────────────────────────
const styles = {
  container: {
    display: "flex",
    minHeight: "100vh",
    backgroundColor: "#f0f4f8",
  },
  leftPanel: {
    flex: 1,
    background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "60px 40px",
    color: "white",
  },
  robotContainer: {
    marginBottom: "30px",
    filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.3))",
  },
  brandTitle: {
    fontSize: "2.5rem",
    fontWeight: "800",
    marginBottom: "15px",
    letterSpacing: "-0.5px",
  },
  brandSubtitle: {
    fontSize: "1.1rem",
    opacity: 0.85,
    textAlign: "center",
    lineHeight: 1.7,
    marginBottom: "40px",
  },
  features: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    width: "100%",
    maxWidth: "280px",
  },
  featureItem: {
    backgroundColor: "rgba(255,255,255,0.15)",
    borderRadius: "10px",
    padding: "12px 20px",
    fontSize: "0.95rem",
    backdropFilter: "blur(10px)",
  },
  rightPanel: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px",
  },
  formCard: {
    backgroundColor: "white",
    borderRadius: "24px",
    padding: "50px 40px",
    width: "100%",
    maxWidth: "420px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.08)",
  },
  formTitle: {
    fontSize: "2rem",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "8px",
  },
  formSubtitle: {
    color: "#64748b",
    fontSize: "1rem",
    marginBottom: "30px",
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: "10px",
    padding: "12px 16px",
    color: "#dc2626",
    fontSize: "0.9rem",
    marginBottom: "20px",
  },
  inputGroup: {
    marginBottom: "20px",
  },
  label: {
    display: "block",
    fontSize: "0.875rem",
    fontWeight: "600",
    color: "#374151",
    marginBottom: "8px",
  },
  input: {
    width: "100%",
    padding: "14px 16px",
    borderRadius: "12px",
    border: "2px solid #e2e8f0",
    fontSize: "1rem",
    outline: "none",
    transition: "border-color 0.2s",
    boxSizing: "border-box",
  },
  submitBtn: {
    width: "100%",
    padding: "16px",
    backgroundColor: "#3b82f6",
    color: "white",
    border: "none",
    borderRadius: "12px",
    fontSize: "1rem",
    fontWeight: "700",
    cursor: "pointer",
    marginTop: "10px",
    marginBottom: "24px",
  },
  switchText: {
    textAlign: "center",
    color: "#64748b",
    fontSize: "0.9rem",
  },
  link: {
    color: "#3b82f6",
    fontWeight: "600",
    textDecoration: "none",
  },
};
