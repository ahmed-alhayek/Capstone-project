import * as React from "react";
import { cn } from "@/lib/utils";

export const GlassPanel = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { elevated?: boolean }
>(({ className, elevated, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "glass rounded-2xl",
      elevated ? "shadow-elevated" : "shadow-soft",
      className,
    )}
    {...props}
  />
));
GlassPanel.displayName = "GlassPanel";
