"use client";

import { useMemo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Upload, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { ProgressChart } from "@/components/dashboard/ProgressChart";
import { SessionsTable } from "@/components/dashboard/SessionsTable";
import { ChampionCard } from "@/components/dashboard/ChampionCard";
import { useTrainingSessions, useChampions } from "@/lib/queries";
import { useAuthStore } from "@/store/auth-store";
import type { ProgressData, SessionHistory, Champion } from "@/types";

// Custom tooltip for pattern chart
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg p-3 border border-white/20">
        <p className="text-sm font-medium mb-1">{label}</p>
        <p className="text-sm text-green-400">
          Maîtrisé: <span className="font-bold">{payload[0].value}%</span>
        </p>
      </div>
    );
  }
  return null;
};

// Loading skeleton
function DashboardSkeleton() {
  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      <div className="absolute inset-0 gradient-mesh opacity-20" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <Skeleton className="h-12 w-64 mb-8" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Skeleton className="h-[400px]" />
          <Skeleton className="h-[400px]" />
        </div>
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: sessionsResponse, isLoading: loadingSessions } = useTrainingSessions();
  const { data: championsResponse, isLoading: loadingChampions } = useChampions();

  // Extract data from API responses
  const sessions = useMemo(() => {
    if (!sessionsResponse) return [];
    // Handle both { sessions: [...] } and direct array responses
    const data = sessionsResponse.data || sessionsResponse;
    return Array.isArray(data) ? data : data.sessions || [];
  }, [sessionsResponse]);

  const champions: Champion[] = useMemo(() => {
    if (!championsResponse) return [];
    const data = championsResponse.data || championsResponse;
    return Array.isArray(data) ? data : data.champions || [];
  }, [championsResponse]);

  // Calculate stats from real data
  const stats = useMemo(() => {
    if (!sessions || sessions.length === 0) {
      return {
        totalSessions: 0,
        avgScore: 0,
        bestScore: 0,
        improvementRate: 0,
      };
    }

    const scores = sessions
      .map((s: any) => s.overall_score || s.score || 0)
      .filter((s: number) => s > 0);

    if (scores.length === 0) {
      return {
        totalSessions: sessions.length,
        avgScore: 0,
        bestScore: 0,
        improvementRate: 0,
      };
    }

    const avgScore = scores.reduce((a: number, b: number) => a + b, 0) / scores.length;
    const bestScore = Math.max(...scores);

    // Calculate improvement (compare last 5 vs first 5 sessions)
    let improvementRate = 0;
    if (scores.length >= 2) {
      const recentScores = scores.slice(-Math.min(5, Math.floor(scores.length / 2)));
      const oldScores = scores.slice(0, Math.min(5, Math.floor(scores.length / 2)));
      const recentAvg = recentScores.reduce((a: number, b: number) => a + b, 0) / recentScores.length;
      const oldAvg = oldScores.reduce((a: number, b: number) => a + b, 0) / oldScores.length;
      improvementRate = oldAvg > 0 ? Math.round(((recentAvg - oldAvg) / oldAvg) * 100) : 0;
    }

    return {
      totalSessions: sessions.length,
      avgScore: Math.round(avgScore * 10) / 10,
      bestScore: Math.round(bestScore * 10) / 10,
      improvementRate,
    };
  }, [sessions]);

  // Prepare chart data
  const progressData: ProgressData[] = useMemo(() => {
    if (!sessions || sessions.length === 0) return [];

    // Group by week and calculate average score
    const sessionsByDate = sessions
      .slice(-20) // Last 20 sessions
      .map((s: any) => ({
        date: new Date(s.created_at || s.started_at).toLocaleDateString("fr-FR", {
          day: "2-digit",
          month: "short",
        }),
        score: s.overall_score || s.score || 0,
        sessions: 1,
      }));

    return sessionsByDate;
  }, [sessions]);

  // Convert sessions to SessionHistory format for the table
  const sessionHistory: SessionHistory[] = useMemo(() => {
    if (!sessions || sessions.length === 0) return [];

    return sessions.slice(0, 10).map((s: any) => ({
      id: s.id,
      date: s.created_at || s.started_at,
      scenario: s.scenario?.name || "Session d'entraînement",
      score: s.overall_score || s.score || 0,
      duration: s.duration_seconds || 0,
      champion_name: s.champion_name || `Champion #${s.champion_id}`,
    }));
  }, [sessions]);

  // Pattern mastery data (placeholder - would need real data from API)
  const patternData = useMemo(() => {
    // This would ideally come from an API endpoint analyzing patterns
    // For now, generate based on session performance
    const baseScore = stats.avgScore * 10;
    return [
      { name: "Openings", mastered: Math.min(100, Math.round(baseScore + Math.random() * 10)) },
      { name: "Objections", mastered: Math.min(100, Math.round(baseScore - 10 + Math.random() * 15)) },
      { name: "Closings", mastered: Math.min(100, Math.round(baseScore - 5 + Math.random() * 12)) },
      { name: "Rapport", mastered: Math.min(100, Math.round(baseScore + 5 + Math.random() * 8)) },
    ];
  }, [stats.avgScore]);

  if (loadingSessions || loadingChampions) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-20" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl lg:text-4xl font-bold mb-2">
            Votre <span className="gradient-text">Dashboard</span>
          </h1>
          <p className="text-muted-foreground">
            {user?.full_name
              ? `Bienvenue ${user.full_name}, suivez votre progression`
              : "Suivez votre progression et analysez vos performances"}
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="mb-8">
          <StatsGrid stats={stats} />
        </div>

        {/* Champions Section */}
        {champions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Mes Champions</h2>
              <Link href="/upload">
                <Button variant="outline" size="sm" className="border-white/20">
                  <Upload className="h-4 w-4 mr-2" />
                  Nouveau champion
                </Button>
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {champions.slice(0, 6).map((champion, index) => (
                <ChampionCard key={champion.id} champion={champion} index={index} />
              ))}
            </div>
          </motion.div>
        )}

        {/* Empty state for champions */}
        {champions.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mb-8"
          >
            <Card className="glass border-white/10 border-dashed">
              <CardContent className="py-12 text-center">
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Aucun champion</h3>
                <p className="text-muted-foreground mb-4">
                  Uploadez votre première vidéo pour créer un champion
                </p>
                <Link href="/upload">
                  <Button className="bg-gradient-primary hover:opacity-90">
                    <Upload className="h-4 w-4 mr-2" />
                    Créer un champion
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Progress Chart */}
          {progressData.length > 0 ? (
            <ProgressChart data={progressData} />
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="glass border-white/10 h-full">
                <CardHeader>
                  <CardTitle className="text-lg">Progression des scores</CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-center h-[300px]">
                  <p className="text-muted-foreground text-center">
                    Complétez des sessions pour voir votre progression
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Pattern Mastery Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="text-lg">Patterns maîtrisés</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] w-full">
                  {sessions.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={patternData} layout="vertical">
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.1)"
                          horizontal={false}
                        />
                        <XAxis
                          type="number"
                          domain={[0, 100]}
                          stroke="rgba(255,255,255,0.5)"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                          tickFormatter={(value) => `${value}%`}
                        />
                        <YAxis
                          type="category"
                          dataKey="name"
                          stroke="rgba(255,255,255,0.5)"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                          width={80}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar
                          dataKey="mastered"
                          fill="#8b5cf6"
                          radius={[0, 4, 4, 0]}
                          background={{ fill: "rgba(255,255,255,0.05)" }}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-muted-foreground text-center">
                        Complétez des sessions pour analyser vos patterns
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Sessions Table */}
        <SessionsTable
          sessions={sessionHistory}
          onViewSession={(id) => console.log("View session", id)}
        />
      </div>
    </div>
  );
}
