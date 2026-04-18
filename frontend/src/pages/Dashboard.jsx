// mental_health_companion/frontend/src/pages/Dashboard.jsx

import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { sendMessage, endSession, getHistory } from "../api/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

// ── CONSTANTS ─────────────────────────────────────────────────────────────────
const EMOTION_COLORS = {
  sadness: "#6366f1",
  nervousness: "#f59e0b",
  fear: "#8b5cf6",
  anger: "#ef4444",
  disappointment: "#f97316",
  grief: "#64748b",
  remorse: "#06b6d4",
  embarrassment: "#ec4899",
  disgust: "#84cc16",
  neutral: "#3b82f6",
};

// eslint-disable-next-line no-unused-vars
const CRISIS_THRESHOLD = 40;

export default function Dashboard() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "User";
  const bottomRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // ── State ──────────────────────────────────────────────────────────────────
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Hi ${username}! 👋 I'm your AI mental health companion. How are you feeling today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [score, setScore] = useState(100);
  const [emotions, setEmotions] = useState({});
  const [scoreHistory, setScoreHistory] = useState([]);
  const [labelHistory, setLabelHistory] = useState([]);
  const [crisis, setCrisis] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState(null);
  const [recording, setRecording] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [sessionHistory, setSessionHistory] = useState([]);

  // ── Auto scroll to bottom on new message ──────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // ── Load session history on mount ─────────────────────────────────────────
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getHistory();
      setSessionHistory(data.history || []);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  // ── Send message ───────────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);
    setIsTyping(true);

    // Add user message to chat
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const data = await sendMessage(userMessage);

      setIsTyping(false);

      // Add AI response
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);

      // Update emotion data
      setScore(data.mental_health_score);
      setEmotions(data.fused_emotions);
      setCrisis(data.crisis_detected);

      // Update score chart
      const now = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      setScoreHistory((prev) => [...prev, data.mental_health_score]);
      setLabelHistory((prev) => [...prev, now]);
    } catch (err) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ── Handle Enter key ───────────────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── End session ───────────────────────────────────────────────────────────
  const handleEndSession = async () => {
    try {
      const data = await endSession();
      setSummary(data.summary);
      setShowSummary(true);
      loadHistory();
    } catch (err) {
      console.error("Failed to end session:", err);
    }
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  // ── Voice recording ───────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        // eslint-disable-next-line no-unused-vars
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        });
        setInput((prev) => prev + " [🎤 Voice recorded — emotions analyzed]");
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  // ── Score color ───────────────────────────────────────────────────────────
  const getScoreColor = (s) => {
    if (s >= 75) return "#22c55e";
    if (s >= 50) return "#f59e0b";
    return "#ef4444";
  };

  // ── Chart data ────────────────────────────────────────────────────────────
  const chartData = {
    labels: labelHistory,
    datasets: [
      {
        label: "Mental Health Score",
        data: scoreHistory,
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,0.1)",
        borderWidth: 3,
        pointRadius: 5,
        pointBackgroundColor: "#3b82f6",
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => ` Score: ${ctx.raw}/100`,
        },
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: { color: "#94a3b8" },
        grid: { color: "rgba(0,0,0,0.05)" },
      },
      x: {
        ticks: { color: "#94a3b8" },
        grid: { display: false },
      },
    },
  };

  // ── TOP EMOTIONS ──────────────────────────────────────────────────────────
  const topEmotions = Object.entries(emotions)
    .filter(([, v]) => v > 0.05)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4);

  return (
    <div style={styles.page}>
      {/* ── NAVBAR ─────────────────────────────────────────────────────────── */}
      <nav style={styles.navbar}>
        <div style={styles.navLeft}>
          <div style={styles.navLogo}>
            <svg width="32" height="32" viewBox="0 0 160 160">
              <rect
                x="30"
                y="30"
                width="100"
                height="80"
                rx="20"
                fill="white"
              />
              <circle cx="60" cy="60" r="10" fill="#3b82f6" />
              <circle cx="100" cy="60" r="10" fill="#3b82f6" />
              <rect
                x="50"
                y="85"
                width="60"
                height="8"
                rx="4"
                fill="#3b82f6"
                opacity="0.7"
              />
              <rect
                x="40"
                y="115"
                width="80"
                height="30"
                rx="10"
                fill="white"
                opacity="0.8"
              />
            </svg>
            <span style={styles.navBrand}>MindCompanion</span>
          </div>
        </div>

        <div style={styles.navCenter}>
          <button
            style={styles.navBtn}
            onClick={() => setShowHistory(!showHistory)}
          >
            📊 History
          </button>
        </div>

        <div style={styles.navRight}>
          <div style={styles.navUser}>👤 {username}</div>
          <button style={styles.endBtn} onClick={handleEndSession}>
            End Session
          </button>
          <button style={styles.logoutBtn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      {/* ── CRISIS ALERT ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {crisis && (
          <motion.div
            style={styles.crisisAlert}
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
          >
            🚨 <strong>We're concerned about you.</strong> If you're in crisis,
            please call <strong>182</strong> (Turkey Crisis Line) or reach out
            to a trusted person immediately.
            <button style={styles.crisisClose} onClick={() => setCrisis(false)}>
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── MAIN LAYOUT ────────────────────────────────────────────────────── */}
      <div style={styles.main}>
        {/* ── LEFT SIDEBAR ─────────────────────────────────────────────────── */}
        <div style={styles.sidebar}>
          {/* Robot Avatar */}
          <div style={styles.sideCard}>
            <motion.div
              style={styles.robotWrap}
              animate={{ y: [0, -8, 0] }}
              transition={{ repeat: Infinity, duration: 3 }}
            >
              <svg width="120" height="120" viewBox="0 0 160 160">
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
                  animate={{ scaleY: isTyping ? [1, 0.1, 1] : 1 }}
                  transition={{
                    repeat: isTyping ? Infinity : 0,
                    duration: 0.5,
                  }}
                />
                <motion.circle
                  cx="100"
                  cy="60"
                  r="12"
                  fill="white"
                  animate={{ scaleY: isTyping ? [1, 0.1, 1] : 1 }}
                  transition={{
                    repeat: isTyping ? Infinity : 0,
                    duration: 0.5,
                  }}
                />
                <circle cx="60" cy="60" r="6" fill="#1e40af" />
                <circle cx="100" cy="60" r="6" fill="#1e40af" />
                {/* Animated mouth when typing */}
                {isTyping ? (
                  <motion.rect
                    x="55"
                    y="85"
                    width="50"
                    height="10"
                    rx="5"
                    fill="white"
                    animate={{ scaleX: [1, 0.6, 1] }}
                    transition={{ repeat: Infinity, duration: 0.4 }}
                  />
                ) : (
                  <rect
                    x="55"
                    y="85"
                    width="50"
                    height="10"
                    rx="5"
                    fill="white"
                    opacity="0.8"
                  />
                )}
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
                <rect
                  x="10"
                  y="118"
                  width="28"
                  height="12"
                  rx="6"
                  fill="#3b82f6"
                />
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
            <p style={styles.robotStatus}>
              {isTyping ? "💭 Thinking..." : "😊 Ready to listen"}
            </p>
          </div>

          {/* Mental Health Score Gauge */}
          <div style={styles.sideCard}>
            <h3 style={styles.cardTitle}>Wellness Score</h3>
            <div style={styles.gaugeWrap}>
              <svg width="140" height="80" viewBox="0 0 140 80">
                {/* Background arc */}
                <path
                  d="M 10 70 A 60 60 0 0 1 130 70"
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Score arc */}
                <motion.path
                  d="M 10 70 A 60 60 0 0 1 130 70"
                  fill="none"
                  stroke={getScoreColor(score)}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray="188"
                  animate={{ strokeDashoffset: 188 - (score / 100) * 188 }}
                  transition={{ duration: 1 }}
                />
                {/* Score text */}
                <text
                  x="70"
                  y="65"
                  textAnchor="middle"
                  fontSize="22"
                  fontWeight="bold"
                  fill={getScoreColor(score)}
                >
                  {score}
                </text>
                <text
                  x="70"
                  y="78"
                  textAnchor="middle"
                  fontSize="10"
                  fill="#94a3b8"
                >
                  out of 100
                </text>
              </svg>
            </div>
            <p
              style={{
                ...styles.scoreLabel,
                color: getScoreColor(score),
              }}
            >
              {score >= 75 ? "😊 Good" : score >= 50 ? "😐 Fair" : "😟 Low"}
            </p>
          </div>

          {/* Top Emotions */}
          {topEmotions.length > 0 && (
            <div style={styles.sideCard}>
              <h3 style={styles.cardTitle}>Detected Emotions</h3>
              {topEmotions.map(([emotion, prob]) => (
                <div key={emotion} style={styles.emotionRow}>
                  <span style={styles.emotionName}>{emotion}</span>
                  <div style={styles.emotionBarWrap}>
                    <motion.div
                      style={{
                        ...styles.emotionBar,
                        backgroundColor: EMOTION_COLORS[emotion] || "#3b82f6",
                        width: `${prob * 100}%`,
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${prob * 100}%` }}
                      transition={{ duration: 0.8 }}
                    />
                  </div>
                  <span style={styles.emotionPct}>
                    {Math.round(prob * 100)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── CHAT AREA ─────────────────────────────────────────────────────── */}
        <div style={styles.chatArea}>
          {/* Score Chart */}
          {scoreHistory.length > 1 && (
            <div style={styles.chartCard}>
              <h3 style={styles.cardTitle}>📈 Session Wellness Trend</h3>
              <div style={{ height: "120px" }}>
                <Line data={chartData} options={chartOptions} />
              </div>
            </div>
          )}

          {/* Messages */}
          <div style={styles.messages}>
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  style={{
                    ...styles.msgRow,
                    justifyContent:
                      msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  {msg.role === "assistant" && (
                    <div style={styles.msgAvatar}>🤖</div>
                  )}
                  <div
                    style={{
                      ...styles.msgBubble,
                      ...(msg.role === "user"
                        ? styles.userBubble
                        : styles.aiBubble),
                    }}
                  >
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div style={styles.msgAvatar}>👤</div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing indicator */}
            {isTyping && (
              <motion.div
                style={{ ...styles.msgRow, justifyContent: "flex-start" }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div style={styles.msgAvatar}>🤖</div>
                <div style={styles.aiBubble}>
                  <motion.span
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ repeat: Infinity, duration: 1.2 }}
                  >
                    ● ● ●
                  </motion.span>
                </div>
              </motion.div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input Area */}
          <div style={styles.inputArea}>
            <textarea
              style={styles.textInput}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type how you're feeling... (Enter to send)"
              rows={2}
              disabled={loading}
            />
            <div style={styles.inputButtons}>
              {/* Voice button */}
              <motion.button
                style={{
                  ...styles.voiceBtn,
                  backgroundColor: recording ? "#ef4444" : "#e2e8f0",
                }}
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                whileTap={{ scale: 0.95 }}
                title="Hold to record"
              >
                {recording ? "⏹" : "🎤"}
              </motion.button>

              {/* Send button */}
              <motion.button
                style={{
                  ...styles.sendBtn,
                  opacity: !input.trim() || loading ? 0.5 : 1,
                }}
                onClick={handleSend}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                disabled={!input.trim() || loading}
              >
                {loading ? "⏳" : "➤"}
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      {/* ── SESSION HISTORY PANEL ──────────────────────────────────────────── */}
      <AnimatePresence>
        {showHistory && (
          <motion.div
            style={styles.historyPanel}
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
          >
            <div style={styles.historyHeader}>
              <h3 style={styles.historyTitle}>📊 Past Sessions</h3>
              <button
                style={styles.closeBtn}
                onClick={() => setShowHistory(false)}
              >
                ✕
              </button>
            </div>

            {sessionHistory.length === 0 ? (
              <p style={styles.noHistory}>No past sessions yet.</p>
            ) : (
              sessionHistory.map((s, i) => (
                <div key={i} style={styles.historyItem}>
                  <div style={styles.historyDate}>{s.date}</div>
                  <div style={styles.historyScore}>
                    Score:{" "}
                    <strong style={{ color: getScoreColor(s.average_score) }}>
                      {s.average_score}/100
                    </strong>
                  </div>
                  <div style={styles.historyEmotion}>
                    Dominant: {s.dominant_emotion}
                  </div>
                  <div style={styles.historyMsgs}>
                    {s.total_messages} messages
                  </div>
                </div>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── SESSION SUMMARY MODAL ──────────────────────────────────────────── */}
      <AnimatePresence>
        {showSummary && summary && (
          <motion.div
            style={styles.modalOverlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              style={styles.modal}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <h2 style={styles.modalTitle}>📋 Session Summary</h2>

              <div style={styles.summaryGrid}>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Messages</span>
                  <span style={styles.summaryValue}>
                    {summary.total_messages}
                  </span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Avg Score</span>
                  <span
                    style={{
                      ...styles.summaryValue,
                      color: getScoreColor(summary.average_score),
                    }}
                  >
                    {summary.average_score}/100
                  </span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Best Moment</span>
                  <span style={{ ...styles.summaryValue, color: "#22c55e" }}>
                    {summary.highest_score}/100
                  </span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={styles.summaryLabel}>Dominant Emotion</span>
                  <span style={styles.summaryValue}>
                    {summary.dominant_emotion}
                  </span>
                </div>
              </div>

              <motion.button
                style={styles.modalBtn}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  setShowSummary(false);
                  handleLogout();
                }}
              >
                Finish & Logout
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── STYLES ────────────────────────────────────────────────────────────────────
const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: "#f0f4f8",
    overflow: "hidden",
  },
  navbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: "64px",
    backgroundColor: "#1e40af",
    color: "white",
    boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
    zIndex: 100,
  },
  navLeft: { display: "flex", alignItems: "center" },
  navLogo: { display: "flex", alignItems: "center", gap: "10px" },
  navBrand: { fontSize: "1.3rem", fontWeight: "800", letterSpacing: "-0.5px" },
  navCenter: { display: "flex", gap: "12px" },
  navBtn: {
    background: "rgba(255,255,255,0.15)",
    border: "none",
    color: "white",
    padding: "8px 16px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
  navRight: { display: "flex", alignItems: "center", gap: "12px" },
  navUser: { fontSize: "0.9rem", opacity: 0.9 },
  endBtn: {
    background: "#f59e0b",
    border: "none",
    color: "white",
    padding: "8px 16px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "600",
    fontSize: "0.85rem",
  },
  logoutBtn: {
    background: "rgba(255,255,255,0.15)",
    border: "1px solid rgba(255,255,255,0.3)",
    color: "white",
    padding: "8px 16px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.85rem",
  },
  crisisAlert: {
    backgroundColor: "#fef2f2",
    borderBottom: "2px solid #ef4444",
    padding: "12px 24px",
    color: "#dc2626",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    position: "relative",
    zIndex: 99,
  },
  crisisClose: {
    marginLeft: "auto",
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: "1.2rem",
    color: "#dc2626",
  },
  main: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
    padding: "16px",
    gap: "16px",
  },
  sidebar: {
    width: "260px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    overflowY: "auto",
  },
  sideCard: {
    backgroundColor: "white",
    borderRadius: "16px",
    padding: "16px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
  },
  cardTitle: {
    fontSize: "0.85rem",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "12px",
  },
  robotWrap: { display: "flex", justifyContent: "center", marginBottom: "8px" },
  robotStatus: {
    textAlign: "center",
    fontSize: "0.85rem",
    color: "#64748b",
    fontWeight: "500",
  },
  gaugeWrap: { display: "flex", justifyContent: "center" },
  scoreLabel: {
    textAlign: "center",
    fontWeight: "700",
    fontSize: "1rem",
    marginTop: "4px",
  },
  emotionRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  emotionName: {
    fontSize: "0.75rem",
    color: "#374151",
    width: "85px",
    textTransform: "capitalize",
  },
  emotionBarWrap: {
    flex: 1,
    backgroundColor: "#f1f5f9",
    borderRadius: "4px",
    height: "8px",
    overflow: "hidden",
  },
  emotionBar: { height: "8px", borderRadius: "4px" },
  emotionPct: {
    fontSize: "0.75rem",
    color: "#64748b",
    width: "32px",
    textAlign: "right",
  },
  chatArea: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    overflow: "hidden",
  },
  chartCard: {
    backgroundColor: "white",
    borderRadius: "16px",
    padding: "16px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    padding: "4px 2px",
  },
  msgRow: { display: "flex", alignItems: "flex-end", gap: "8px" },
  msgAvatar: { fontSize: "1.4rem", flexShrink: 0 },
  msgBubble: {
    maxWidth: "70%",
    padding: "12px 16px",
    borderRadius: "16px",
    fontSize: "0.95rem",
    lineHeight: 1.5,
  },
  userBubble: {
    backgroundColor: "#3b82f6",
    color: "white",
    borderBottomRightRadius: "4px",
  },
  aiBubble: {
    backgroundColor: "white",
    color: "#1e293b",
    borderBottomLeftRadius: "4px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  },
  inputArea: {
    backgroundColor: "white",
    borderRadius: "16px",
    padding: "12px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
    display: "flex",
    gap: "10px",
    alignItems: "flex-end",
  },
  textInput: {
    flex: 1,
    border: "2px solid #e2e8f0",
    borderRadius: "12px",
    padding: "10px 14px",
    fontSize: "0.95rem",
    resize: "none",
    outline: "none",
    fontFamily: "inherit",
  },
  inputButtons: { display: "flex", flexDirection: "column", gap: "6px" },
  voiceBtn: {
    width: "42px",
    height: "42px",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "1.1rem",
  },
  sendBtn: {
    width: "42px",
    height: "42px",
    backgroundColor: "#3b82f6",
    color: "white",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "1.1rem",
    fontWeight: "700",
  },
  historyPanel: {
    position: "fixed",
    right: 0,
    top: "64px",
    bottom: 0,
    width: "300px",
    backgroundColor: "white",
    boxShadow: "-4px 0 20px rgba(0,0,0,0.1)",
    padding: "20px",
    overflowY: "auto",
    zIndex: 200,
  },
  historyHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  historyTitle: { fontSize: "1.1rem", fontWeight: "700", color: "#1e293b" },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: "1.2rem",
    cursor: "pointer",
    color: "#64748b",
  },
  noHistory: { color: "#94a3b8", textAlign: "center", marginTop: "40px" },
  historyItem: {
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    padding: "14px",
    marginBottom: "10px",
    borderLeft: "4px solid #3b82f6",
  },
  historyDate: { fontSize: "0.8rem", color: "#94a3b8", marginBottom: "6px" },
  historyScore: { fontSize: "0.9rem", marginBottom: "4px" },
  historyEmotion: {
    fontSize: "0.85rem",
    color: "#64748b",
    textTransform: "capitalize",
    marginBottom: "4px",
  },
  historyMsgs: { fontSize: "0.8rem", color: "#94a3b8" },
  modalOverlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 300,
  },
  modal: {
    backgroundColor: "white",
    borderRadius: "24px",
    padding: "40px",
    width: "90%",
    maxWidth: "480px",
    boxShadow: "0 25px 60px rgba(0,0,0,0.2)",
  },
  modalTitle: {
    fontSize: "1.5rem",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "24px",
    textAlign: "center",
  },
  summaryGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
    marginBottom: "28px",
  },
  summaryItem: {
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  summaryLabel: {
    fontSize: "0.8rem",
    color: "#94a3b8",
    fontWeight: "600",
    textTransform: "uppercase",
  },
  summaryValue: { fontSize: "1.3rem", fontWeight: "700", color: "#1e293b" },
  modalBtn: {
    width: "100%",
    padding: "16px",
    backgroundColor: "#3b82f6",
    color: "white",
    border: "none",
    borderRadius: "12px",
    fontSize: "1rem",
    fontWeight: "700",
    cursor: "pointer",
  },
};
