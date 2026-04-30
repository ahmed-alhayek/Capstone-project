import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Lock, ShieldCheck, Sparkles, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { useState } from "react";
import { loginUser, registerUser } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — Mindful" },
      { name: "description", content: "Welcome back. Sign in to continue your sessions." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  return <AuthLayout mode="login" />;
}

export function AuthLayout({ mode }: { mode: "login" | "register" }) {
  const isLogin = mode === "login";
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (isLogin) {
        const data = await loginUser(email, password);
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username);
        toast.success(data.message || "Signed in successfully");
        navigate({ to: "/chat" });
      } else {
        const data = await registerUser(name || email.split("@")[0], email, password);
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username);
        toast.success(data.message || "Account created successfully");
        navigate({ to: "/chat" });
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute right-4 top-4 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>
      <div className="mx-auto grid min-h-screen max-w-6xl grid-cols-1 gap-0 lg:grid-cols-2">
        {/* Form column */}
        <div className="flex items-center justify-center px-4 py-16 sm:px-8">
          <div className="w-full max-w-sm animate-[rise-in_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
            <Link to="/" className="inline-flex items-center gap-2.5">
              <span
                className="inline-block h-7 w-7 rounded-full"
                style={{
                  background:
                    "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--primary) 80%, white 10%), color-mix(in oklab, var(--accent) 60%, var(--primary)))",
                }}
                aria-hidden
              />
              <span className="text-[15px] font-semibold tracking-tight">Mindful</span>
            </Link>

            <h1 className="mt-10 text-3xl font-semibold tracking-tight">
              {isLogin ? "Welcome back." : "Make space for yourself."}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground text-pretty">
              {isLogin
                ? "We're glad you're here. Pick up where you left off."
                : "Create your account. It takes a moment, and it's entirely yours."}
            </p>

            <form
              className="mt-8 space-y-4"
              onSubmit={handleSubmit}
            >
              {!isLogin && (
                <div className="space-y-1.5">
                  <Label htmlFor="name">Name</Label>
                  <Input 
                    id="name" 
                    name="name" 
                    value={name} 
                    onChange={(e) => setName(e.target.value)} 
                    placeholder="What should we call you?" 
                    autoComplete="name" 
                  />
                </div>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 inline-flex h-11 w-full items-center justify-center gap-2 rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground shadow-elevated transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-floating hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none"
              >
                {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                {isLogin ? "Sign in" : "Create account"}
              </button>

              <div className="relative my-2 flex items-center text-[11px] uppercase tracking-wider text-muted-foreground">
                <span className="flex-1 border-t border-border" />
                <span className="px-3">or</span>
                <span className="flex-1 border-t border-border" />
              </div>

              <button
                type="button"
                onClick={() => (window.location.href = "/chat")}
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full border border-border bg-surface-elevated text-sm font-medium transition-all hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Continue with Apple
              </button>
              <button
                type="button"
                onClick={() => (window.location.href = "/chat")}
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full border border-border bg-surface-elevated text-sm font-medium transition-all hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Continue with Google
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-muted-foreground">
              {isLogin ? "New here? " : "Already have an account? "}
              <Link
                to={isLogin ? "/register" : "/login"}
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                {isLogin ? "Create an account" : "Sign in"}
              </Link>
            </p>
          </div>
        </div>

        {/* Trust column */}
        <div className="relative hidden items-center justify-center overflow-hidden p-12 lg:flex">
          <div
            aria-hidden
            className="absolute inset-0 -z-10"
            style={{
              background:
                "radial-gradient(60% 60% at 50% 40%, color-mix(in oklab, var(--primary) 18%, transparent), transparent 70%), radial-gradient(40% 40% at 80% 80%, color-mix(in oklab, var(--accent) 16%, transparent), transparent 70%)",
            }}
          />
          <div className="max-w-sm space-y-8 animate-[rise-in_0.6s_cubic-bezier(0.22,1,0.36,1)_both]">
            <div
              className="h-32 w-32 rounded-full"
              style={{
                background:
                  "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--primary) 80%, white 10%), color-mix(in oklab, var(--accent) 60%, var(--primary)))",
                boxShadow: "0 0 80px color-mix(in oklab, var(--primary) 40%, transparent)",
                animation: "breathe 5s cubic-bezier(0.22,1,0.36,1) infinite",
              }}
            />
            <h2 className="text-2xl font-semibold tracking-tight text-balance">
              A space that's yours, and only yours.
            </h2>
            <ul className="space-y-5">
              {[
                { icon: Lock, title: "End-to-end private", body: "Encrypted before it leaves your device." },
                { icon: ShieldCheck, title: "Never sold", body: "No ads. No trackers. No data brokers." },
                { icon: Sparkles, title: "You own your data", body: "Export or delete everything, any time." },
              ].map(({ icon: Icon, title, body }) => (
                <li key={title} className="flex items-start gap-3">
                  <Icon className="mt-0.5 h-5 w-5 shrink-0" style={{ color: "var(--primary)" }} />
                  <div>
                    <div className="text-sm font-medium">{title}</div>
                    <div className="text-sm text-muted-foreground">{body}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
