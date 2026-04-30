import { createFileRoute } from "@tanstack/react-router";
import { AuthLayout } from "./login";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Create your account — Mindful" },
      { name: "description", content: "Create your private Mindful account in moments." },
    ],
  }),
  component: () => <AuthLayout mode="register" />,
});
