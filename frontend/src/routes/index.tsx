import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/store/authStore";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const navigate = useNavigate();
  const { token, hydrated } = useAuthStore();
  useEffect(() => {
    if (!hydrated) return;
    navigate({ to: token ? "/dashboard" : "/login", replace: true });
  }, [hydrated, token, navigate]);
  return (
    <div className="flex min-h-screen items-center justify-center text-muted-foreground text-sm">
      Loading…
    </div>
  );
}
