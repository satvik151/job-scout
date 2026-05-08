import { useState, type FormEvent } from "react";
import { Sparkles, Eye, EyeOff, Loader2 } from "lucide-react";
import { Link, useNavigate } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";

type Mode = "login" | "register";

export function AuthCard({ mode }: { mode: Mode }) {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function doLogin(em: string, pw: string) {
    const { access_token } = await api.login(em, pw);
    // store token first so /auth/me sees it
    setAuth(access_token, { id: 0, email: em, has_resume: false });
    const me = await api.me();
    setAuth(access_token, me);
    toast.success("Signed in");
    navigate({ to: "/dashboard" });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register" && password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      if (mode === "register") {
        await api.register(email, password);
        toast.success("Account created");
      }
      await doLogin(email, password);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card relative z-10 w-[420px] max-w-[90vw] p-10 fade-up">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="h-5 w-5 text-primary" />
        <h1 className="text-[24px] font-semibold tracking-tight">Job Scout</h1>
      </div>
      <p className="text-[13px] text-muted-foreground mb-8">
        AI-powered job intelligence
      </p>

      {/* Tabs */}
      <div className="relative mb-6 flex gap-6 border-b border-border/60">
        <TabLink to="/login" active={mode === "login"}>Login</TabLink>
        <TabLink to="/register" active={mode === "register"}>Register</TabLink>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          required
          autoComplete="email"
        />
        <PasswordField
          label="Password"
          value={password}
          onChange={setPassword}
          show={showPw}
          toggle={() => setShowPw((v) => !v)}
          autoComplete={mode === "login" ? "current-password" : "new-password"}
        />
        {mode === "register" && (
          <Field
            label="Confirm password"
            type={showPw ? "text" : "password"}
            value={confirm}
            onChange={setConfirm}
            required
            autoComplete="new-password"
          />
        )}

        {error && (
          <p className="text-[12px] text-destructive">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="flex h-10 w-full items-center justify-center rounded-md bg-primary text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : mode === "login" ? (
            "Sign in"
          ) : (
            "Create account"
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-[12px] text-muted-foreground">
        {mode === "login" ? (
          <>
            Don't have an account?{" "}
            <Link to="/register" className="text-foreground hover:text-primary">
              Register
            </Link>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <Link to="/login" className="text-foreground hover:text-primary">
              Login
            </Link>
          </>
        )}
      </p>
    </div>
  );
}

function TabLink({
  to,
  active,
  children,
}: {
  to: "/login" | "/register";
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className={`relative pb-3 text-sm transition ${
        active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
      {active && (
        <span className="absolute bottom-[-1px] left-0 right-0 h-[2px] rounded-full bg-primary" />
      )}
    </Link>
  );
}

function Field({
  label,
  type,
  value,
  onChange,
  ...rest
}: {
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] text-muted-foreground">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full rounded-md border border-border bg-background/40 px-3 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none transition focus:border-primary"
        {...rest}
      />
    </label>
  );
}

function PasswordField({
  label,
  value,
  onChange,
  show,
  toggle,
  autoComplete,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  show: boolean;
  toggle: () => void;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] text-muted-foreground">
        {label}
      </span>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required
          autoComplete={autoComplete}
          className="h-10 w-full rounded-md border border-border bg-background/40 px-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none transition focus:border-primary"
        />
        <button
          type="button"
          onClick={toggle}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
          tabIndex={-1}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
    </label>
  );
}