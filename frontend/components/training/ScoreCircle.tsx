"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ScoreCircleProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  className?: string;
}

export function ScoreCircle({
  score,
  size = 100,
  strokeWidth = 8,
  showLabel = true,
  className,
}: ScoreCircleProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = (score / 10) * 100;
  const offset = circumference - (progress / 100) * circumference;

  const getScoreColor = (score: number) => {
    if (score >= 8) return { stroke: "#22c55e", text: "text-green-400" };
    if (score >= 6) return { stroke: "#eab308", text: "text-yellow-400" };
    if (score >= 4) return { stroke: "#f97316", text: "text-orange-400" };
    return { stroke: "#ef4444", text: "text-red-400" };
  };

  const colors = getScoreColor(score);

  return (
    <div className={cn("relative inline-flex", className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-white/10"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>

      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={cn("text-2xl font-bold", colors.text)}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: "spring" }}
          >
            {score.toFixed(1)}
          </motion.span>
          <span className="text-xs text-muted-foreground">/10</span>
        </div>
      )}
    </div>
  );
}
