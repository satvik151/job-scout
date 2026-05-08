import { motion } from "framer-motion";

function scoreColor(score: number) {
  if (score > 7) return "#22c55e";
  if (score >= 4) return "#f59e0b";
  return "#ef4444";
}

export function ScoreBadge({ score }: { score: number }) {
  const color = scoreColor(score);
  const circumference = 2 * Math.PI * 22;
  const offset = (1 - score / 10) * circumference;

  return (
    <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center">
      <svg viewBox="0 0 52 52" width={52} height={52} style={{ filter: `drop-shadow(0 0 12px ${color}66)` }}>
        {/* Background circle */}
        <circle cx={26} cy={26} r={22} strokeWidth={4} fill="none" stroke="#2a2a2a" />

        {/* Animated foreground circle */}
        <motion.circle
          cx={26}
          cy={26}
          r={22}
          strokeWidth={4}
          fill="none"
          stroke={color}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          whileInView={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
          viewport={{ once: true }}
          style={{ transform: "rotate(-90deg)", transformOrigin: "26px 26px" }}
        />

        {/* Center text */}
        <motion.text
          x={26}
          y={26}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={13}
          fontFamily="monospace"
          fontWeight="600"
          fill={color}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          viewport={{ once: true }}
        >
          {score.toFixed(1)}
        </motion.text>
      </svg>
    </div>
  );
}
