// mental_health_companion/frontend/src/pages/Register.jsx

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { registerUser } from "../api/api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm: "",
  });
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

    // Validation
    if (!form.username || !form.email || !form.password || !form.confirm) {
      setError("Please fill in all fields");
      return;
    }
    if (form.username.length < 3) {
      setError("Username must be at least 3 characters");
      return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const data = await registerUser(form.username, form.email, form.password);
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.error || "Registration failed. Please try again.",
      );
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
            <rect
              x="30"
              y="30"
              width="100"
              height="80"
              rx="20"
              fill="#3b82f6"
            />
            <motion.circle
              cx="60"
              cy="60"
              r="12"
              fill="white"
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ repeat: Infinity, duration: 4 }}
            />
            <motion.circle
              cx="100"
              cy="60"
              r="12"
              fill="white"
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ repeat: Infinity, duration: 4 }}
            />
            <circle cx="60" cy="60" r="6" fill="#1e40af" />
            <circle cx="100" cy="60" r="6" fill="#1e40af" />
            {/* Smile mouth */}
            <path
              d="M 55 88 Q 80 102 105 88"
              stroke="white"
              strokeWidth="4"
              fill="none"
              strokeLinecap="round"
            />
            <line
              x1="80"
              y1="30"
              x2="80"
              y2="10"
              stroke="#3b82f6"
              strokeWidth="4"
            />
            <circle cx="80" cy="8" r="6" fill="#60a5fa" />
            <rect
              x="40"
              y="115"
              width="80"
              height="35"
              rx="10"
              fill="#2563eb"
            />
            <rect x="10" y="118" width="28" height="12" rx="6" fill="#3b82f6" />
            <rect
              x="122"
              y="118"
              width="28"
              height="12"
              rx="6"
              fill="#3b82f6"
            />
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

        <h1 style={styles.brandTitle}>Join MindCompanion</h1>
        <p style={styles.brandSubtitle}>
          Start your mental wellness journey today. <br />
          Your AI companion is ready to help.
        </p>

        <div style={styles.features}>
          {[
            "🔒 Your data is private & secure",
            "📈 Track your wellness over time",
            "🤖 24/7 AI support available",
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

      {/* Right Panel — Register Form */}
      <motion.div
        style={styles.rightPanel}
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={styles.formCard}>
          <h2 style={styles.formTitle}>Create Account</h2>
          <p style={styles.formSubtitle}>Fill in your details to get started</p>

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
            {/* Username */}
            <div style={styles.inputGroup}>
              <label style={styles.label}>Username</label>
              <input
                type="text"
                name="username"
                value={form.username}
                onChange={handleChange}
                placeholder="e.g. ahmed123"
                style={styles.input}
                required
              />
            </div>

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
                placeholder="Min. 6 characters"
                style={styles.input}
                required
              />
            </div>

            {/* Confirm Password */}
            <div style={styles.inputGroup}>
              <label style={styles.label}>Confirm Password</label>
              <input
                type="password"
                name="confirm"
                value={form.confirm}
                onChange={handleChange}
                placeholder="Repeat your password"
                style={styles.input}
                required
              />
            </div>

            <motion.button
              type="submit"
              style={{ ...styles.submitBtn, opacity: loading ? 0.7 : 1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={loading}
            >
              {loading ? "⏳ Creating account..." : "Create Account →"}
            </motion.button>
          </form>

          <p style={styles.switchText}>
            Already have an account?{" "}
            <Link to="/login" style={styles.link}>
              Sign in here
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
    marginBottom: "18px",
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
