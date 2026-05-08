import { createFileRoute } from "@tanstack/react-router";
import { AuthBackground } from "@/components/AuthBackground";
import { AuthCard } from "@/components/AuthCard";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Create account — Job Scout" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-4">
      <AuthBackground />
      <AuthCard mode="register" />
    </div>
  );
}