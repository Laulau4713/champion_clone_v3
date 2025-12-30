"use client";

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, Clock, MessageSquare, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { CircularProgress } from "@/components/ui/progress";
import { cn, formatDuration } from "@/lib/utils";

interface ScoreDisplayProps {
  currentScore: number;
  previousScore?: number;
  totalExchanges: number;
  elapsedSeconds: number;
  targetScore?: number;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({
  currentScore,
  previousScore,
  totalExchanges,
  elapsedSeconds,
  targetScore = 8,
}) => {
  const scoreDiff = previousScore !== undefined ? currentScore - previousScore : 0;
  const trend = scoreDiff > 0 ? "up" : scoreDiff < 0 ? "down" : "stable";

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor =
    trend === "up" ? "text-success-400" : trend === "down" ? "text-error-400" : "text-slate-400";

  return (
    <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700/50">
      <CardContent className="p-4">
        <div className="flex items-center gap-6">
          {/* Main Score */}
          <div className="flex-shrink-0">
            <CircularProgress value={currentScore} max={10} size={80} strokeWidth={6} />
          </div>

          {/* Stats */}
          <div className="flex-1 grid grid-cols-3 gap-4">
            {/* Trend */}
            <div className="text-center">
              <div className={cn("flex items-center justify-center gap-1", trendColor)}>
                <TrendIcon className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {scoreDiff > 0 ? "+" : ""}
                  {scoreDiff.toFixed(1)}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Tendance</p>
            </div>

            {/* Exchanges */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-secondary-400">
                <MessageSquare className="h-4 w-4" />
                <span className="text-sm font-medium">{totalExchanges}</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Échanges</p>
            </div>

            {/* Time */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-primary-400">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">{formatDuration(elapsedSeconds)}</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Durée</p>
            </div>
          </div>

          {/* Target */}
          <div className="flex-shrink-0 text-center px-4 border-l border-slate-700/50">
            <div className="flex items-center gap-1 text-slate-400">
              <Target className="h-4 w-4" />
              <span className="text-lg font-bold">{targetScore}</span>
            </div>
            <p className="text-xs text-slate-500">Objectif</p>
          </div>
        </div>

        {/* Progress bar to target */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Progression vers l&apos;objectif</span>
            <span>{Math.round((currentScore / targetScore) * 100)}%</span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className={cn(
                "h-full rounded-full",
                currentScore >= targetScore
                  ? "bg-success-500"
                  : currentScore >= targetScore * 0.7
                  ? "bg-warning-500"
                  : "bg-primary-500"
              )}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, (currentScore / targetScore) * 100)}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Mini version for header
export const ScoreDisplayMini: React.FC<{
  score: number;
  elapsedSeconds: number;
}> = ({ score, elapsedSeconds }) => (
  <div className="flex items-center gap-4">
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
          score >= 8
            ? "bg-success-500/20 text-success-400"
            : score >= 6
            ? "bg-warning-500/20 text-warning-400"
            : "bg-error-500/20 text-error-400"
        )}
      >
        {score.toFixed(1)}
      </div>
      <span className="text-xs text-slate-500">Score</span>
    </div>
    <div className="flex items-center gap-1 text-slate-400">
      <Clock className="h-4 w-4" />
      <span className="text-sm">{formatDuration(elapsedSeconds)}</span>
    </div>
  </div>
);

export default ScoreDisplay;
