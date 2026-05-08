import { createFileRoute } from "@tanstack/react-router";
import { AuthBackground } from "@/components/AuthBackground";
import { AuthCard } from "@/components/AuthCard";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Sign in — Job Scout" }] }),
  component: LoginPage,
});

function LoginPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-4">
      <AuthBackground />
      <AuthCard mode="login" />
    </div>
  );
}