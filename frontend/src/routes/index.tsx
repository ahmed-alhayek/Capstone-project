import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Lock, ShieldCheck, Sparkles } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { GlassPanel } from "@/components/mindful/glass-panel";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Mindful — A calmer place to be heard" },
      {
        name: "description",
        content:
          "A private, emotionally intelligent companion for everyday mental wellness. End-to-end private. Yours alone.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />

      <main className="relative mx-auto max-w-6xl px-4 sm:px-6">
        {/* Ambient backdrop */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[640px] opacity-70"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, color-mix(in oklab, var(--primary) 18%, transparent), transparent 70%), radial-gradient(40% 40% at 80% 10%, color-mix(in oklab, var(--accent) 18%, transparent), transparent 70%)",
          }}
        />

        <section className="pt-16 pb-20 sm:pt-24 sm:pb-28">
          <div className="mx-auto max-w-3xl text-center animate-[rise-in_0.6s_cubic-bezier(0.22,1,0.36,1)_both]">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-3 py-1 text-[12px] font-medium text-muted-foreground shadow-soft">
              <Sparkles className="h-3.5 w-3.5" style={{ color: "var(--primary)" }} />
              Quietly with you, every day
            </span>

            <h1 className="mt-6 text-balance text-4xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
              A calmer place
              <br />
              <span style={{ color: "var(--primary)" }}>to be heard.</span>
            </h1>

            <p className="mx-auto mt-6 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
              Mindful is an emotionally intelligent companion for the in-between moments —
              when you need to think out loud, soften, or just be met where you are.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/chat"
                className="group inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-elevated transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-floating hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                Begin a session
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
              </Link>
              <Link
                to="/register"
                className="rounded-full border border-border bg-surface-elevated px-6 py-3 text-sm font-medium transition-all hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Create an account
              </Link>
            </div>
          </div>

          {/* Privacy pillars */}
          <div className="mx-auto mt-20 grid max-w-4xl gap-4 sm:grid-cols-3">
            {[
              { icon: Lock, title: "End-to-end private", body: "Your sessions are encrypted before they leave your device." },
              { icon: ShieldCheck, title: "Never sold", body: "No ads, no third-party trackers, no data brokers. Ever." },
              { icon: Sparkles, title: "You own your data", body: "Export or delete everything in one tap, any time." },
            ].map(({ icon: Icon, title, body }, i) => (
              <GlassPanel
                key={title}
                className="p-5 animate-[rise-in_0.6s_cubic-bezier(0.22,1,0.36,1)_both]"
                style={{ animationDelay: `${120 + i * 80}ms` }}
              >
                <Icon className="h-5 w-5" style={{ color: "var(--primary)" }} />
                <h3 className="mt-3 text-sm font-semibold tracking-tight">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{body}</p>
              </GlassPanel>
            ))}
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-center text-xs text-muted-foreground sm:px-6">
        Mindful is a wellness companion, not a substitute for professional care. In a crisis, please call{" "}
        <a href="tel:988" className="underline underline-offset-4 hover:text-foreground">988</a>.
      </footer>
    </div>
  );
}
