import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function InsightCard({
  title,
  body,
  className,
  style,
}: {
  title: string;
  body: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border bg-surface-elevated p-5 shadow-soft",
        "transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-elevated",
        className,
      )}
      style={style}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent-foreground">
          <Sparkles className="h-4 w-4" style={{ color: "var(--accent)" }} />
        </div>
        <div>
          <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
          <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground text-pretty">{body}</p>
        </div>
      </div>
    </div>
  );
}
