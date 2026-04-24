import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/site-header";
import { InsightCard } from "@/components/mindful/insight-card";
import { GlassPanel } from "@/components/mindful/glass-panel";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { heatmapData, INSIGHTS, moodTimeline, MOOD_META } from "@/lib/mock";
import { getHistory } from "@/lib/api";
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
  const [sessions, setSessions] = React.useState<any[]>([]);

  React.useEffect(() => {
    getHistory().then((data) => {
      setSessions(data.history || []);
    }).catch((err) => console.error("Failed to fetch history", err));
  }, []);

  const data = React.useMemo(() => {
    const r = RANGES.find((x) => x.id === range)!;
    const all = moodTimeline();
    return all.slice(-Math.min(r.days, all.length));
  }, [range]);

  const heatmap = React.useMemo(() => heatmapData(), []);
  const avg = Math.round(data.reduce((a, b) => a + b.score, 0) / data.length);

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
        <GlassPanel elevated className="mt-8 p-5 sm:p-6 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
          <div className="flex items-baseline justify-between">
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Wellness trend
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {avg}
                <span className="ml-2 text-sm font-normal text-muted-foreground">average</span>
              </div>
            </div>
          </div>
          <div className="mt-4 h-56 sm:h-64">
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
                      title={`Week ${wi + 1}, day ${di + 1}: ${cell.intensity} sessions`}
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
            <ul className="divide-y divide-border-soft">
              {sessions.map((s: any, idx) => {
                const emotionKey = s.dominant_emotion as keyof typeof MOOD_META;
                const meta = MOOD_META[emotionKey] || { emoji: "💭", color: "var(--foreground)" };
                return (
                  <li
                    key={idx}
                    className="flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-muted/50"
                  >
                    <span className="text-2xl" aria-hidden>{meta.emoji}</span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm font-medium">
                          {s.date}
                        </span>
                        <span className="text-[11px] text-muted-foreground">{s.total_messages} messages</span>
                      </div>
                      <p className="mt-0.5 truncate text-sm text-muted-foreground">Session summary</p>
                    </div>
                    <span className="text-sm font-semibold tabular-nums text-foreground/80">{Math.round(s.average_score)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}
