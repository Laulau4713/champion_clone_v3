"use client";

import React from "react";
import { motion } from "framer-motion";
import { Activity, TrendingUp, Award, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { StatsData } from "@/types";
import { cn } from "@/lib/utils";

interface StatsCardsProps {
  stats: StatsData;
  isLoading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: number;
  color: "primary" | "secondary" | "success" | "warning";
  index: number;
}

const colorClasses = {
  primary: {
    bg: "bg-primary-500/10",
    text: "text-primary-400",
    icon: "text-primary-500",
  },
  secondary: {
    bg: "bg-secondary-500/10",
    text: "text-secondary-400",
    icon: "text-secondary-500",
  },
  success: {
    bg: "bg-success-500/10",
    text: "text-success-400",
    icon: "text-success-500",
  },
  warning: {
    bg: "bg-warning-500/10",
    text: "text-warning-400",
    icon: "text-warning-500",
  },
};

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  color,
  index,
}) => {
  const colors = colorClasses[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="hover:border-slate-600 transition-colors">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">{title}</p>
              <p className="text-3xl font-bold text-white">{value}</p>
              {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
              {trend !== undefined && (
                <div
                  className={cn(
                    "flex items-center gap-1 mt-2 text-xs",
                    trend >= 0 ? "text-success-400" : "text-error-400"
                  )}
                >
                  <TrendingUp
                    className={cn("h-3 w-3", trend < 0 && "rotate-180")}
                  />
                  <span>
                    {trend >= 0 ? "+" : ""}
                    {trend}%
                  </span>
                  <span className="text-slate-500">vs précédent</span>
                </div>
              )}
            </div>
            <div className={cn("p-3 rounded-lg", colors.bg)}>
              <div className={colors.icon}>{icon}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const LoadingSkeleton: React.FC = () => (
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
    {[1, 2, 3, 4].map((i) => (
      <Card key={i}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-3 w-20" />
            </div>
            <Skeleton className="w-12 h-12 rounded-lg" />
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
);

export const StatsCards: React.FC<StatsCardsProps> = ({ stats, isLoading }) => {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  const cards: Omit<StatCardProps, "index">[] = [
    {
      title: "Sessions totales",
      value: stats.totalSessions,
      subtitle: "entraînements réalisés",
      icon: <Activity className="h-6 w-6" />,
      color: "primary",
    },
    {
      title: "Score moyen",
      value: stats.avgScore.toFixed(1),
      subtitle: "sur 10",
      icon: <Target className="h-6 w-6" />,
      color: "secondary",
    },
    {
      title: "Meilleur score",
      value: stats.bestScore.toFixed(1),
      subtitle: "record personnel",
      icon: <Award className="h-6 w-6" />,
      color: "success",
    },
    {
      title: "Progression",
      value: `${stats.improvementRate >= 0 ? "+" : ""}${stats.improvementRate}%`,
      subtitle: "amélioration globale",
      icon: <TrendingUp className="h-6 w-6" />,
      trend: stats.improvementRate,
      color: "warning",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <StatCard key={card.title} {...card} index={index} />
      ))}
    </div>
  );
};

export default StatsCards;
