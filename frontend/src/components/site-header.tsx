import { Link, useLocation } from "@tanstack/react-router";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/chat", label: "Chat" },
  { to: "/summary", label: "Summary" },
  { to: "/history", label: "History" },
] as const;

export function SiteHeader() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-40">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Link to="/" className="group flex items-center gap-2.5">
          <span
            className="inline-block h-7 w-7 rounded-full"
            style={{
              background:
                "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--primary) 80%, white 10%), color-mix(in oklab, var(--accent) 60%, var(--primary)))",
              boxShadow: "0 0 18px color-mix(in oklab, var(--primary) 40%, transparent)",
            }}
            aria-hidden
          />
          <span className="text-[15px] font-semibold tracking-tight">Mindful</span>
        </Link>

        <nav className="glass hidden items-center gap-1 rounded-full p-1 md:flex" aria-label="Primary">
          {NAV.map((item) => {
            const active = pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  active
                    ? "bg-primary text-primary-foreground shadow-soft"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="hidden rounded-full px-3.5 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground sm:inline-flex"
          >
            Sign in
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
