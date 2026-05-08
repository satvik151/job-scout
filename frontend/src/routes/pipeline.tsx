import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Calendar, Play, Loader2 } from "lucide-react";
import { ProtectedGate } from "@/components/ProtectedGate";
import { Navbar } from "@/components/Navbar";
import { api, type PipelineStatus } from "@/lib/api";

export const Route = createFileRoute("/pipeline")({
  head: () => ({ meta: [{ title: "Pipeline — Job Scout" }] }),
  component: () => (
    <ProtectedGate>
      <PipelinePage />
    </ProtectedGate>
  ),
});

const MOCK: PipelineStatus = {
  status: "success",
  jobs_scraped: 24,
  new_jobs: 7,
  emails_sent: 1,
  duration_seconds: 18,
  timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
};

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  if (isNaN(t)) return "";
  const diff = Math.max(0, Date.now() - t);
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Ran just now";
  if (m < 60) return `Ran ${m} minute${m === 1 ? "" : "s"} ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `Ran ${h} hour${h === 1 ? "" : "s"} ago`;
  const d = Math.floor(h / 24);
  return `Ran ${d} day${d === 1 ? "" : "s"} ago`;
}

function PipelinePage() {
  const status = useQuery({
    queryKey: ["pipeline-status"],
    queryFn: () => api.pipelineStatus(),
    retry: false,
  });

  const [runState, setRunState] = useState<"idle" | "running" | "success" | "error">("idle");
  const [runError, setRunError] = useState<string | null>(null);

  const runPipeline = useMutation({
    mutationFn: () => api.runPipeline(),
    onMutate: () => {
      setRunState("running");
      setRunError(null);
    },
    onSuccess: () => {
      setRunState("success");
      setTimeout(() => setRunState("idle"), 5000);
    },
    onError: (err: Error) => {
      setRunState("error");
      setRunError(err.message);
    },
  });

  const data: PipelineStatus | null =
    status.data ?? (status.isError ? MOCK : null);
  const isDemo = !!status.isError;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-[700px] px-6 py-6">
        <h1 className="text-[20px] font-semibold">Pipeline Status</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Automation runs daily at 9:00 AM IST
        </p>

        {/* Last Run */}
        <section
          className="relative mt-6 rounded-[12px] border p-6"
          style={{ background: "#161616", borderColor: "#2a2a2a" }}
        >
          {isDemo && (
            <span
              className="absolute right-3 top-3 rounded-full px-2 py-0.5 text-[10px]"
              style={{ background: "#2a2a2a", color: "#888" }}
            >
              Demo
            </span>
          )}
          <h2 className="mb-4 text-[14px] font-semibold">Last Run</h2>
          {status.isLoading ? (
            <div className="space-y-3">
              <div className="skeleton-shimmer h-4 w-1/2 rounded" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="skeleton-shimmer h-16 rounded-md" />
                ))}
              </div>
            </div>
          ) : data ? (
            <>
              <div className="flex items-center gap-2 text-[13px]">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{
                    background: data.status === "success" ? "#22c55e" : "#ef4444",
                  }}
                />
                <span>
                  {data.status === "success"
                    ? "Last run successful"
                    : "Last run failed"}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Metric label="Jobs Scraped" value={String(data.jobs_scraped)} />
                <Metric label="New Listings" value={String(data.new_jobs)} />
                <Metric label="Emails Sent" value={String(data.emails_sent)} />
                <Metric label="Duration" value={`${data.duration_seconds}s`} />
              </div>
              <p className="mt-3 text-[12px] text-muted-foreground">
                {relativeTime(data.timestamp)}
              </p>
            </>
          ) : null}
        </section>

        {/* Manual Trigger */}
        <section
          className="mt-4 rounded-[12px] border p-6"
          style={{ background: "#161616", borderColor: "#2a2a2a" }}
        >
          <h2 className="text-[14px] font-semibold">Manual Trigger</h2>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Run the full pipeline now — scrape → score → email
          </p>
          {runState === "success" ? (
            <div
              className="mt-4 flex h-11 w-full items-center justify-center rounded-md text-[13px] font-medium"
              style={{ background: "rgba(34,197,94,0.12)", color: "#22c55e" }}
            >
              ✓ Pipeline started — check back in ~30 seconds
            </div>
          ) : (
            <button
              disabled={runState === "running"}
              onClick={() => runPipeline.mutate()}
              className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-md text-[14px] font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-70"
              style={{ background: "#6366f1" }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background = "#4f46e5")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background = "#6366f1")
              }
            >
              {runState === "running" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" /> Run Pipeline Now
                </>
              )}
            </button>
          )}
          {runError && (
            <p className="mt-2 text-[12px]" style={{ color: "#ef4444" }}>
              {runError}
            </p>
          )}
        </section>

        {/* Next Scheduled */}
        <section
          className="mt-4 flex items-center justify-between rounded-[12px] border p-6"
          style={{ background: "#161616", borderColor: "#2a2a2a" }}
        >
          <div>
            <h2 className="text-[14px] font-semibold">Next Scheduled Run</h2>
            <p className="mt-1 text-[12px] text-muted-foreground">
              Runs automatically every day
            </p>
          </div>
          <div
            className="flex items-center gap-2 font-mono text-[18px] font-semibold"
            style={{ color: "#6366f1" }}
          >
            <Calendar className="h-4 w-4" />
            9:00 AM IST
          </div>
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded-md border px-4 py-3"
      style={{ background: "#1a1a1a", borderColor: "#2a2a2a" }}
    >
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-0.5 font-mono text-[16px] font-semibold">{value}</p>
    </div>
  );
}
