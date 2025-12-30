"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  SkipForward,
  Square,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CircularProgress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface FeedbackPanelProps {
  score: number;
  feedback?: string;
  suggestions?: string[];
  strengths?: string[];
  improvements?: string[];
  championWouldSay?: string;
  onNextScenario?: () => void;
  onEndSession?: () => void;
  isSessionComplete?: boolean;
}

export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({
  score,
  feedback,
  suggestions = [],
  strengths = [],
  improvements = [],
  championWouldSay,
  onNextScenario,
  onEndSession,
  isSessionComplete,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Feedback</CardTitle>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-md hover:bg-slate-700 transition-colors md:hidden"
          >
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-slate-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-slate-400" />
            )}
          </button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-6"
            >
              {/* Score */}
              <div className="flex justify-center py-4">
                <CircularProgress value={score} max={10} size={140} />
              </div>

              {/* Feedback Text */}
              {(feedback || championWouldSay) && (
                <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {feedback || championWouldSay}
                  </p>
                </div>
              )}

              {/* Strengths */}
              {strengths.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-success-400">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Points forts</span>
                  </div>
                  <ul className="space-y-1">
                    {strengths.map((strength, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-success-400 mt-1">✓</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {improvements.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-warning-400">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">À améliorer</span>
                  </div>
                  <ul className="space-y-1">
                    {improvements.map((improvement, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-warning-400 mt-1">→</span>
                        {improvement}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-secondary-400">
                    <Lightbulb className="h-4 w-4" />
                    <span className="text-sm font-medium">Suggestions</span>
                  </div>
                  <ul className="space-y-2">
                    {suggestions.map((suggestion, i) => (
                      <li
                        key={i}
                        className={cn(
                          "p-3 rounded-lg text-sm text-slate-300",
                          "bg-secondary-500/10 border border-secondary-500/20"
                        )}
                      >
                        💡 {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col gap-2 pt-4 border-t border-slate-700/50">
                {!isSessionComplete && onNextScenario && (
                  <Button onClick={onNextScenario} variant="default">
                    <SkipForward className="mr-2 h-4 w-4" />
                    Scénario suivant
                  </Button>
                )}
                {onEndSession && (
                  <Button onClick={onEndSession} variant="outline">
                    <Square className="mr-2 h-4 w-4" />
                    Terminer la session
                  </Button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};

export default FeedbackPanel;
