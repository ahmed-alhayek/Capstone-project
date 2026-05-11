import axios from "axios";

const BASE_URL = "http://localhost:5000/api";

// Endpoints that should NOT trigger a redirect-to-login on 401.
// (Otherwise a wrong password on /login redirects you to /login,
// killing the error toast and making login look broken.)
const AUTH_ENDPOINTS = ["/login", "/register", "/forgot-password", "/reset-password"];

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    const isAuthRequest = AUTH_ENDPOINTS.some((path) => url.includes(path));

    // Only kick out to /login on 401 for protected endpoints,
    // not when the auth attempt itself fails.
    if (error.response?.status === 401 && !isAuthRequest) {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// ── AUTH ──────────────────────────────────────────────────────────────────────

export const registerUser = async (username: string, email: string, password: string) => {
  const response = await api.post("/register", { username, email, password });
  return response.data;
};

export const loginUser = async (email: string, password: string) => {
  const response = await api.post("/login", { email, password });
  return response.data;
};

export const forgotPassword = async (email: string) => {
  const response = await api.post("/forgot-password", { email });
  return response.data;
};

export const resetPassword = async (token: string, password: string) => {
  const response = await api.post("/reset-password", { token, password });
  return response.data;
};

// ── CHAT ──────────────────────────────────────────────────────────────────────

export const sendMessage = async (message: string, audioEmotions: any = null) => {
  const response = await api.post("/chat", {
    message,
    audio_emotions: audioEmotions,
  });
  return response.data;
};

export const analyzeAudio = async (audioBlob: Blob) => {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  const response = await api.post("/analyze-audio", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

// ── PHASE 2C AUDIO (HuBERT) ───────────────────────────────────────────────────

export interface AudioAnalysisResult {
  emotions: Record<string, number>;
  dominant_emotion: string;
  confidence: number;
  model: string;
}

export const analyzeAudioV2 = async (audioBlob: Blob): Promise<AudioAnalysisResult> => {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  const response = await api.post<AudioAnalysisResult>("/analyze-audio-v2", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

// ── SESSION ───────────────────────────────────────────────────────────────────

export const endSession = async () => {
  const response = await api.post("/session/end");
  return response.data;
};

export interface HistoryEntry {
  date: string;
  average_score: number;
  dominant_emotion: string;
  total_messages: number;
}

export interface HistoryResponse {
  history: HistoryEntry[];
}

export const getHistory = async (): Promise<HistoryResponse> => {
  const response = await api.get<HistoryResponse>("/session/history");
  return response.data;
};

export interface PastMessage {
  role: "user" | "assistant";
  content: string;
  emotions: Record<string, number> | null;
  score: number | null;
  timestamp: string | null;
}

export interface MessagesByDateResponse {
  messages: PastMessage[];
  date: string;
}

export const getMessagesByDate = async (date: string): Promise<MessagesByDateResponse> => {
  const response = await api.get<MessagesByDateResponse>("/messages", { params: { date } });
  return response.data;
};

// ── HEALTH ────────────────────────────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;
