import * as React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Mic, MicOff, Send, MessageSquare, Settings, Plus, X } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { TelemetryPill } from "@/components/mindful/telemetry-pill";
import { BreathingOrb, type OrbState } from "@/components/mindful/breathing-orb";
import { CrisisBanner } from "@/components/mindful/crisis-banner";
import { Textarea } from "@/components/ui/textarea";
import {
  SESSIONS,
  type Message,
  type ScoreState,
} from "@/lib/mock";
import { sendMessage } from "@/lib/api";
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

function ChatPage() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [draft, setDraft] = React.useState("");
  const [mode, setMode] = React.useState<"text" | "voice">("text");
  const [orbState, setOrbState] = React.useState<OrbState>("idle");
  const [crisisDemo, setCrisisDemo] = React.useState(false);
  const [score, setScore] = React.useState<ScoreState>({ value: 100, mood: "calm", trend: "steady" });
  const [showCrisis, setShowCrisis] = React.useState(false);
  const [crisisDismissed, setCrisisDismissed] = React.useState(false);
  const [thinking, setThinking] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (score.value < 40 && !crisisDismissed) setShowCrisis(true);
    if (score.value >= 50) setCrisisDismissed(false);
  }, [score.value, crisisDismissed]);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const send = async () => {
    const text = draft.trim();
    if (!text) return;
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text, ts: Date.now() };
    setMessages((m) => [...m, userMsg]);
    setDraft("");
    setThinking(true);
    
    try {
      const response = await sendMessage(text);
      setMessages((m) => [
        ...m,
        { id: `a-${Date.now()}`, role: "ai", text: response.response, ts: Date.now() },
      ]);
      setScore({
        value: response.mental_health_score,
        mood: response.mental_health_score > 60 ? "calm" : "anxious",
        trend: "steady"
      });
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setThinking(false);
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
                  className="inline-flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label="New session"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              <div className="space-y-1">
                <button className="w-full rounded-xl bg-primary-soft px-3 py-2.5 text-left text-sm font-medium transition-colors">
                  <div className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--primary)" }} />
                    Today
                  </div>
                  <div className="mt-0.5 truncate text-xs text-muted-foreground">In progress…</div>
                </button>
                {SESSIONS.slice(0, 5).map((s) => (
                  <button
                    key={s.id}
                    className="w-full rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <div className="text-sm">
                      {new Date(s.date).toLocaleDateString("en", { weekday: "short", month: "short", day: "numeric" })}
                    </div>
                    <div className="mt-0.5 truncate text-xs text-muted-foreground">{s.summary}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Mode toggle + settings */}
            <div className="rounded-2xl border border-border bg-surface-elevated p-3 shadow-soft">
              <div className="grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
                <button
                  type="button"
                  onClick={() => setMode("text")}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
                    mode === "text" ? "bg-surface-elevated shadow-soft text-foreground" : "text-muted-foreground",
                  )}
                >
                  <MessageSquare className="h-3.5 w-3.5" /> Text
                </button>
                <button
                  type="button"
                  onClick={() => setMode("voice")}
                  className={cn(
                    "inline-flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
                    mode === "voice" ? "bg-surface-elevated shadow-soft text-foreground" : "text-muted-foreground",
                  )}
                >
                  <Mic className="h-3.5 w-3.5" /> Voice
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
          </div>
        </aside>

        {/* Main */}
        <section className="flex min-h-[calc(100vh-7rem)] flex-col">
          {/* Top bar */}
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold tracking-tight">A quiet moment</h1>
              <p className="text-xs text-muted-foreground">No rush. We can sit here as long as you need.</p>
            </div>
            <TelemetryPill state={score} />
          </div>

          {showCrisis && !crisisDismissed && (
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
                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
                {thinking && (
                  <div className="flex justify-start">
                    <div className="rounded-2xl rounded-bl-md bg-primary-soft px-4 py-3">
                      <span className="inline-flex gap-1">
                        {[0, 150, 300].map((d) => (
                          <span
                            key={d}
                            className="h-1.5 w-1.5 rounded-full bg-foreground/50"
                            style={{ animation: `breathe 1.4s cubic-bezier(0.22,1,0.36,1) infinite`, animationDelay: `${d}ms` }}
                          />
                        ))}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Composer */}
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
            </>
          ) : (
            <VoiceMode
              orbState={orbState}
              setOrbState={setOrbState}
              onExit={() => setMode("text")}
            />
          )}
        </section>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const time = new Date(message.ts).toLocaleTimeString("en", { hour: "numeric", minute: "2-digit" });
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
        <div className={cn("mt-1 text-[10px] text-muted-foreground/70", isUser ? "text-right" : "text-left")}>
          {time}
        </div>
      </div>
    </div>
  );
}

function VoiceMode({
  orbState,
  setOrbState,
  onExit,
}: {
  orbState: OrbState;
  setOrbState: (s: OrbState) => void;
  onExit: () => void;
}) {
  const toggle = () => {
    if (orbState === "idle") {
      setOrbState("recording");
    } else if (orbState === "recording") {
      setOrbState("processing");
      setTimeout(() => setOrbState("idle"), 2200);
    }
  };

  const label =
    orbState === "recording" ? "Listening…" : orbState === "processing" ? "Thinking…" : "Tap to speak";

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

      <button
        type="button"
        onClick={toggle}
        disabled={orbState === "processing"}
        className={cn(
          "mt-6 inline-flex h-14 w-14 items-center justify-center rounded-full shadow-elevated transition-all duration-300",
          "hover:shadow-floating hover:-translate-y-0.5 disabled:opacity-60",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          orbState === "recording" ? "bg-support" : "bg-primary",
        )}
        aria-label={orbState === "recording" ? "Stop recording" : "Start recording"}
      >
        {orbState === "recording" ? (
          <MicOff className="h-5 w-5 text-support-foreground" />
        ) : (
          <Mic className="h-5 w-5 text-primary-foreground" />
        )}
      </button>
    </div>
  );
}
