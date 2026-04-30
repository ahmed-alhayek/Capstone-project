import * as React from "react";
import { MoodRing } from "./mood-ring";
import { MOOD_META, type ScoreState } from "@/lib/mock";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetDescription } from "@/components/ui/sheet";

export function TelemetryPill({ state }: { state: ScoreState }) {
  const meta = MOOD_META[state.mood];
  const tone = (meta.tone as "primary" | "accent" | "support") ?? "primary";
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          type="button"
          aria-label={`Current mood: ${meta.label}, score ${state.value}. Open details.`}
          className={cn(
            "glass inline-flex items-center gap-2.5 rounded-full pl-1.5 pr-3.5 py-1.5",
            "transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]",
            "hover:shadow-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
        >
          <MoodRing value={state.value} size={32} tone={tone} />
          <span className="text-[13px] font-medium leading-none">{meta.label}</span>
          <span className="text-[11px] text-muted-foreground" aria-hidden>
            {state.trend === "up" ? "↗" : state.trend === "down" ? "↘" : "→"}
          </span>
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>How you're showing up</SheetTitle>
          <SheetDescription>
            A quiet read on this session — not a diagnosis. It updates as we talk.
          </SheetDescription>
        </SheetHeader>
        <div className="mt-8 space-y-6">
          <div className="flex items-center gap-5 rounded-2xl border border-border bg-surface-elevated p-5 shadow-soft">
            <MoodRing value={state.value} size={72} tone={tone} />
            <div>
              <div className="text-2xl font-semibold tracking-tight">{meta.label}</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Wellness score {state.value} · trending {state.trend}
              </div>
            </div>
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Your score is a soft signal we keep in the background. It draws from sentiment,
            pacing, and the words you choose. You can hide it any time in settings.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
