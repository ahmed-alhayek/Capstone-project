// Mock data layer (kept for Summary/History pages) + real-emotion helpers.

export type Mood = "calm" | "hopeful" | "reflective" | "tender" | "heavy" | "anxious" | "low";

export type Message = {
  id: string;
  role: "ai" | "user";
  text: string;
  ts: number;
};

export type Session = {
  id: string;
  date: string; // ISO
  durationMin: number;
  moodStart: Mood;
  moodEnd: Mood;
  score: number; // 0-100
  topics: string[];
  summary: string;
};

export const MOOD_META: Record<Mood, { label: string; tone: string; emoji: string }> = {
  calm: { label: "Calm", tone: "primary", emoji: "🌿" },
  hopeful: { label: "Hopeful", tone: "primary", emoji: "🌅" },
  reflective: { label: "Reflective", tone: "accent", emoji: "🌙" },
  tender: { label: "Tender", tone: "accent", emoji: "🤍" },
  heavy: { label: "Heavy", tone: "support", emoji: "🌧" },
  anxious: { label: "Anxious", tone: "support", emoji: "🌬" },
  low: { label: "Low", tone: "support", emoji: "🌫" },
};

// ─── REAL emotion helper ────────────────────────────────────────────
// Maps RoBERTa's 12-category fused_emotions object to the existing Mood type.
// This lets the chat use REAL emotions while keeping the visual design the same.
const EMOTION_TO_MOOD: Record<string, Mood> = {
  joy: "calm",
  love: "calm",
  excitement: "hopeful",
  neutral: "reflective",
  embarrassment: "tender",
  remorse: "tender",
  disappointment: "heavy",
  disgust: "heavy",
  sadness: "low",
  fear: "anxious",
  nervousness: "anxious",
  anger: "anxious",
};

export function emotionsToMood(emotions: Record<string, number>, score: number): Mood {
  // Find dominant emotion (highest score)
  let topName = "";
  let topVal = -Infinity;
  for (const [name, val] of Object.entries(emotions)) {
    if (val > topVal) {
      topVal = val;
      topName = name;
    }
  }

  // If neutral dominates strongly, fall back to score-based mood
  if (topName === "neutral" && topVal > 0.5) {
    if (score < 40) return "low";
    if (score < 55) return "heavy";
    if (score < 68) return "reflective";
    if (score < 80) return "hopeful";
    return "calm";
  }

  return EMOTION_TO_MOOD[topName] ?? "reflective";
}

// ─── Below: legacy mock data for Summary/History pages (do not break) ─
// Deterministic seeded RNG so charts don't jitter between renders
function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(7);

function pick<T>(arr: T[]): T {
  return arr[Math.floor(rand() * arr.length)];
}

const TOPIC_POOL = [
  "work stress",
  "family",
  "sleep",
  "self-talk",
  "boundaries",
  "grief",
  "uncertainty",
  "burnout",
  "friendship",
  "creative block",
  "body image",
  "money",
  "loneliness",
  "transitions",
];

const MOODS: Mood[] = ["calm", "hopeful", "reflective", "tender", "heavy", "anxious", "low"];

export function generateSessions(count = 28): Session[] {
  const out: Session[] = [];
  const now = Date.now();
  for (let i = 0; i < count; i++) {
    const score = Math.round(45 + rand() * 45);
    const topics = Array.from(
      new Set(Array.from({ length: 1 + Math.floor(rand() * 2) }, () => pick(TOPIC_POOL))),
    );
    out.push({
      id: `s-${i}`,
      date: new Date(
        now - i * 24 * 60 * 60 * 1000 - Math.floor(rand() * 8) * 3600_000,
      ).toISOString(),
      durationMin: 8 + Math.floor(rand() * 28),
      moodStart: pick(MOODS),
      moodEnd: pick(MOODS),
      score,
      topics,
      summary: pick([
        "You named what was weighing on you, and gave it less power.",
        "Some softness returned by the end. That counts.",
        "You stayed with discomfort instead of running from it.",
        "A small reframe shifted the day.",
        "You let yourself rest in not-knowing.",
      ]),
    });
  }
  return out.reverse();
}

export const SESSIONS = generateSessions();

// Mood timeline for charts (last 30 days)
export function moodTimeline() {
  const now = Date.now();
  return Array.from({ length: 30 }, (_, i) => {
    const day = new Date(now - (29 - i) * 24 * 60 * 60 * 1000);
    const base = 60 + Math.sin(i / 4) * 12 + (rand() - 0.5) * 10;
    return {
      day: day.toLocaleDateString("en", { month: "short", day: "numeric" }),
      score: Math.max(28, Math.min(95, Math.round(base))),
      iso: day.toISOString(),
    };
  });
}

// Heatmap data — 12 weeks x 7 days intensity 0-3
export function heatmapData() {
  return Array.from({ length: 12 }, (_, w) =>
    Array.from({ length: 7 }, (_, d) => ({
      week: w,
      day: d,
      intensity: rand() < 0.35 ? 0 : Math.floor(rand() * 4),
    })),
  );
}

// Canned AI replies — gentle, varied, not sycophantic
const AI_REPLIES = [
  "Thank you for telling me that. What part feels heaviest right now?",
  "That sounds like a lot to be carrying. Take a slow breath with me — there's no rush here.",
  "I hear you. Can you say more about when this started feeling this way?",
  "It makes sense that you'd feel that. What would feel kind to yourself in this moment?",
  "Mm. Let's slow down for a second. What's underneath the frustration, do you think?",
  "You don't have to have it figured out. Just being here is enough.",
  "I notice you mentioned that twice. Sometimes what we repeat is what most needs hearing.",
  "What would the most compassionate version of you say to you right now?",
];

export function nextAIReply(): string {
  return pick(AI_REPLIES);
}

// Drifting wellness score generator with optional crisis demo
export type ScoreState = { value: number; mood: Mood; trend: "up" | "down" | "steady" };

export function driftScore(prev: number, crisisDemo = false): ScoreState {
  const target = crisisDemo ? 32 : 68;
  const pull = (target - prev) * 0.04;
  const noise = (rand() - 0.5) * 6;
  const value = Math.max(15, Math.min(95, Math.round(prev + pull + noise)));
  const delta = value - prev;
  const trend: ScoreState["trend"] = delta > 1 ? "up" : delta < -1 ? "down" : "steady";
  let mood: Mood = "calm";
  if (value < 40) mood = "low";
  else if (value < 55) mood = "heavy";
  else if (value < 68) mood = "reflective";
  else if (value < 80) mood = "hopeful";
  else mood = "calm";
  return { value, mood, trend };
}

export const INITIAL_MESSAGES: Message[] = [
  {
    id: "m-0",
    role: "ai",
    text: "Hi. I'm here whenever you're ready. We can go at whatever pace feels right.",
    ts: Date.now() - 60_000,
  },
];

export const INSIGHTS = [
  {
    title: "Evenings are lighter for you",
    body: "Across the past month, your sessions after 7pm trend 14 points higher than morning ones.",
  },
  {
    title: "Naming it helps",
    body: "On days you mentioned a specific feeling word, your closing score lifted by an average of 9 points.",
  },
  {
    title: "Sundays are tender",
    body: "A gentle dip on Sunday afternoons — not unusual. Worth a softer plan for the day.",
  },
];
