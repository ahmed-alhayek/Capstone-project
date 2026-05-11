import { createFileRoute, Link } from "@tanstack/react-router";
import { Loader2, Mail } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { useState } from "react";
import { forgotPassword } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Forgot password — Mindful" },
      { name: "description", content: "Reset your Mindful password." },
    ],
  }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const data = await forgotPassword(email);
      toast.success(data.message || "Check your inbox");
      setSubmitted(true);
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Something went wrong");
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

          {!submitted ? (
            <>
              <h1 className="mt-10 text-3xl font-semibold tracking-tight">Forgot your password?</h1>
              <p className="mt-2 text-sm text-muted-foreground text-pretty">
                Enter your email and we'll send you a link to set a new one.
              </p>

              <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
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

                <button
                  type="submit"
                  disabled={isLoading}
                  className="mt-2 inline-flex h-11 w-full items-center justify-center gap-2 rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground shadow-elevated transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:shadow-floating hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none"
                >
                  {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Send reset link
                </button>
              </form>
            </>
          ) : (
            <div className="mt-10">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Mail className="h-6 w-6" style={{ color: "var(--primary)" }} />
              </div>
              <h1 className="mt-6 text-3xl font-semibold tracking-tight">Check your email</h1>
              <p className="mt-2 text-sm text-muted-foreground text-pretty">
                If an account exists for <strong>{email}</strong>, a reset link is on its way. The
                link expires in 1 hour.
              </p>
              <p className="mt-3 text-xs text-muted-foreground">
                Didn't get it? Check spam, or try again in a minute.
              </p>
            </div>
          )}

          <p className="mt-8 text-center text-sm text-muted-foreground">
            Remembered it?{" "}
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
