import * as React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Phone, Wind, MessageCircle, Heart } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { GlassPanel } from "@/components/mindful/glass-panel";

export const Route = createFileRoute("/crisis")({
  head: () => ({
    meta: [
      { title: "Support — Mindful" },
      { name: "description", content: "You don't have to be alone with this. Gentle next steps." },
    ],
  }),
  component: CrisisPage,
});

function CrisisPage() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 pb-16 sm:px-6">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[480px] opacity-60"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, color-mix(in oklab, var(--support) 22%, transparent), transparent 70%)",
          }}
        />

        <div className="animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
          <Heart className="h-7 w-7" style={{ color: "var(--support)" }} aria-hidden />
          <h1 className="mt-5 text-balance text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            We noticed things feel heavy.
            <br />
            You don't have to be alone with this.
          </h1>
          <p className="mt-4 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground">
            Take what you need from this page. There's no right next step — only the one that
            feels possible right now.
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <ActionCard
            icon={Phone}
            title="Talk to a human"
            body="988 Suicide & Crisis Lifeline · 24/7, free, confidential."
            cta="Call 988"
            href="tel:988"
            primary
          />
          <ActionCard
            icon={Wind}
            title="Grounding exercise"
            body="A 60-second breath. Slow, no goal but to be here."
            cta="Begin"
            href="#breathe"
          />
          <ActionCard
            icon={MessageCircle}
            title="Keep talking"
            body="We can slow the pace. No pressure, no fixing — just being met."
            cta="Return to chat"
            href="/chat"
          />
        </div>

        <Breath />

        <GlassPanel className="mt-8 p-5">
          <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Other lines, if you prefer
          </div>
          <ul className="mt-4 grid gap-2 sm:grid-cols-2">
            {[
              { name: "Samaritans (UK & ROI)", num: "116 123" },
              { name: "Lifeline (Australia)", num: "13 11 14" },
              { name: "Crisis Text Line (US)", num: "Text HOME to 741741" },
              { name: "Trans Lifeline", num: "877-565-8860" },
            ].map((r) => (
              <li key={r.name} className="flex items-center justify-between rounded-xl px-3 py-2.5 text-sm">
                <span className="text-muted-foreground">{r.name}</span>
                <span className="font-medium tabular-nums">{r.num}</span>
              </li>
            ))}
          </ul>
        </GlassPanel>

        <p className="mt-10 text-center text-xs text-muted-foreground">
          If you are in immediate danger, please call your local emergency number.
        </p>
      </main>
    </div>
  );
}

function ActionCard({
  icon: Icon,
  title,
  body,
  cta,
  href,
  primary,
}: {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  body: string;
  cta: string;
  href: string;
  primary?: boolean;
}) {
  const isExternal = href.startsWith("tel:") || href.startsWith("http") || href.startsWith("#");
  const Inner = (
    <>
      <Icon className="h-5 w-5" style={{ color: primary ? "var(--support)" : "var(--primary)" }} />
      <h2 className="mt-4 text-base font-semibold tracking-tight">{title}</h2>
      <p className="mt-1.5 flex-1 text-sm leading-relaxed text-muted-foreground text-pretty">{body}</p>
      <span
        className="mt-5 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium shadow-soft transition-all"
        style={{
          backgroundColor: primary ? "var(--support)" : "var(--surface-elevated)",
          color: primary ? "var(--support-foreground)" : "var(--foreground)",
          border: primary ? "none" : "1px solid var(--border)",
        }}
      >
        {cta}
      </span>
    </>
  );
  const className =
    "flex flex-col rounded-2xl border border-border bg-surface-elevated p-5 shadow-soft transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-elevated hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";
  return isExternal ? (
    <a href={href} className={className}>{Inner}</a>
  ) : (
    <Link to={href} className={className}>{Inner}</Link>
  );
}

function Breath() {
  const [running, setRunning] = React.useState(false);
  return (
    <section
      id="breathe"
      className="mt-10 rounded-3xl border border-border bg-surface-elevated p-8 text-center shadow-soft"
    >
      <h2 className="text-lg font-semibold tracking-tight">A 60-second breath</h2>
      <p className="mt-2 text-sm text-muted-foreground">In for 4. Hold for 4. Out for 6. Repeat.</p>
      <div className="mx-auto mt-8 flex h-48 w-48 items-center justify-center">
        <div
          className="h-32 w-32 rounded-full"
          style={{
            background:
              "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--primary) 80%, white 10%), color-mix(in oklab, var(--accent) 60%, var(--primary)))",
            animation: running ? "breathe 8s cubic-bezier(0.22,1,0.36,1) infinite" : undefined,
            boxShadow: "0 0 60px color-mix(in oklab, var(--primary) 35%, transparent)",
          }}
        />
      </div>
      <button
        type="button"
        onClick={() => setRunning((r) => !r)}
        className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-soft transition-all hover:shadow-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        {running ? "Pause" : "Begin"}
      </button>
    </section>
  );
}
