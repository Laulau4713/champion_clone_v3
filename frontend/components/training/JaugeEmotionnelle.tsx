"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { MoodState } from "@/types";

interface JaugeEmotionnelleProps {
  value: number;
  delta?: number;
  mood: MoodState;
  visible?: boolean;
  threshold?: number;
  className?: string;
}

const moodConfig: Record<MoodState, { label: string; emoji: string; color: string }> = {
  hostile: { label: "Hostile", emoji: "😠", color: "text-red-500" },
  aggressive: { label: "Agressif", emoji: "😤", color: "text-orange-500" },
  skeptical: { label: "Sceptique", emoji: "🤨", color: "text-yellow-500" },
  neutral: { label: "Neutre", emoji: "😐", color: "text-gray-400" },
  interested: { label: "Intéressé", emoji: "🙂", color: "text-green-400" },
  enthusiastic: { label: "Enthousiaste", emoji: "😊", color: "text-green-500" },
};

export function JaugeEmotionnelle({
  value,
  delta,
  mood,
  visible = true,
  threshold = 80,
  className,
}: JaugeEmotionnelleProps) {
  const moodInfo = moodConfig[mood] || moodConfig.neutral;
  const isAboveThreshold = value >= threshold;

  // Color based on value
  const getGaugeColor = () => {
    if (value >= 70) return "bg-green-500";
    if (value >= 50) return "bg-yellow-500";
    if (value >= 30) return "bg-orange-500";
    return "bg-red-500";
  };

  if (!visible) {
    return (
      <div className={cn("glass rounded-xl p-4", className)}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Jauge Émotionnelle</span>
          <span className={cn("text-xl", moodInfo.color)}>{moodInfo.emoji}</span>
        </div>
        <div className="h-3 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-gray-600 to-gray-500 w-full animate-pulse" />
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center italic">
          Jauge cachée en mode expert
        </p>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className={cn("glass rounded-xl p-4", className)}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Jauge Émotionnelle</span>
          <Tooltip>
            <TooltipTrigger>
              <span className={cn("text-xl cursor-help", moodInfo.color)}>
                {moodInfo.emoji}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>{moodInfo.label}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Gauge bar */}
        <div className="relative h-4 bg-white/10 rounded-full overflow-hidden">
          {/* Threshold marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white/50 z-10"
            style={{ left: `${threshold}%` }}
          />

          {/* Value bar */}
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={cn("h-full rounded-full", getGaugeColor())}
          />
        </div>

        {/* Value and delta */}
        <div className="flex items-center justify-between mt-2">
          <span className="text-lg font-bold">{value}</span>

          <AnimatePresence>
            {delta !== undefined && delta !== 0 && (
              <motion.span
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={cn(
                  "text-sm font-medium px-2 py-0.5 rounded-full",
                  delta > 0 ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                )}
              >
                {delta > 0 ? `+${delta}` : delta}
              </motion.span>
            )}
          </AnimatePresence>

          <Tooltip>
            <TooltipTrigger>
              <span className="text-xs text-muted-foreground cursor-help">
                Seuil: {threshold}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>Atteindre {threshold} pour conclure la vente</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Conversion indicator */}
        {isAboveThreshold && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-3 p-2 bg-green-500/20 rounded-lg text-center"
          >
            <span className="text-green-400 text-sm font-medium">
              Conversion possible !
            </span>
          </motion.div>
        )}
      </div>
    </TooltipProvider>
  );
}
