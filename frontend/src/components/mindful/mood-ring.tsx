import { cn } from "@/lib/utils";

type Tone = "primary" | "accent" | "support";

export function MoodRing({
  value,
  size = 44,
  tone = "primary",
  className,
}: {
  value: number; // 0-100
  size?: number;
  tone?: Tone;
  className?: string;
}) {
  const stroke = 4;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const offset = c - (pct / 100) * c;
  const colorVar =
    tone === "support" ? "var(--support)" : tone === "accent" ? "var(--accent)" : "var(--primary)";

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="var(--border)"
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={colorVar}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 800ms cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-semibold tabular-nums">
        {pct}
      </span>
    </div>
  );
}
