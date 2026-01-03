"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Trophy, Target, Clock, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  iconColor: string;
  delay?: number;
}

function StatCard({
  title,
  value,
  change,
  icon: Icon,
  iconColor,
  delay = 0,
}: StatCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card className="glass border-white/10 hover:border-primary-500/30 transition-all">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">{title}</p>
              <p className="text-3xl font-bold">{value}</p>
              {change !== undefined && (
                <div
                  className={cn(
                    "flex items-center gap-1 mt-2 text-sm",
                    isPositive && "text-green-400",
                    isNegative && "text-red-400",
                    !isPositive && !isNegative && "text-muted-foreground"
                  )}
                >
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : isNegative ? (
                    <TrendingDown className="h-4 w-4" />
                  ) : null}
                  <span>
                    {isPositive ? "+" : ""}
                    {change}% vs mois dernier
                  </span>
                </div>
              )}
            </div>
            <div
              className={cn("p-3 rounded-xl", iconColor.replace("text-", "bg-") + "/20")}
            >
              <Icon className={cn("h-6 w-6", iconColor)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

interface StatsGridProps {
  stats: {
    totalSessions: number;
    avgScore?: number;
    averageScore?: number;
    bestScore: number;
    improvement?: number;
    improvementRate?: number;
  };
  isLoading?: boolean;
}

export function StatsGrid({ stats, isLoading }: StatsGridProps) {
  const avgScore = stats.avgScore ?? stats.averageScore ?? 0;
  const improvement = stats.improvement ?? stats.improvementRate ?? 0;

  const cards = [
    {
      title: "Sessions totales",
      value: stats.totalSessions,
      change: undefined,
      icon: Target,
      iconColor: "text-blue-400",
    },
    {
      title: "Score moyen",
      value: `${Math.round(avgScore)}/100`,
      change: undefined,
      icon: Zap,
      iconColor: "text-purple-400",
    },
    {
      title: "Meilleur score",
      value: `${Math.round(stats.bestScore)}/100`,
      change: undefined,
      icon: Trophy,
      iconColor: "text-yellow-400",
    },
    {
      title: "Progression",
      value: `${improvement >= 0 ? "+" : ""}${improvement}%`,
      change: improvement,
      icon: TrendingUp,
      iconColor: "text-green-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <StatCard key={card.title} {...card} delay={index * 0.1} />
      ))}
    </div>
  );
}
