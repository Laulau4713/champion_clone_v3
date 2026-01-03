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
import { Upload, Sparkles, BookOpen, Target, Crown, ArrowRight, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { ProgressChart } from "@/components/dashboard/ProgressChart";
import { SessionsTable } from "@/components/dashboard/SessionsTable";
import { ChampionCard } from "@/components/dashboard/ChampionCard";
import { useTrainingSessions, useChampions, useSkillsProgress, useVoiceSessions } from "@/lib/queries";
import type { VoiceSessionListItem } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
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

  // Check if user is on free plan
  const isFreeUser = user?.subscription_plan === "free";
  const isEnterpriseUser = user?.subscription_plan === "enterprise";
  const trialSessionsUsed = user?.trial_sessions_used || 0;
  const trialSessionsMax = user?.trial_sessions_max || 3;

  // Fetch voice sessions (V2) for all users
  const { data: voiceSessions, isLoading: loadingVoiceSessions } = useVoiceSessions();

  // Only fetch champions and champion-based sessions for enterprise users
  const { data: sessionsResponse, isLoading: loadingSessions } = useTrainingSessions({
    enabled: isEnterpriseUser,
  });
  const { data: championsResponse, isLoading: loadingChampions } = useChampions({
    enabled: isEnterpriseUser,
  });
  const { data: skillsProgress } = useSkillsProgress();

  // Extract data from API responses - Use voice sessions for non-enterprise
  const sessions = useMemo(() => {
    // For non-enterprise users, use voice sessions (V2)
    if (!isEnterpriseUser) {
      if (!voiceSessions) return [];
      return voiceSessions.map((vs: VoiceSessionListItem) => ({
        id: vs.id,
        created_at: vs.created_at,
        started_at: vs.created_at,
        overall_score: vs.score,
        score: vs.score,
        duration_seconds: vs.duration_seconds,
        scenario: { name: vs.skill_name },
        champion_name: vs.skill_name,
        status: vs.status,
        current_gauge: vs.current_gauge,
        starting_gauge: vs.starting_gauge,
      }));
    }
    // For enterprise users, use champion sessions (V1)
    if (!sessionsResponse) return [];
    const response = sessionsResponse as any;
    const data = response?.data || response;
    return Array.isArray(data) ? data : data?.sessions || [];
  }, [isEnterpriseUser, voiceSessions, sessionsResponse]);

  const champions: Champion[] = useMemo(() => {
    if (!championsResponse) return [];
    const response = championsResponse as any;
    const data = response?.data || response;
    return Array.isArray(data) ? data : data?.champions || [];
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
    // For now, generate based on session performance (score is already 0-100)
    const baseScore = stats.avgScore;
    return [
      { name: "Openings", mastered: Math.min(100, Math.max(0, Math.round(baseScore + 5))) },
      { name: "Objections", mastered: Math.min(100, Math.max(0, Math.round(baseScore - 10))) },
      { name: "Closings", mastered: Math.min(100, Math.max(0, Math.round(baseScore - 5))) },
      { name: "Rapport", mastered: Math.min(100, Math.max(0, Math.round(baseScore + 10))) },
    ];
  }, [stats.avgScore]);

  // Show loading state: for enterprise check champion data, for others check voice sessions
  const isLoading = isEnterpriseUser
    ? (loadingSessions || loadingChampions)
    : loadingVoiceSessions;

  if (isLoading) {
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
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl lg:text-4xl font-bold">
              Votre <span className="gradient-text">Dashboard</span>
            </h1>
            {isFreeUser && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-400">
                Essai gratuit
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground">
            {user?.full_name
              ? `Bienvenue ${user.full_name}, suivez votre progression`
              : "Suivez votre progression et analysez vos performances"}
          </p>
        </motion.div>

        {/* Trial Banner for Free Users */}
        {isFreeUser && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <Alert className="border-yellow-500/30 bg-yellow-500/10">
              <Sparkles className="h-4 w-4 text-yellow-400" />
              <AlertDescription className="flex items-center justify-between">
                <span className="text-yellow-200">
                  <strong>Essai gratuit</strong> — Vous avez accès à 1 cours, 1 quiz et {trialSessionsMax} sessions d&apos;entraînement.
                  {trialSessionsUsed > 0 && ` (${trialSessionsUsed}/${trialSessionsMax} sessions utilisées)`}
                </span>
                <Link href="/features">
                  <Button size="sm" className="bg-yellow-500 hover:bg-yellow-600 text-black ml-4">
                    <Crown className="h-4 w-4 mr-1" />
                    Passer à Pro
                  </Button>
                </Link>
              </AlertDescription>
            </Alert>
          </motion.div>
        )}

        {/* Onboarding for Free Users with no activity */}
        {isFreeUser && sessions.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mb-8"
          >
            <Card className="glass border-primary-500/30 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-secondary-500/5" />
              <CardContent className="relative py-8">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2">Bienvenue sur Champion Clone !</h2>
                  <p className="text-muted-foreground">Commencez votre parcours vers l&apos;excellence commerciale</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                  <Link href="/learn" className="block">
                    <Card className="glass border-white/10 hover:border-primary-500/50 transition-all h-full">
                      <CardContent className="p-6 text-center">
                        <div className="inline-flex p-3 rounded-xl bg-blue-500/20 mb-4">
                          <BookOpen className="h-6 w-6 text-blue-400" />
                        </div>
                        <h3 className="font-semibold mb-1">1. Apprenez</h3>
                        <p className="text-sm text-muted-foreground">
                          Suivez votre premier cours
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                  <Link href="/learn" className="block">
                    <Card className="glass border-white/10 hover:border-primary-500/50 transition-all h-full">
                      <CardContent className="p-6 text-center">
                        <div className="inline-flex p-3 rounded-xl bg-green-500/20 mb-4">
                          <Target className="h-6 w-6 text-green-400" />
                        </div>
                        <h3 className="font-semibold mb-1">2. Validez</h3>
                        <p className="text-sm text-muted-foreground">
                          Passez votre premier quiz
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                  <Link href="/training" className="block">
                    <Card className="glass border-white/10 hover:border-primary-500/50 transition-all h-full">
                      <CardContent className="p-6 text-center">
                        <div className="inline-flex p-3 rounded-xl bg-purple-500/20 mb-4">
                          <Sparkles className="h-6 w-6 text-purple-400" />
                        </div>
                        <h3 className="font-semibold mb-1">3. Pratiquez</h3>
                        <p className="text-sm text-muted-foreground">
                          Entraînez-vous avec l&apos;IA
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Stats Grid - Show only if has activity or is premium */}
        {(!isFreeUser || sessions.length > 0) && (
          <div className="mb-8">
            <StatsGrid stats={stats} />
          </div>
        )}

        {/* Skills Progress Section */}
        {skillsProgress && skillsProgress.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Progression des compétences</h2>
              <Link href="/learn">
                <Button variant="outline" size="sm" className="border-white/20">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Voir les cours
                </Button>
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skillsProgress.filter((sp: any) => sp.quiz_passed || sp.scenarios_completed > 0).map((skill: any, index: number) => (
                <motion.div
                  key={skill.skill_slug}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * index }}
                >
                  <Card className="glass border-white/10">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium">{skill.skill_name}</h3>
                        {skill.is_validated ? (
                          <Badge className="bg-green-500/20 text-green-400">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Validé
                          </Badge>
                        ) : skill.quiz_passed ? (
                          <Badge className="bg-blue-500/20 text-blue-400">
                            Quiz réussi
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-muted-foreground">
                            En cours
                          </Badge>
                        )}
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Quiz</span>
                          <span className={skill.quiz_passed ? "text-green-400" : "text-muted-foreground"}>
                            {skill.quiz_passed ? (
                              <span className="flex items-center gap-1">
                                <CheckCircle2 className="h-4 w-4" />
                                Réussi
                              </span>
                            ) : (
                              <span className="flex items-center gap-1">
                                <XCircle className="h-4 w-4" />
                                Non passé
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Scénarios</span>
                          <span>{skill.scenarios_passed}/{skill.scenarios_required}</span>
                        </div>
                        {skill.best_score > 0 && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Meilleur score</span>
                            <span className="text-primary-400">{Math.round(skill.best_score)}%</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Champions Section - Only for enterprise users */}
        {isEnterpriseUser && champions.length > 0 && (
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

        {/* Empty state for champions - Only for enterprise users */}
        {isEnterpriseUser && champions.length === 0 && (
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

        {/* Charts Row - Show only if has activity or is premium */}
        {(!isFreeUser || sessions.length > 0) && (
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
        )}

        {/* Sessions Table - Show only if has activity or is premium */}
        {(!isFreeUser || sessions.length > 0) && (
          <SessionsTable
            sessions={sessionHistory}
            onViewSession={(id) => console.log("View session", id)}
          />
        )}
      </div>
    </div>
  );
}
