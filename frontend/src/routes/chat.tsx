import * as React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Mic, MicOff, Send, MessageSquare, Settings, Plus, X, Upload, Camera } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { TelemetryPill } from "@/components/mindful/telemetry-pill";
import { BreathingOrb, type OrbState } from "@/components/mindful/breathing-orb";
import { CrisisBanner } from "@/components/mindful/crisis-banner";
import { Textarea } from "@/components/ui/textarea";
import { type Message, type ScoreState, emotionsToMood } from "@/lib/mock";
import {
  sendMessage,
  getHistory,
  analyzeAudioV2,
  analyzeFace,
  getMessagesByDate,
  type AudioAnalysisResult,
  type FaceAnalysisResult,
} from "@/lib/api";
import { useFaceCapture } from "@/hooks/use-face-capture";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/chat")({
  head: () => ({
    meta: [
      { title: "Session — Mindful" },
      { name: "description", content: "A private space to think out loud, with text or voice." },
    ],
  }),
  component: ChatPage,
});

// ─── Backend response shape ────────────────────────────────────────────
type FusedEmotions = Record<string, number>;
type ChatResponse = {
  response: string;
  fused_emotions: FusedEmotions;
  mental_health_score: number;
  crisis_detected: boolean;
};

type HistoryEntry = {
  average_score: number;
  date: string;
  dominant_emotion: string;
  total_messages: number;
};

// ─── Per-user chat persistence in localStorage ─────────────────────────
const STORAGE_KEY_PREFIX = "mindful_chat_state:";

type PersistedChatState = {
  messages: Message[];
  score: ScoreState;
  emotions: FusedEmotions | null;
};

function getStorageKey(): string | null {
  const username = localStorage.getItem("username");
  return username ? `${STORAGE_KEY_PREFIX}${username}` : null;
}

