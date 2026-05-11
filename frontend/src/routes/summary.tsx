import * as React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, BookmarkPlus, Share2 } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { MoodRing } from "@/components/mindful/mood-ring";
import { GlassPanel } from "@/components/mindful/glass-panel";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { MOOD_META } from "@/lib/mock";
import { getHistory, type HistoryEntry } from "@/lib/api";

export const Route = createFileRoute("/summary")({
  head: () => ({
    meta: [
      { title: "Session summary — Mindful" },
      { name: "description", content: "A gentle recap of where you started and where you landed." },
    ],
  }),
  component: SummaryPage,
});

function SummaryPage() {
  const [history, setHistory] = React.useState<HistoryEntry[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    getHistory()
      .then((data) => setHistory(data.history || []))
      .catch((err) => console.error("Failed to fetch history", err))
      .finally(() => setLoading(false));
  }, []);

  const last7 = React.useMemo(() => history.slice(-7), [history]);
  const trend = React.useMemo(() => last7.map((h) => ({ score: h.average_score })), [last7]);

  const start = last7.length > 0 ? Math.round(last7[0].average_score) : 0;
  const end = last7.length > 0 ? Math.round(last7[last7.length - 1].average_score) : 0;
  const delta = end - start;

  const topics = React.useMemo(() => {
    const counts = new Map<string, number>();
    last7.forEach((h) => {
      counts.set(h.dominant_emotion, (counts.get(h.dominant_emotion) || 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([emotion]) => emotion);
  }, [last7]);

  const hasData = last7.length > 0;
  const periodLabel = hasData
    ? `Last ${last7.length} day${last7.length === 1 ? "" : "s"}`
    : "No sessions yet";

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 pb-16 sm:px-6">
        <div className="animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            {periodLabel}
          </span>
          <h1 className="mt-3 text-balance text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            {hasData ? "Here's how this week unfolded." : "Your story starts here."}
          </h1>
          <p className="mt-3 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground">
            {hasData
              ? "A gentle look at where you've been and where you're heading. The arc is yours."
              : "Once you've had a few conversations, your patterns will start to appear here."}
          </p>
        </div>

        {loading ? (
          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <GlassPanel key={i} className="p-5">
                <div className="h-3 w-24 animate-pulse rounded bg-muted" />
                <div className="mt-6 h-8 w-32 animate-pulse rounded bg-muted" />
                <div className="mt-4 h-3 w-40 animate-pulse rounded bg-muted" />
              </GlassPanel>
            ))}
          </div>
        ) : hasData ? (
          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            <GlassPanel
              className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]"
              style={{ animationDelay: "100ms" }}
            >
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Mood shift
              </div>
              <div className="mt-4 flex items-center gap-4">
                <MoodRing value={start} size={48} tone="support" />
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <MoodRing value={end} size={56} tone="primary" />
              </div>
              <div className="mt-4 text-sm">
                <span
                  className="font-semibold"
                  style={{ color: delta >= 0 ? "var(--primary)" : "var(--support)" }}
                >
                  {delta >= 0 ? "+" : ""}
                  {delta} points
                </span>
                <span className="text-muted-foreground">
                  {" "}
                  · across {last7.length} day{last7.length === 1 ? "" : "s"}
                </span>
              </div>
            </GlassPanel>

            <GlassPanel
              className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]"
              style={{ animationDelay: "180ms" }}
            >
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Most felt
              </div>
              <ul className="mt-4 flex flex-wrap gap-1.5">
                {topics.length > 0 ? (
                  topics.map((t) => {
                    const meta = MOOD_META[t as keyof typeof MOOD_META] || {
                      emoji: "💭",
                      color: "var(--accent)",
                    };
                    return (
                      <li
                        key={t}
                        className="inline-flex items-center gap-1 rounded-full bg-accent-soft px-3 py-1 text-[12px] font-medium"
                        style={{ color: "var(--accent)" }}
                      >
                        <span aria-hidden>{meta.emoji}</span>
                        {t}
                      </li>
                    );
                  })
                ) : (
                  <li className="text-sm text-muted-foreground">Still settling in.</li>
                )}
              </ul>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                You named the shape of it. Naming is half the work.
              </p>
            </GlassPanel>

            <GlassPanel
              className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]"
              style={{ animationDelay: "260ms" }}
            >
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {last7.length}-day trend
              </div>
              <div className="mt-3 h-16">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend}>
                    <YAxis hide domain={[20, 100]} />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="var(--primary)"
                      strokeWidth={2.5}
                      dot={false}
                      animationDuration={800}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">
                  {delta > 0 ? "Trending up" : delta < 0 ? "Trending softer" : "Holding steady"}
                </span>{" "}
                {delta !== 0 ? "across the window." : "for now."}
              </p>
            </GlassPanel>
          </div>
        ) : (
          <GlassPanel className="mt-10 p-8 text-center">
            <p className="text-sm text-muted-foreground">
              No data to summarize yet. Head to chat and have a conversation — your patterns will
              start showing up here.
            </p>
            <Link
              to="/chat"
              className="mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-elevated transition-all hover:shadow-floating hover:-translate-y-0.5"
            >
              Begin a session
              <ArrowRight className="h-4 w-4" />
            </Link>
          </GlassPanel>
        )}

        {hasData && (
          <>
            <div className="mt-10 rounded-3xl border border-border bg-surface-elevated p-6 shadow-soft">
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                A small reflection
              </div>
              <p className="mt-3 text-pretty text-base leading-relaxed">
                Tonight, before bed, try this: write down one sentence the most compassionate
                version of you might say. Not advice. Not a fix. Just a sentence.
              </p>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                <button className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-elevated transition-all hover:shadow-floating hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
                  <BookmarkPlus className="h-4 w-4" /> Save to journal
                </button>
                <button className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-5 py-2.5 text-sm font-medium transition-all hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                  <Share2 className="h-4 w-4" /> Share with therapist
                </button>
              </div>
              <Link
                to="/history"
                className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
              >
                View full history →
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
