// mental_health_companion/frontend/src/api/api.js

import axios from "axios";

const BASE_URL = "http://localhost:5000/api";

// ── Create axios instance with base URL ───────────────────────────────────────
const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Automatically attach JWT token to every request ───────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auto-logout when token expires or is invalid ──────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// ── AUTH ──────────────────────────────────────────────────────────────────────

export const registerUser = async (username, email, password) => {
  const response = await api.post("/register", { username, email, password });
  return response.data;
};

export const loginUser = async (email, password) => {
  const response = await api.post("/login", { email, password });
  return response.data;
};

// ── CHAT ──────────────────────────────────────────────────────────────────────

export const sendMessage = async (message, audioEmotions = null) => {
  const response = await api.post("/chat", {
    message,
    audio_emotions: audioEmotions,
  });
  return response.data;
};

export const analyzeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  const response = await api.post("/analyze-audio", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

// ── SESSION ───────────────────────────────────────────────────────────────────

export const endSession = async () => {
  const response = await api.post("/session/end");
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get("/session/history");
  return response.data;
};

// ── HEALTH ────────────────────────────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};