function loadChatState(): Partial<PersistedChatState> {
  const key = getStorageKey();
  if (!key) return {};
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveChatState(state: PersistedChatState) {
  const key = getStorageKey();
  if (!key) return;
  try {
    localStorage.setItem(key, JSON.stringify(state));
  } catch {
    // quota or serialization error — ignore
  }
}

function clearChatState() {
  const key = getStorageKey();
  if (!key) return;
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

function ChatPage() {
  const persisted = React.useMemo(() => loadChatState(), []);

  const [messages, setMessages] = React.useState<Message[]>(persisted.messages ?? []);
  const [draft, setDraft] = React.useState("");
  const [mode, setMode] = React.useState<"text" | "voice" | "face">("text");
  const [faceEmotions, setFaceEmotions] = React.useState<Record<string, number> | null>(null);
  const [crisisDemo, setCrisisDemo] = React.useState(false);
  const [score, setScore] = React.useState<ScoreState>(
    persisted.score ?? { value: 100, mood: "calm", trend: "steady" },
  );
  const [emotions, setEmotions] = React.useState<FusedEmotions | null>(persisted.emotions ?? null);
  const [history, setHistory] = React.useState<HistoryEntry[]>([]);
  const [showCrisis, setShowCrisis] = React.useState(false);
  const [crisisDismissed, setCrisisDismissed] = React.useState(false);
  const [thinking, setThinking] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  // Past-session viewing
  const [viewingDate, setViewingDate] = React.useState<string | null>(null);
  const [viewedMessages, setViewedMessages] = React.useState<Message[]>([]);
  const [viewedLoading, setViewedLoading] = React.useState(false);

  // Load real session history on mount
  React.useEffect(() => {
    getHistory()
      .then((data) => setHistory(data?.history ?? []))
      .catch((err) => console.warn("Could not load session history:", err));
  }, []);

  // Persist chat state whenever messages / score / emotions change
  React.useEffect(() => {
    saveChatState({ messages, score, emotions });
  }, [messages, score, emotions]);

  React.useEffect(() => {
    if (score.value < 40 && !crisisDismissed) setShowCrisis(true);
    if (score.value >= 50) setCrisisDismissed(false);
  }, [score.value, crisisDismissed]);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, viewedMessages, thinking]);

  const send = async () => {
    const text = draft.trim();
    if (!text) return;
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text, ts: Date.now() };
    setMessages((m) => [...m, userMsg]);
    setDraft("");
    setThinking(true);

    try {
      const response = (await sendMessage(text, null, faceEmotions)) as ChatResponse;
      setFaceEmotions(null);
      setMessages((m) => [
        ...m,
        { id: `a-${Date.now()}`, role: "ai", text: response.response, ts: Date.now() },
      ]);

      const newScore = response.mental_health_score;
      const previousValue = score.value;
      const trend: ScoreState["trend"] =
        newScore - previousValue > 1 ? "up" : newScore - previousValue < -1 ? "down" : "steady";

      setScore({
        value: Math.round(newScore),
        mood: emotionsToMood(response.fused_emotions, newScore),
        trend,
      });
      setEmotions(response.fused_emotions);
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setThinking(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setScore({ value: 100, mood: "calm", trend: "steady" });
    setEmotions(null);
    setShowCrisis(false);
    setCrisisDismissed(false);
    clearChatState();
  };

  const viewPastSession = async (dateStr: string) => {
    setViewingDate(dateStr);
    setViewedLoading(true);
    setViewedMessages([]);
    try {
      const data = await getMessagesByDate(dateStr);
      const converted: Message[] = data.messages.map((m, i) => ({
        id: `past-${dateStr}-${i}`,
        role: m.role === "assistant" ? "ai" : "user",
        text: m.content,
        ts: m.timestamp ? new Date(m.timestamp).getTime() : Date.now(),
      }));
      setViewedMessages(converted);
    } catch (err) {
      console.error("Failed to load past session", err);
    } finally {
      setViewedLoading(false);
    }
  };

  const returnToToday = () => {
    setViewingDate(null);
    setViewedMessages([]);
  };

  const displayedMessages = viewingDate ? viewedMessages : messages;

  // Called when VoiceMode finishes analyzing audio with HuBERT
  const handleAudioAnalyzed = (result: AudioAnalysisResult) => {
    setEmotions(result.emotions);
  };

  // Called when FaceMode captures and analyzes a frame
  const handleFaceAnalyzed = (result: FaceAnalysisResult) => {
    if (result.face_detected) {
      setFaceEmotions(result.emotions);
      setEmotions(result.emotions);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />

      <div className="mx-auto grid max-w-6xl gap-6 px-4 pb-10 sm:px-6 lg:grid-cols-[280px_1fr]">
        {/* Left rail */}
        <aside className="hidden lg:block">
          <div className="sticky top-24 space-y-4">
            <div className="rounded-2xl border border-border bg-surface-elevated p-3 shadow-soft">
              <div className="flex items-center justify-between px-2 pb-2 pt-1">
                <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Sessions
                </span>
                <button
                  type="button"
                  onClick={clearChat}
                  className="inline-flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label="New session"
                  title="Start a new session"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              <div className="space-y-1">
                <button
                  type="button"
                  onClick={returnToToday}
                  className={cn(
                    "w-full rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    !viewingDate ? "bg-primary-soft" : "hover:bg-muted",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: "var(--primary)" }}
                    />
                    Today
                  </div>
                  <div className="mt-0.5 truncate text-xs text-muted-foreground">
                    {!viewingDate ? "In progress…" : "Click to return"}
                  </div>
                </button>

                {history.length === 0 ? (
                  <div className="rounded-xl px-3 py-3 text-xs text-muted-foreground">
                    Your past sessions will appear here.
                  </div>
                ) : (
                  history.slice(0, 5).map((s, i) => (
                    <button
                      key={`${s.date}-${i}`}
                      type="button"
                      onClick={() => viewPastSession(s.date)}
                      className={cn(
                        "w-full rounded-xl px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        viewingDate === s.date ? "bg-primary-soft" : "hover:bg-muted",
                      )}
                    >
                      <div className="text-sm">{formatDate(s.date)}</div>
                      <div className="mt-0.5 truncate text-xs text-muted-foreground">
                        {capitalize(s.dominant_emotion)} · score {Math.round(s.average_score)}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Mode toggle + settings */}
            <div className="rounded-2xl border border-border bg-surface-elevated p-3 shadow-soft">
              <div className="grid grid-cols-3 gap-1 rounded-xl bg-muted p-1">
                <button
                  type="button"
                  onClick={() => setMode("text")}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
                    mode === "text"
                      ? "bg-surface-elevated shadow-soft text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <MessageSquare className="h-3.5 w-3.5" /> Text
                </button>
                <button
                  type="button"
                  onClick={() => setMode("voice")}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
                    mode === "voice"
                      ? "bg-surface-elevated shadow-soft text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <Mic className="h-3.5 w-3.5" /> Voice
                </button>
                <button
                  type="button"
                  onClick={() => setMode("face")}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
                    mode === "face"
                      ? "bg-surface-elevated shadow-soft text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <Camera className="h-3.5 w-3.5" /> Face
                </button>
              </div>

              <label className="mt-3 flex items-start gap-3 rounded-xl px-2 py-2.5">
                <Settings className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Crisis demo</span>
                    <input
                      type="checkbox"
                      checked={crisisDemo}
                      onChange={(e) => setCrisisDemo(e.target.checked)}
                      className="h-4 w-4 accent-[var(--primary)]"
                    />
                  </div>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                    Drift score below 40 to preview the support flow.
                  </p>
                </div>
              </label>
            </div>

            {/* Emotion breakdown */}
            {emotions && !viewingDate && <EmotionBreakdown emotions={emotions} />}
          </div>
        </aside>

        {/* Main */}
        <section className="flex min-h-[calc(100vh-7rem)] flex-col">
          {/* Top bar */}
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold tracking-tight">
                {viewingDate ? `Session · ${formatDate(viewingDate)}` : "A quiet moment"}
              </h1>
              <p className="text-xs text-muted-foreground">
                {viewingDate
                  ? "A look back. Read-only."
                  : "No rush. We can sit here as long as you need."}
              </p>
            </div>
            <TelemetryPill state={score} />
          </div>

          {showCrisis && !crisisDismissed && !viewingDate && (
            <div className="mb-4">
              <CrisisBanner onDismiss={() => setCrisisDismissed(true)} />
            </div>
          )}

          {mode === "text" ? (
            <>
              {/* Message stream */}
              <div
                ref={scrollRef}
                className="flex-1 space-y-4 overflow-y-auto rounded-3xl border border-border-soft bg-surface-elevated/40 p-4 sm:p-6"
              >
                {viewedLoading && viewingDate ? (
                  <p className="text-center text-sm text-muted-foreground">Loading…</p>
                ) : displayedMessages.length === 0 && viewingDate ? (
                  <p className="text-center text-sm text-muted-foreground">
                    No messages on this day.
                  </p>
                ) : (
                  displayedMessages.map((m) => <MessageBubble key={m.id} message={m} />)
                )}
                {!viewingDate && thinking && (
                  <div className="flex justify-start">
                    <div className="rounded-2xl rounded-bl-md bg-primary-soft px-4 py-3">
                      <span className="inline-flex gap-1">
                        {[0, 150, 300].map((d) => (
                          <span
                            key={d}
                            className="h-1.5 w-1.5 rounded-full bg-foreground/50"
                            style={{
                              animation: `breathe 1.4s cubic-bezier(0.22,1,0.36,1) infinite`,
                              animationDelay: `${d}ms`,
                            }}
                          />
                        ))}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Composer or past-session banner */}
              {viewingDate ? (
                <div className="mt-4 rounded-2xl border border-border bg-surface-elevated p-4 text-center shadow-soft">
                  <p className="text-sm text-muted-foreground">
                    Viewing {formatDate(viewingDate)} · read-only
                  </p>
                  <button
                    type="button"
                    onClick={returnToToday}
                    className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-foreground underline-offset-4 hover:underline"
                  >
                    ← Back to today's session
                  </button>
                </div>
              ) : (
                <div className="mt-4">
                  <div className="glass relative flex items-end gap-2 rounded-2xl p-2.5 shadow-elevated">
                    <Textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          send();
                        }
                      }}
                      placeholder="Whatever's here is welcome…"
                      rows={1}
                      className="min-h-[40px] resize-none border-0 bg-transparent p-2 text-[15px] leading-relaxed shadow-none focus-visible:ring-0"
                    />
                    <button
                      type="button"
                      onClick={() => setMode("voice")}
                      className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label="Switch to voice"
                    >
                      <Mic className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={send}
                      disabled={!draft.trim()}
                      className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-soft transition-all hover:shadow-elevated disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                      aria-label="Send message"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="mt-3 flex items-center justify-between px-1 text-[11px] text-muted-foreground">
                    <span>Press Enter to send · Shift+Enter for a new line</span>
                    <Link to="/summary" className="underline-offset-4 hover:underline">
                      End session
                    </Link>
                  </div>
                </div>
              )}
            </>
          ) : mode === "voice" ? (
            <VoiceMode onExit={() => setMode("text")} onAudioAnalyzed={handleAudioAnalyzed} />
          ) : (
            <FaceMode
              onExit={() => setMode("text")}
              onFaceAnalyzed={handleFaceAnalyzed}
              pendingEmotions={faceEmotions}
            />
          )}
        </section>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const time = new Date(message.ts).toLocaleTimeString("en", {
    hour: "numeric",
    minute: "2-digit",
  });
  return (
    <div
      className={cn(
        "flex animate-[rise-in_0.4s_cubic-bezier(0.22,1,0.36,1)_both]",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div className="max-w-[78%]">
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-[15px] leading-relaxed text-pretty",
            isUser
              ? "rounded-br-md bg-accent-soft text-foreground"
              : "rounded-bl-md bg-primary-soft text-foreground",
          )}
        >
          {message.text}
        </div>
        <div
          className={cn(
            "mt-1 text-[10px] text-muted-foreground/70",
            isUser ? "text-right" : "text-left",
          )}
        >
          {time}
        </div>
      </div>
    </div>
  );
}

// ─── Emotion breakdown card ────────────────────────────────────────────
function EmotionBreakdown({ emotions }: { emotions: FusedEmotions }) {
  const sorted = Object.entries(emotions)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  const max = sorted[0]?.[1] ?? 1;

  return (
    <div className="rounded-2xl border border-border bg-surface-elevated p-4 shadow-soft animate-[rise-in_0.4s_cubic-bezier(0.22,1,0.36,1)_both]">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Emotion breakdown
        </span>
      </div>
      <div className="space-y-2.5">
        {sorted.map(([name, value]) => {
          const pct = max > 0 ? (value / max) * 100 : 0;
          const displayPct = Math.round(value * 100);
          return (
            <div key={name}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="capitalize text-foreground">{name}</span>
                <span className="tabular-nums text-muted-foreground">{displayPct}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
                  style={{
                    width: `${pct}%`,
                    background: "var(--primary)",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[10px] leading-relaxed text-muted-foreground/70">
        Detected by RoBERTa across 12 mental health categories.
      </p>
    </div>
  );
}

// ─── Helpers ───────────────────────────────────────────────────────────
function formatDate(raw: string): string {
  const d = new Date(raw.replace(" ", "T"));
  if (isNaN(d.getTime())) return raw;
  return d.toLocaleDateString("en", { weekday: "short", month: "short", day: "numeric" });
}

function capitalize(s: string): string {
  if (!s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ─── Voice mode (real HuBERT recording + file upload) ──────────────────
function VoiceMode({
  onExit,
  onAudioAnalyzed,
}: {
  onExit: () => void;
  onAudioAnalyzed: (result: AudioAnalysisResult) => void;
}) {
  const { state, duration, start, stop } = useAudioRecorder();
  const [uploading, setUploading] = React.useState(false);
  const [lastResult, setLastResult] = React.useState<AudioAnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const orbState: OrbState = uploading
    ? "processing"
    : state === "recording"
      ? "recording"
      : "idle";

  const label = uploading
    ? "Analyzing audio…"
    : state === "recording"
      ? "Listening…"
      : state === "requesting"
        ? "Allow microphone…"
        : lastResult
          ? `Detected: ${lastResult.dominant_emotion}`
          : "Tap the mic, or upload a file";

  const handleClick = async () => {
    if (uploading) return;
    setErrorMsg(null);

    if (state === "idle") {
      try {
        await start();
      } catch (err: unknown) {
        const name = (err as { name?: string })?.name;
        setErrorMsg(
          name === "NotAllowedError"
            ? "Microphone permission denied"
            : "Could not access microphone",
        );
      }
      return;
    }

    if (state === "recording") {
      try {
        const wav = await stop();
        if (wav.size < 4000) {
          setErrorMsg("Recording too short — try a longer message");
          return;
        }
        setUploading(true);
        const result = await analyzeAudioV2(wav);
        setLastResult(result);
        onAudioAnalyzed(result);
      } catch (err) {
        console.error(err);
        setErrorMsg("Voice analysis failed");
      } finally {
        setUploading(false);
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (!file) return;

    setErrorMsg(null);
    setUploading(true);
    try {
      const result = await analyzeAudioV2(file);
      setLastResult(result);
      onAudioAnalyzed(result);
    } catch (err) {
      console.error(err);
      setErrorMsg("Could not analyze that audio file");
    } finally {
      setUploading(false);
    }
  };

  const fmt = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;

  const buttonDisabled = uploading || state === "requesting";

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center rounded-3xl border border-border-soft bg-surface-elevated/40 p-6">
      <button
        type="button"
        onClick={onExit}
        className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Exit voice mode"
      >
        <X className="h-4 w-4" />
      </button>

      <BreathingOrb state={orbState} />

      <p className="mt-12 text-sm font-medium text-muted-foreground" aria-live="polite">
        {label}
      </p>

      {state === "recording" && (
        <p className="mt-2 font-mono text-xs text-muted-foreground/70">{fmt(duration)}</p>
      )}

      {lastResult && state === "idle" && !uploading && (
        <p className="mt-2 text-xs text-muted-foreground/80">
          {Math.round(lastResult.confidence * 100)}% confidence
        </p>
      )}

      {errorMsg && <p className="mt-2 text-xs text-support">{errorMsg}</p>}

      <button
        type="button"
        onClick={handleClick}
        disabled={buttonDisabled}
        className={cn(
          "mt-6 inline-flex h-14 w-14 items-center justify-center rounded-full shadow-elevated transition-all duration-300",
          "hover:shadow-floating hover:-translate-y-0.5 disabled:opacity-60",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          state === "recording" ? "bg-support" : "bg-primary",
        )}
        aria-label={state === "recording" ? "Stop recording" : "Start recording"}
      >
        {state === "recording" ? (
          <MicOff className="h-5 w-5 text-support-foreground" />
        ) : (
          <Mic className="h-5 w-5 text-primary-foreground" />
        )}
      </button>

      {/* File upload — fallback for demos with clean dataset samples */}
      {state !== "recording" && !uploading && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/wav,audio/mpeg,audio/mp4,audio/x-m4a,audio/*"
            className="hidden"
            onChange={handleFileSelect}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-4 py-2 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Upload audio file"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload audio file
          </button>
        </>
      )}
    </div>
  );
}

// ─── Face mode (webcam capture + image upload) ─────────────────────────
function FaceMode({
  onExit,
  onFaceAnalyzed,
  pendingEmotions,
}: {
  onExit: () => void;
  onFaceAnalyzed: (result: FaceAnalysisResult) => void;
  pendingEmotions: Record<string, number> | null;
}) {
  const { state, videoRef, start, stop, capture } = useFaceCapture();
  const [analyzing, setAnalyzing] = React.useState(false);
  const [lastResult, setLastResult] = React.useState<FaceAnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleStart = async () => {
    setErrorMsg(null);
    try {
      await start();
    } catch (err: unknown) {
      const name = (err as { name?: string })?.name;
      setErrorMsg(name === "NotAllowedError" ? "Camera permission denied" : "Could not access camera");
    }
  };

  const handleCapture = async () => {
    setErrorMsg(null);
    setAnalyzing(true);
    try {
      const blob = await capture();
      const result = await analyzeFace(blob);
      setLastResult(result);
      if (!result.face_detected) {
        setErrorMsg("No face detected — move closer or improve lighting");
      } else {
        onFaceAnalyzed(result);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(
        (err as any)?.response?.data?.detail ||
        (err as any)?.response?.data?.error ||
        "Face analysis failed",
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (!file) return;
    setErrorMsg(null);
    setAnalyzing(true);
    try {
      const result = await analyzeFace(file);
      setLastResult(result);
      if (!result.face_detected) {
        setErrorMsg("No face detected in image");
      } else {
        onFaceAnalyzed(result);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(
        (err as any)?.response?.data?.detail ||
        (err as any)?.response?.data?.error ||
        "Could not analyze that image",
      );
    } finally {
      setAnalyzing(false);
    }
  };

  React.useEffect(() => {
    return () => stop();
  }, [stop]);

  const label = analyzing
    ? "Analyzing…"
    : lastResult?.face_detected
      ? `Detected: ${lastResult.dominant_emotion}`
      : state === "active"
        ? "Tap capture to analyze your expression"
        : state === "requesting"
          ? "Allow camera…"
          : "Start camera or upload an image";

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center rounded-3xl border border-border-soft bg-surface-elevated/40 p-6">
      <button
        type="button"
        onClick={onExit}
        className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Exit face mode"
      >
        <X className="h-4 w-4" />
      </button>

      {state === "active" ? (
        <div className="relative mb-4 overflow-hidden rounded-2xl border border-border shadow-soft">
          <video ref={videoRef} className="h-48 w-64 object-cover" muted playsInline />
          {analyzing && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60">
              <span className="text-xs text-muted-foreground">Analyzing…</span>
            </div>
          )}
        </div>
      ) : (
        <div className="mb-4 flex h-48 w-64 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/30">
          <Camera className="h-8 w-8 text-muted-foreground/40" />
        </div>
      )}

      <p className="text-sm font-medium text-muted-foreground" aria-live="polite">
        {label}
      </p>

      {lastResult?.face_detected && !analyzing && (
        <p className="mt-1 text-xs text-muted-foreground/80">
          {Math.round(lastResult.confidence * 100)}% confidence
          {pendingEmotions ? " · will be used in next message" : ""}
        </p>
      )}

      {errorMsg && <p className="mt-2 text-xs text-support">{errorMsg}</p>}

      <div className="mt-6 flex items-center gap-3">
        {state !== "active" ? (
          <button
            type="button"
            onClick={handleStart}
            disabled={state === "requesting"}
            className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-primary shadow-elevated transition-all hover:shadow-floating hover:-translate-y-0.5 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            aria-label="Start camera"
          >
            <Camera className="h-5 w-5 text-primary-foreground" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleCapture}
            disabled={analyzing}
            className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-primary shadow-elevated transition-all hover:shadow-floating hover:-translate-y-0.5 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            aria-label="Capture expression"
          >
            <Camera className="h-5 w-5 text-primary-foreground" />
          </button>
        )}
      </div>

      {!analyzing && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/*"
            className="hidden"
            onChange={handleFileSelect}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-4 py-2 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Upload image"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload image
          </button>
        </>
      )}
    </div>
  );
}
