import { cn } from "@/lib/utils";

export type OrbState = "idle" | "recording" | "processing";

export function BreathingOrb({ state, className }: { state: OrbState; className?: string }) {
  return (
    <div
      className={cn("relative flex items-center justify-center", className)}
      role="status"
      aria-live="polite"
      aria-label={
        state === "recording" ? "Listening" : state === "processing" ? "Thinking" : "Ready when you are"
      }
    >
      {/* Ripples for recording state */}
      {state === "recording" && (
        <>
          <span
            className="absolute h-56 w-56 rounded-full"
            style={{
              background: "radial-gradient(circle, color-mix(in oklab, var(--primary) 30%, transparent), transparent 70%)",
              animation: "ripple 2.4s cubic-bezier(0.22,1,0.36,1) infinite",
            }}
          />
          <span
            className="absolute h-56 w-56 rounded-full"
            style={{
              background: "radial-gradient(circle, color-mix(in oklab, var(--primary) 30%, transparent), transparent 70%)",
              animation: "ripple 2.4s cubic-bezier(0.22,1,0.36,1) infinite",
              animationDelay: "1.2s",
            }}
          />
        </>
      )}

      <div
        className={cn(
          "relative h-56 w-56 rounded-full transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]",
          state === "processing" && "animate-spin",
        )}
        style={{
          background:
            state === "processing"
              ? "conic-gradient(from 0deg, color-mix(in oklab, var(--primary) 60%, transparent), color-mix(in oklab, var(--accent) 50%, transparent), color-mix(in oklab, var(--primary) 60%, transparent))"
              : "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--primary) 80%, white 10%), color-mix(in oklab, var(--accent) 60%, var(--primary)))",
          boxShadow: "0 0 80px color-mix(in oklab, var(--primary) 30%, transparent), inset 0 0 40px color-mix(in oklab, white 20%, transparent)",
          animation:
            state === "processing"
              ? "spin 3s linear infinite"
              : "breathe 5s cubic-bezier(0.22,1,0.36,1) infinite",
        }}
      />
      <div
        className={cn(
          "absolute h-32 w-32 rounded-full bg-surface-elevated/40",
          "backdrop-blur-md",
        )}
      />
    </div>
  );
}
