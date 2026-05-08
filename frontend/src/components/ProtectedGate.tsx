import { useEffect, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/store/authStore";

export function ProtectedGate({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { token, hydrated } = useAuthStore();

  useEffect(() => {
    if (hydrated && !token) {
      navigate({ to: "/login" });
    }
  }, [hydrated, token, navigate]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }
  if (!token) return null;
  return <>{children}</>;
}