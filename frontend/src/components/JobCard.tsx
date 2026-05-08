import { MapPin } from "lucide-react";
import type { Job } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";

function scoreColor(score: number) {
  if (score > 7) return "#22c55e";
  if (score >= 4) return "#f59e0b";
  return "#ef4444";
}

function relativeDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const now = new Date();
  const startOfDay = (date: Date) =>
    new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const days = Math.floor((startOfDay(now) - startOfDay(d)) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function senPill(s: Job["seniority_fit"]) {
  switch (s) {
    case "good fit":
      return { bg: "#166534", color: "#22c55e", label: "good fit" };
    case "underqualified":
      return { bg: "#78350f", color: "#f59e0b", label: "underqualified" };
    case "overqualified":
      return { bg: "#1e3a5f", color: "#60a5fa", label: "overqualified" };
  }
}

export function JobCard({ job, index }: { job: Job; index: number }) {
  const score = job.final_score ?? job.score ?? 0;
  const color = scoreColor(score);
  const pct = Math.max(0, Math.min(100, job.skills_match_pct ?? 0));
  const sen = senPill(job.seniority_fit);
  const ringPct = Math.max(0, Math.min(100, (score / 10) * 100));
  const visibleMissing = (job.missing_skills ?? []).slice(0, 4);
  const extra = (job.missing_skills?.length ?? 0) - visibleMissing.length;

  return (
    <article
      className="fade-up rounded-[12px] border border-border bg-card p-5 transition-all duration-200 hover:border-primary"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Row 1 */}
      <div className="flex items-start gap-4">
        <ScoreBadge score={score} />
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[15px] font-semibold text-foreground">
            {job.title}
          </h3>
          <p className="truncate text-[13px] text-muted-foreground">{job.company}</p>
          {job.location && (
            <p className="mt-0.5 flex items-center gap-1 text-[12px] text-muted-foreground">
              <MapPin className="h-3 w-3" />
              <span className="truncate">{job.location}</span>
            </p>
          )}
        </div>
        {job.is_new && (
          <span className="rounded-full border border-primary/40 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
            NEW
          </span>
        )}
      </div>

      {/* Row 2 — skills bar */}
      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between text-[12px]">
          <span className="text-muted-foreground">Skills Match</span>
          <span className="font-mono text-foreground">{pct.toFixed(0)}%</span>
        </div>
        <div className="h-[6px] w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full"
            style={{
              width: `${pct}%`,
              background: "linear-gradient(90deg, #6366f1, #22c55e)",
            }}
          />
        </div>
      </div>

      {/* Row 3 — seniority + date */}
      <div className="mt-4 flex items-center justify-between">
        <span
          className="rounded-full px-2.5 py-0.5 text-[11px] font-medium"
          style={{ background: sen.bg, color: sen.color }}
        >
          {sen.label}
        </span>
        <span className="text-[12px] text-muted-foreground">
          {relativeDate(job.scraped_at)}
        </span>
      </div>

      {/* Row 4 — missing skills */}
      <div className="mt-4">
        <p className="mb-1.5 text-[11px] uppercase tracking-wide text-muted-foreground">
          Missing skills
        </p>
        {visibleMissing.length === 0 ? (
          <span className="text-[11px]" style={{ color: "#22c55e" }}>
            No missing skills
          </span>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {visibleMissing.map((s) => (
              <span
                key={s}
                className="rounded-full px-2 py-0.5 text-[11px]"
                style={{ background: "#2a2a2a", color: "#888" }}
              >
                {s}
              </span>
            ))}
            {extra > 0 && (
              <span
                className="rounded-full px-2 py-0.5 text-[11px]"
                style={{ background: "#2a2a2a", color: "#888" }}
              >
                +{extra} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Row 5 — reason */}
      {job.reason && (
        <p
          className="mt-3 text-[12px] italic"
          style={{
            color: "#666",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {job.reason}
        </p>
      )}

      {/* Row 6 — apply */}
      <button
        onClick={() => window.open(job.url, "_blank", "noopener,noreferrer")}
        className="mt-4 flex h-9 w-full items-center justify-center rounded-md border border-border text-[13px] font-medium text-foreground transition hover:border-primary hover:text-primary"
      >
        Apply →
      </button>
    </article>
  );
}