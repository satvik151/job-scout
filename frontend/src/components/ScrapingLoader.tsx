import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, Cpu, Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const stages = [
  { label: "Scraping", icon: Search },
  { label: "Processing", icon: Cpu },
  { label: "Scoring", icon: Sparkles },
  { label: "Almost done", icon: CheckCircle },
] as const;

const logs = [
  "→ Connecting to Internshala...",
  "→ Bypassing rate limits...",
  "→ Found 47 internship listings",
  "→ Filtering duplicates...",
  "→ 23 new listings identified",
  "→ Loading resume context...",
  "→ Sending batch to Groq API...",
  "→ Scored 8/23 jobs...",
  "→ Scored 16/23 jobs...",
  "→ Scored 23/23 jobs ✓",
  "→ Saving to database...",
  "→ Pipeline complete.",
];

export function ScrapingLoader() {
  const [currentStage, setCurrentStage] = useState(0);
  const [ellipsis, setEllipsis] = useState("");
  const [visibleLogs, setVisibleLogs] = useState<string[]>(logs.slice(0, 1));

  const stageMessage = useMemo(
    () => [
      "Scraping Internshala...",
      "Extracting job details...",
      "Scoring against your resume...",
      "Wrapping up...",
    ][currentStage],
    [currentStage],
  );

  useEffect(() => {
    setCurrentStage(0);
    setEllipsis("");
    setVisibleLogs(logs.slice(0, 1));

    const stageTimer = window.setInterval(() => {
      setCurrentStage((stage) => Math.min(stage + 1, stages.length - 1));
    }, 30000);

    const ellipsisTimer = window.setInterval(() => {
      setEllipsis((value) => (value === "" ? "." : value === "." ? ".." : value === ".." ? "..." : ""));
    }, 400);

    const logTimer = window.setInterval(() => {
      setVisibleLogs((current) => {
        const nextIndex = Math.min(current.length, logs.length - 1);
        if (nextIndex === current.length) {
          return current;
        }

        const nextLogs = [...current, logs[nextIndex]];
        return nextLogs.slice(-4);
      });
    }, 3500);

    return () => {
      window.clearInterval(stageTimer);
      window.clearInterval(ellipsisTimer);
      window.clearInterval(logTimer);
    };
  }, []);

  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center gap-8 px-4 py-10">
      <div className="flex w-full max-w-[720px] items-stretch justify-between gap-2 overflow-hidden">
        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const isCompleted = index < currentStage;
          const isActive = index === currentStage;
          const isPending = index > currentStage;

          return (
            <div key={stage.label} className="flex flex-1 items-center">
              <div className="flex min-w-0 flex-1 flex-col items-center">
                <motion.div
                  animate={isActive ? { scale: [1, 1.15, 1] } : undefined}
                  transition={isActive ? { repeat: Infinity, duration: 1.2 } : undefined}
                  className="flex h-10 w-10 items-center justify-center rounded-full border"
                  style={{
                    borderColor: isCompleted
                      ? "#22c55e"
                      : isActive
                        ? "#6366f1"
                        : "#2a2a2a",
                    color: isCompleted
                      ? "#22c55e"
                      : isActive
                        ? "#6366f1"
                        : "#333",
                  }}
                >
                  <Icon size={20} />
                </motion.div>
                <span
                  className="mt-2 text-[12px]"
                  style={{
                    color: isCompleted
                      ? "#22c55e"
                      : isActive
                        ? "#f5f5f5"
                        : "#555",
                  }}
                >
                  {stage.label}
                </span>
              </div>
              {index < stages.length - 1 && (
                <div className="relative mx-2 h-px flex-1 overflow-hidden rounded-full bg-[#2a2a2a]">
                  {isCompleted ? (
                    <div className="h-full w-full bg-[#22c55e]" />
                  ) : isActive ? (
                    <motion.div
                      className="h-full bg-[#6366f1]"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 30, ease: "linear" }}
                    />
                  ) : (
                    <div className="h-full w-full bg-[#2a2a2a]" />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="text-center">
        <AnimatePresence mode="wait">
          <motion.p
            key={currentStage}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="text-[18px] font-semibold text-[#f5f5f5]"
          >
            {stageMessage}
          </motion.p>
        </AnimatePresence>
        <span className="mt-1 inline-block font-mono text-[18px] text-[#6366f1]">
          {ellipsis}
        </span>
      </div>

      <div className="w-full max-w-[520px] rounded-[8px] border border-[#1f1f1f] bg-[#0d0d0d] p-4 font-mono text-[12px]">
        <div className="flex items-center">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="ml-1.5 h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
          <span className="ml-1.5 h-2.5 w-2.5 rounded-full bg-[#28ca42]" />
          <span className="ml-2 text-[11px] text-[#555]">job-scout — pipeline</span>
        </div>
        <div className="mt-3 h-[110px] overflow-hidden">
          <div className="flex flex-col gap-1">
            <AnimatePresence initial={false}>
              {visibleLogs.map((line) => {
                const color = line.includes("✓") || line.toLowerCase().includes("complete")
                  ? "#22c55e"
                  : line.includes("Found") || line.includes("identified")
                    ? "#6366f1"
                    : "#555";

                return (
                  <motion.div
                    key={line}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -8 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="truncate"
                    style={{ color }}
                  >
                    {line}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="w-full max-w-[520px]">
        <p className="text-[12px] text-[#555]">⏱ Usually takes 1–2 minutes</p>
        <div className="mt-2 h-[2px] w-full rounded-[1px] bg-[#1a1a1a]">
          <motion.div
            className="h-full rounded-[1px] bg-gradient-to-r from-[#6366f1] to-[#22c55e]"
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 110, ease: "linear" }}
          />
        </div>
      </div>
    </div>
  );
}