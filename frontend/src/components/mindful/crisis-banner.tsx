import { Link } from "@tanstack/react-router";
import { Heart, Phone, Wind } from "lucide-react";

export function CrisisBanner({ onDismiss }: { onDismiss?: () => void }) {
  return (
    <div
      role="region"
      aria-label="Support resources"
      className="rounded-2xl border p-5 shadow-soft animate-[rise-in_0.42s_cubic-bezier(0.22,1,0.36,1)_both]"
      style={{
        backgroundColor: "var(--support-soft)",
        borderColor: "color-mix(in oklab, var(--support) 30%, transparent)",
      }}
    >
      <div className="flex items-start gap-3">
        <Heart className="mt-0.5 h-5 w-5 shrink-0" style={{ color: "var(--support)" }} aria-hidden />
        <div className="flex-1">
          <p className="text-sm font-semibold text-foreground">
            We noticed things feel heavy. You don't have to be alone with this.
          </p>
          <p className="mt-1 text-sm text-muted-foreground text-pretty">
            Take what you need. There's no right next step — only the one that feels possible.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <a
              href="tel:988"
              className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-support-foreground shadow-soft transition-all hover:shadow-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              style={{ backgroundColor: "var(--support)" }}
            >
              <Phone className="h-3.5 w-3.5" /> Talk to a human (988)
            </a>
            <Link
              to="/crisis"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-4 py-2 text-sm font-medium transition-all hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Wind className="h-3.5 w-3.5" /> Grounding exercise
            </Link>
            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="rounded-full px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Not now
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
