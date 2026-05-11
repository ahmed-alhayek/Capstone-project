import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Loader2, CheckCircle2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { useState } from "react";
import { resetPassword } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/reset-password")({
  validateSearch: (search: Record<string, unknown>): { token?: string } => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Reset password — Mindful" },
      { name: "description", content: "Set a new password for your Mindful account." },
    ],
  }),
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      toast.error("Missing reset token. Use the link from your email.");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    if (password !== confirm) {
      toast.error("Passwords don't match");
      return;
    }

    setIsLoading(true);
    try {
      const data = await resetPassword(token, password);
      toast.success(data.message || "Password updated");
      setDone(true);
      setTimeout(() => navigate({ to: "/login" }), 2000);
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Could not reset password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute right-4 top-4 sm:right-6 sm:top-6">
        <ThemeToggle />
      </div>
      <div className="flex min-h-screen items-center justify-center px-4 py-16 sm:px-8">
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

          {!done ? (
            <>
              <h1 className="mt-10 text-3xl font-semibold tracking-tight">Set a new password</h1>
              <p className="mt-2 text-sm text-muted-foreground text-pretty">
                Pick something you'll remember. At least 6 characters.
              </p>

              {!token && (
                <div className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                  This page needs a valid reset link. Please open the link from your email.
                </div>
              )}

              <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-1.5">
                  <Label htmlFor="password">New password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="confirm">Confirm password</Label>
                  <Input
                    id="confirm"
                    name="confirm"
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !token}
                  className="mt-2 inline-flex h-11 w-full items-center justify-center gap-2 rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground shadow-elevated transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-floating hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none"
                >
                  {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Update password
                </button>
              </form>
            </>
          ) : (
            <div className="mt-10">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <CheckCircle2 className="h-6 w-6" style={{ color: "var(--primary)" }} />
              </div>
              <h1 className="mt-6 text-3xl font-semibold tracking-tight">Password updated</h1>
              <p className="mt-2 text-sm text-muted-foreground text-pretty">
                You're all set. Redirecting you to sign in...
              </p>
            </div>
          )}

          <p className="mt-8 text-center text-sm text-muted-foreground">
            <Link
              to="/login"
              className="font-medium text-foreground underline-offset-4 hover:underline"
            >
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
