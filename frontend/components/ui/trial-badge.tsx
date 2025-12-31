"use client";

import { Badge } from "@/components/ui/badge";
import { Sparkles, Crown } from "lucide-react";
import { cn } from "@/lib/utils";

interface TrialBadgeProps {
  sessionsUsed: number;
  sessionsMax: number;
  isPremium: boolean;
  className?: string;
}

export function TrialBadge({
  sessionsUsed,
  sessionsMax,
  isPremium,
  className,
}: TrialBadgeProps) {
  if (isPremium) {
    return (
      <Badge
        className={cn(
          "bg-gradient-to-r from-amber-500/10 to-yellow-500/10 text-amber-400 border-amber-500/20",
          className
        )}
      >
        <Crown className="w-3 h-3 mr-1" />
        Premium
      </Badge>
    );
  }

  const remaining = sessionsMax - sessionsUsed;
  const isExpired = remaining <= 0;
  const isLow = remaining === 1;

  return (
    <Badge
      className={cn(
        "transition-colors",
        isExpired
          ? "bg-red-500/10 text-red-400 border-red-500/20"
          : isLow
            ? "bg-orange-500/10 text-orange-400 border-orange-500/20"
            : "bg-violet-500/10 text-violet-400 border-violet-500/20",
        className
      )}
    >
      <Sparkles className="w-3 h-3 mr-1" />
      {isExpired
        ? "Essai termin\u00e9"
        : `Essai gratuit - ${sessionsUsed}/${sessionsMax}`}
    </Badge>
  );
}
