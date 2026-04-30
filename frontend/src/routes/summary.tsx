import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, BookmarkPlus, Share2 } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { MoodRing } from "@/components/mindful/mood-ring";
import { GlassPanel } from "@/components/mindful/glass-panel";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { moodTimeline, MOOD_META } from "@/lib/mock";

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
  const trend = moodTimeline().slice(-7);
  const start = 52;
  const end = 71;
  const delta = end - start;

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 pb-16 sm:px-6">
        <div className="animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Session · just now · 18 min
          </span>
          <h1 className="mt-3 text-balance text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            You worked through a lot today.
          </h1>
          <p className="mt-3 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground">
            You started carrying something heavy and found a softer way to hold it. That's not a
            small thing — it's the work.
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <GlassPanel className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]" style={{ animationDelay: "100ms" }}>
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Mood shift</div>
            <div className="mt-4 flex items-center gap-4">
              <MoodRing value={start} size={48} tone="support" />
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              <MoodRing value={end} size={56} tone="primary" />
            </div>
            <div className="mt-4 text-sm">
              <span className="font-semibold" style={{ color: "var(--primary)" }}>
                +{delta} points
              </span>
              <span className="text-muted-foreground"> · heavy → hopeful</span>
            </div>
          </GlassPanel>

          <GlassPanel className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]" style={{ animationDelay: "180ms" }}>
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Topics held</div>
            <ul className="mt-4 flex flex-wrap gap-1.5">
              {["work stress", "self-talk", "boundaries"].map((t) => (
                <li key={t} className="rounded-full bg-accent-soft px-3 py-1 text-[12px] font-medium" style={{ color: "var(--accent)" }}>
                  {t}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              You named the shape of it. Naming is half the work.
            </p>
          </GlassPanel>

          <GlassPanel className="p-5 animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]" style={{ animationDelay: "260ms" }}>
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Last 7 days</div>
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
              <span className="font-semibold text-foreground">Trending up</span> across the week.
            </p>
          </GlassPanel>
        </div>

        <div className="mt-10 rounded-3xl border border-border bg-surface-elevated p-6 shadow-soft">
          <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">A small reflection</div>
          <p className="mt-3 text-pretty text-base leading-relaxed">
            Tonight, before bed, try this: write down one sentence the most compassionate version
            of you might say. Not advice. Not a fix. Just a sentence.
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
      </main>
    </div>
  );
}

// (intentionally re-using mood meta for accessibility lookups)
void MOOD_META;
