import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/site-header";
import { InsightCard } from "@/components/mindful/insight-card";
import { GlassPanel } from "@/components/mindful/glass-panel";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { INSIGHTS, MOOD_META } from "@/lib/mock";
import { getHistory, type HistoryEntry } from "@/lib/api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History — Mindful" },
      { name: "description", content: "Your sessions over time, told gently." },
    ],
  }),
  component: HistoryPage,
});

const RANGES = [
  { id: "week", label: "Week", days: 7 },
  { id: "month", label: "Month", days: 30 },
  { id: "quarter", label: "90 days", days: 90 },
] as const;

function HistoryPage() {
  const [range, setRange] = React.useState<(typeof RANGES)[number]["id"]>("month");
  const [sessions, setSessions] = React.useState<HistoryEntry[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    getHistory()
      .then((data) => setSessions(data.history || []))
      .catch((err) => console.error("Failed to fetch history", err))
      .finally(() => setLoading(false));
  }, []);

  // Trend chart data — driven by real history, range-filtered
  const data = React.useMemo(() => {
    const r = RANGES.find((x) => x.id === range)!;
    return sessions.slice(-Math.min(r.days, sessions.length)).map((s) => ({
      day: s.date,
      score: Math.round(s.average_score),
    }));
  }, [range, sessions]);

  const avg = data.length > 0 ? Math.round(data.reduce((a, b) => a + b.score, 0) / data.length) : 0;

  // Heatmap — last 12 weeks (84 days) keyed by date, intensity from total_messages
  const heatmap = React.useMemo(() => {
    const today = new Date();
    const totalDays = 12 * 7;

    const byDate = new Map<string, number>();
    sessions.forEach((s) => {
      const d = new Date(s.date);
      if (!isNaN(d.getTime())) {
        byDate.set(d.toISOString().slice(0, 10), s.total_messages);
      }
    });

    const flat: Array<{ intensity: number }> = [];
    for (let i = totalDays - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const key = date.toISOString().slice(0, 10);
      const messages = byDate.get(key) || 0;
      const intensity = messages === 0 ? 0 : messages <= 5 ? 1 : messages <= 15 ? 2 : 3;
      flat.push({ intensity });
    }

    const weeks: Array<Array<{ intensity: number }>> = [];
    for (let w = 0; w < 12; w++) {
      weeks.push(flat.slice(w * 7, (w + 1) * 7));
    }
    return weeks;
  }, [sessions]);

  const recentSessions = React.useMemo(() => [...sessions].reverse().slice(0, 10), [sessions]);

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-4 pb-16 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Your unfolding</h1>
            <p className="mt-2 text-sm text-muted-foreground text-pretty">
              The arc of how you've been showing up — without judgment.
            </p>
          </div>
          <div className="glass inline-flex rounded-full p-1">
            {RANGES.map((r) => (
              <button
                key={r.id}
                onClick={() => setRange(r.id)}
                className={cn(
                  "rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-all",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  range === r.id
                    ? "bg-primary text-primary-foreground shadow-soft"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Trend chart */}
        <GlassPanel
          elevated
          className="mt-8 p-5 sm:p-6 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]"
        >
          <div className="flex items-baseline justify-between">
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Wellness trend
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {data.length > 0 ? avg : "—"}
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  {data.length > 0 ? "average" : "no data yet"}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-4 h-56 sm:h-64">
            {loading ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Loading…
              </div>
            ) : data.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Once you've had a few sessions, the arc will appear here.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
                  <defs>
                    <linearGradient id="fillScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--border-soft)" vertical={false} />
                  <XAxis
                    dataKey="day"
                    stroke="var(--muted-foreground)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    stroke="var(--muted-foreground)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    domain={[20, 100]}
                  />
                  <Tooltip
                    cursor={{ stroke: "var(--border)", strokeWidth: 1 }}
                    contentStyle={{
                      background: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      boxShadow: "var(--shadow-elevated)",
                      fontSize: 12,
                      color: "var(--popover-foreground)",
                    }}
                    labelStyle={{ color: "var(--muted-foreground)", marginBottom: 4 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="var(--primary)"
                    strokeWidth={2.5}
                    fill="url(#fillScore)"
                    animationDuration={900}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </GlassPanel>

        {/* Heatmap + insights */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <GlassPanel className="p-5 sm:p-6">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Session intensity · last 12 weeks
            </div>
            <div className="mt-5 flex gap-1">
              {heatmap.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-1">
                  {week.map((cell, di) => (
                    <div
                      key={di}
                      className="h-3.5 w-3.5 rounded-[3px] transition-transform hover:scale-110"
                      style={{
                        background:
                          cell.intensity === 0
                            ? "var(--border-soft)"
                            : `color-mix(in oklab, var(--primary) ${cell.intensity * 28}%, var(--border-soft))`,
                      }}
                      title={`Week ${wi + 1}, day ${di + 1}: intensity ${cell.intensity}`}
                    />
                  ))}
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2 text-[11px] text-muted-foreground">
              <span>Less</span>
              <div className="flex gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-3 w-3 rounded-[3px]"
                    style={{
                      background:
                        i === 0
                          ? "var(--border-soft)"
                          : `color-mix(in oklab, var(--primary) ${i * 28}%, var(--border-soft))`,
                    }}
                  />
                ))}
              </div>
              <span>More</span>
            </div>
          </GlassPanel>

          <div className="space-y-3">
            {INSIGHTS.map((i, idx) => (
              <InsightCard
                key={i.title}
                title={i.title}
                body={i.body}
                className="animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]"
                style={{ animationDelay: `${idx * 80}ms` } as React.CSSProperties}
              />
            ))}
          </div>
        </div>

        {/* Sessions list */}
        <section className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Recent sessions
          </h2>
          <div className="mt-4 overflow-hidden rounded-2xl border border-border bg-surface-elevated shadow-soft">
            {loading ? (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">Loading…</div>
            ) : recentSessions.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                No sessions yet. Your first chat will land here.
              </div>
            ) : (
              <ul className="divide-y divide-border-soft">
                {recentSessions.map((s, idx) => {
                  const emotionKey = s.dominant_emotion as keyof typeof MOOD_META;
                  const meta = MOOD_META[emotionKey] || { emoji: "💭", color: "var(--foreground)" };
                  return (
                    <li
                      key={`${s.date}-${idx}`}
                      className="flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-muted/50"
                    >
                      <span className="text-2xl" aria-hidden>
                        {meta.emoji}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline gap-2">
                          <span className="text-sm font-medium">{s.date}</span>
                          <span className="text-[11px] text-muted-foreground">
                            {s.total_messages} messages
                          </span>
                        </div>
                        <p className="mt-0.5 truncate text-sm text-muted-foreground">
                          Dominant: {s.dominant_emotion}
                        </p>
                      </div>
                      <span className="text-sm font-semibold tabular-nums text-foreground/80">
                        {Math.round(s.average_score)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
