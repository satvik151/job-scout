import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { RefreshCw, Mail, Play, Loader2, Search, Inbox, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { ProtectedGate } from "@/components/ProtectedGate";
import { Navbar } from "@/components/Navbar";
import { JobCard } from "@/components/JobCard";
import { api, type Job, type JobsResponse } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useCountUp } from "@/hooks/useCountUp";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Job Scout" }] }),
  component: () => (
    <ProtectedGate>
      <DashboardPage />
    </ProtectedGate>
  ),
});

function DashboardPage() {
  const { user } = useAuthStore();
  const [jobsData, setJobsData] = useState<JobsResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [seniority, setSeniority] = useState<"all" | Job["seniority_fit"]>("all");
  const [sortBy, setSortBy] = useState<"score" | "skills" | "fresh">("score");

  const fetchJobs = useMutation({
    mutationFn: () => api.fetchJobs(2),
    onSuccess: (data) => {
      setJobsData(data);
      setErrorMsg(null);
      const newCount = data.jobs.filter((j) => j.is_new).length;
      toast.success(`Fetched ${data.jobs.length} jobs, ${newCount} new`);
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      toast.error(err.message);
    },
  });

  const sendDigest = useMutation({
    mutationFn: () => api.sendDigest(),
    onSuccess: () => toast.success("Digest sent to your email"),
    onError: (err: Error) => toast.error(err.message),
  });

  const runPipeline = useMutation({
    mutationFn: () => api.runPipeline(),
    onSuccess: () => toast.success("Pipeline started in background"),
    onError: (err: Error) => toast.error(err.message),
  });

  const busy = fetchJobs.isPending || sendDigest.isPending || runPipeline.isPending;
  const jobs = jobsData?.jobs ?? [];

  const filteredJobs = useMemo(() => {
    let list = jobs.slice();
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (j) =>
          j.title?.toLowerCase().includes(q) ||
          j.company?.toLowerCase().includes(q),
      );
    }
    if (seniority !== "all") {
      list = list.filter((j) => j.seniority_fit === seniority);
    }
    if (sortBy === "score") {
      list.sort(
        (a, b) => (b.final_score ?? b.score) - (a.final_score ?? a.score),
      );
    } else if (sortBy === "skills") {
      list.sort((a, b) => b.skills_match_pct - a.skills_match_pct);
    } else {
      list.sort(
        (a, b) =>
          new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime(),
      );
    }
    return list;
  }, [jobs, search, seniority, sortBy]);

  const stats = useMemo(() => {
    const total = jobs.length;
    const newCount = jobs.filter((j) => j.is_new).length;
    const top = jobs.reduce(
      (m, j) => Math.max(m, j.final_score ?? j.score ?? 0),
      0,
    );
    const avg = total
      ? jobs.reduce((s, j) => s + (j.skills_match_pct ?? 0), 0) / total
      : 0;
    return { total, newCount, top, avg };
  }, [jobs]);

  // Count-up animations for stats
  const animatedTotal = useCountUp(stats.total);
  const animatedNewCount = useCountUp(stats.newCount);
  const animatedTop = useCountUp(stats.top, 1500);
  const animatedAvg = useCountUp(stats.avg);

  return (
    <motion.div
      className="min-h-screen"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      <Navbar />
      <main className="mx-auto max-w-[1200px] px-6 py-6">
        {/* Stats */}
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[0, 1, 2, 3].map((index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: "easeOut", delay: index * 0.08 }}
            >
              {index === 0 && <StatCard label="Total Jobs Fetched" value={animatedTotal.toString()} />}
              {index === 1 && <StatCard label="New Jobs" value={animatedNewCount.toString()} />}
              {index === 2 && <StatCard label="Top Score" value={`${animatedTop.toFixed(1)}/10`} />}
              {index === 3 && <StatCard label="Avg Skills Match" value={`${Math.round(animatedAvg)}%`} />}
            </motion.div>
          ))}
        </section>

        {/* Actions */}
        <section className="mt-6 flex flex-wrap gap-2">
          <button
            disabled={busy}
            onClick={() => fetchJobs.mutate()}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:opacity-60"
          >
            {fetchJobs.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Scoring jobs...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Fetch & Score Jobs
              </>
            )}
          </button>
          <button
            disabled={busy}
            onClick={() => sendDigest.mutate()}
            className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm text-foreground transition hover:border-primary disabled:opacity-60"
          >
            <Mail className="h-4 w-4" />
            Send Digest Email
          </button>
          <button
            disabled={busy}
            onClick={() => runPipeline.mutate()}
            className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm text-muted-foreground transition hover:bg-secondary hover:text-foreground disabled:opacity-60"
          >
            <Play className="h-4 w-4" />
            Run Pipeline
          </button>
        </section>

        {/* Filters */}
        <section className="mt-6 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search jobs..."
              className="h-10 w-full rounded-md border border-border bg-card pl-9 pr-3 text-sm outline-none transition focus:border-primary"
            />
          </div>
          <select
            value={seniority}
            onChange={(e) =>
              setSeniority(e.target.value as typeof seniority)
            }
            className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-primary"
          >
            <option value="all">All</option>
            <option value="good fit">Good fit</option>
            <option value="underqualified">Underqualified</option>
            <option value="overqualified">Overqualified</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="h-10 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-primary"
          >
            <option value="score">Sort: Score</option>
            <option value="skills">Sort: Skills Match</option>
            <option value="fresh">Sort: Freshness</option>
          </select>
        </section>

        {/* Jobs */}
        <section className="mt-6">
          {fetchJobs.isPending ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="skeleton-shimmer h-[280px] rounded-[12px] border border-border"
                />
              ))}
            </div>
          ) : errorMsg ? (
            <div
              className="rounded-[12px] p-5 text-center"
              style={{
                border: "1px solid rgba(239,68,68,0.25)",
                background: "rgba(239,68,68,0.03)",
              }}
            >
              <p className="text-[13px]" style={{ color: "#ef4444" }}>
                Could not fetch jobs — check if the backend is running
              </p>
              <button
                onClick={() => fetchJobs.mutate()}
                className="mt-3 rounded-md px-4 py-2 text-[13px] transition"
                style={{ border: "1px solid rgba(239,68,68,0.4)", color: "#ef4444" }}
              >
                Retry
              </button>
            </div>
          ) : jobs.length === 0 ? (
            jobsData ? (
              <div className="flex flex-col items-center py-[60px] text-center">
                <Inbox className="h-12 w-12" style={{ color: "#2a2a2a" }} />
                <p className="mt-3 text-[15px]" style={{ color: "#888" }}>
                  No jobs found
                </p>
                {user && !user.has_resume && (
                  <Link
                    to="/profile"
                    className="mt-4 rounded-md px-4 py-2 text-[13px] transition"
                    style={{ border: "1px solid #6366f1", color: "#6366f1" }}
                  >
                    Upload Resume First
                  </Link>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center py-[60px] text-center">
                <Sparkles className="h-12 w-12" style={{ color: "#2a2a2a" }} />
                <p className="mt-3 text-[15px]" style={{ color: "#888" }}>
                  Fetch jobs to get started
                </p>
                <p className="mt-1 text-[13px]" style={{ color: "#555" }}>
                  Click "Fetch & Score Jobs" above
                </p>
              </div>
            )
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {filteredJobs.map((job, i) => (
                <JobCard key={`${job.url}-${i}`} job={job} index={i} />
              ))}
            </div>
          )}
        </section>
      </main>
    </motion.div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      <p className="text-[12px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-mono text-[28px] font-semibold text-foreground">
        {value}
      </p>
    </div>
  );
}