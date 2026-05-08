import { Link, useNavigate } from "@tanstack/react-router";
import { Sparkles, AlertTriangle, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  return (
    <header
      className="sticky top-0 z-30 border-b border-border"
      style={{ background: "rgba(10,10,10,0.8)", backdropFilter: "blur(20px)" }}
    >
      <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-3">
        <Link to="/dashboard" className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Job Scout</span>
        </Link>

        <div className="flex items-center gap-4">
          {user && !user.has_resume && (
            <Link
              to="/profile"
              className="hidden items-center gap-1.5 rounded-full border border-warning/40 bg-warning/10 px-3 py-1 text-[11px] font-medium text-warning sm:inline-flex"
              style={{ color: "#f59e0b" }}
            >
              <AlertTriangle className="h-3 w-3" />
              Upload resume to enable scoring
            </Link>
          )}
          {user && (
            <span className="hidden text-[13px] text-muted-foreground sm:inline">
              {user.email}
            </span>
          )}
          <Link
            to="/profile"
            className="text-[13px] text-muted-foreground hover:text-foreground"
            activeProps={{ className: "text-[13px] font-medium text-foreground" }}
          >
            Profile
          </Link>
          <Link
            to="/pipeline"
            className="text-[13px] text-muted-foreground hover:text-foreground transition-colors"
            activeProps={{ className: "text-[13px] font-medium text-foreground" }}
          >
            Pipeline
          </Link>
          <button
            onClick={() => {
              logout();
              navigate({ to: "/login" });
            }}
            className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-[12px] text-muted-foreground transition hover:border-primary hover:text-foreground"
          >
            <LogOut className="h-3 w-3" />
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}