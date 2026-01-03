"use client";

import { useState, useEffect, Suspense } from "react";
import { motion } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import {
  BookOpen,
  Trophy,
  Clock,
  CheckCircle2,
  Lock,
  Target,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { learningAPI, authAPI } from "@/lib/api";
import { TrialBadge } from "@/components/ui/trial-badge";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { Cours, Skill, DifficultyLevel, User } from "@/types";

const difficultyConfig: Record<DifficultyLevel, { label: string; color: string }> = {
  easy: {
    label: "Facile",
    color: "bg-green-500/20 text-green-400 border-green-500/30",
  },
  medium: {
    label: "Moyen",
    color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  },
  expert: {
    label: "Expert",
    color: "bg-red-500/20 text-red-400 border-red-500/30",
  },
};

interface UserProgressData {
  current_course: number;
  skills_validated: number;
  skills_total: number;
}

function LearnPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") || "courses";

  const [cours, setCours] = useState<Cours[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [progress, setProgress] = useState<UserProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      const [coursRes, skillsRes, progressRes, userRes] = await Promise.all([
        learningAPI.getCourses(),
        learningAPI.getSkills(),
        learningAPI.getProgress().catch(() => ({ data: null })),
        authAPI.me().catch(() => ({ data: null })),
      ]);

      setCours(coursRes.data || []);
      setSkills(skillsRes.data || []);
      if (progressRes.data) {
        setProgress(progressRes.data as unknown as UserProgressData);
      }
      if (userRes.data) {
        setUser(userRes.data);
      }
    } catch (error) {
      console.error("Error loading content:", error);
    } finally {
      setLoading(false);
    }
  };

  const progressPercentage = progress && progress.skills_total > 0
    ? (progress.skills_validated / progress.skills_total) * 100
    : 0;

  const currentCourse = progress?.current_course || 1;

  // Trial users (free plan) have limited access
  const isFreeUser = user?.subscription_plan === "free";
  const TRIAL_MAX_COURSE_ORDER = 1;
  const TRIAL_MAX_QUIZ_INDEX = 0;

  const canAccessCourse = (order: number) => {
    if (!isFreeUser) return true;
    return order <= TRIAL_MAX_COURSE_ORDER;
  };

  const canAccessQuiz = (index: number) => {
    if (!isFreeUser) return true;
    return index <= TRIAL_MAX_QUIZ_INDEX;
  };

  const handleLockedContent = () => {
    setShowPremiumModal(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        >
          <Sparkles className="h-8 w-8 text-primary-400" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-dark pt-8 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold gradient-text">
              Apprendre
            </h1>
            {user && (
              <TrialBadge
                sessionsUsed={user.trial_sessions_used}
                sessionsMax={user.trial_sessions_max}
                isPremium={user.subscription_plan !== "free"}
              />
            )}
          </div>
          <p className="text-muted-foreground">
            Cours et quiz pour maîtriser les techniques de vente
          </p>
        </motion.div>

        {/* Progress Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary-500/20">
                <Trophy className="h-6 w-6 text-primary-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Votre Progression</h2>
                <p className="text-sm text-muted-foreground">
                  {progress?.skills_validated || 0} / {progress?.skills_total || skills.length} compétences validées
                </p>
              </div>
            </div>
            <span className="text-2xl font-bold text-primary-400">
              {Math.round(progressPercentage)}%
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </motion.div>

        {/* Main Content Tabs */}
        <Tabs defaultValue={initialTab} className="space-y-6">
          <TabsList className="glass">
            <TabsTrigger value="courses" className="gap-2">
              <BookOpen className="h-4 w-4" />
              Cours
            </TabsTrigger>
            <TabsTrigger value="quiz" className="gap-2">
              <Target className="h-4 w-4" />
              Quiz
            </TabsTrigger>
          </TabsList>

          {/* Courses Tab */}
          <TabsContent value="courses">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              {cours.map((course, index) => {
                const courseOrder = course.order ?? course.day ?? index + 1;
                const isCompleted = courseOrder < currentCourse;
                const levelConfig = difficultyConfig[course.level];
                const isLocked = !canAccessCourse(courseOrder);

                return (
                  <motion.div
                    key={course.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className={cn(
                      "h-full flex flex-col transition-colors",
                      isLocked ? "opacity-60" : "hover:border-primary-500/30"
                    )}>
                      <CardHeader className="flex-1">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="bg-slate-800/50">
                              Module {courseOrder}
                            </Badge>
                            <Badge className={cn(levelConfig?.color || "bg-gray-500/20")}>
                              {levelConfig?.label || course.level}
                            </Badge>
                          </div>
                          {isLocked ? (
                            <Lock className="h-5 w-5 text-yellow-500" />
                          ) : isCompleted ? (
                            <CheckCircle2 className="h-5 w-5 text-green-400" />
                          ) : null}
                        </div>
                        <CardTitle className="text-lg mt-2">
                          {course.title}
                        </CardTitle>
                        <CardDescription className="line-clamp-2">{course.objective}</CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="flex items-center text-sm text-muted-foreground mb-4">
                          <Clock className="h-4 w-4 mr-1" />
                          {course.duration_minutes} min
                        </div>
                        {isLocked ? (
                          <Button
                            className="w-full"
                            variant="outline"
                            onClick={handleLockedContent}
                          >
                            <Lock className="h-4 w-4 mr-2" />
                            Premium requis
                          </Button>
                        ) : (
                          <Button
                            className="w-full"
                            variant={isCompleted ? "outline" : "default"}
                            onClick={() => router.push(`/learn/cours/${courseOrder}`)}
                          >
                            {isCompleted ? "Revoir" : "Commencer"}
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}

              {cours.length === 0 && (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun cours disponible pour le moment</p>
                </div>
              )}
            </motion.div>
          </TabsContent>

          {/* Quiz Tab */}
          <TabsContent value="quiz">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              {skills.map((skill, index) => {
                const levelConfig = difficultyConfig[skill.level];
                const isLocked = !canAccessQuiz(index);

                return (
                  <motion.div
                    key={skill.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className={cn(
                      "h-full flex flex-col transition-colors",
                      isLocked ? "opacity-60" : "hover:border-primary-500/30"
                    )}>
                      <CardHeader className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <Badge className={cn(levelConfig?.color || "bg-gray-500/20")}>
                            {levelConfig?.label || skill.level}
                          </Badge>
                          {isLocked && (
                            <Lock className="h-5 w-5 text-yellow-500" />
                          )}
                        </div>
                        <CardTitle className="text-lg">{skill.name}</CardTitle>
                        <CardDescription className="line-clamp-2">
                          {skill.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="text-sm text-muted-foreground mb-4">
                          Seuil de validation : {skill.pass_threshold}%
                        </div>
                        {isLocked ? (
                          <Button
                            className="w-full"
                            variant="outline"
                            onClick={handleLockedContent}
                          >
                            <Lock className="h-4 w-4 mr-2" />
                            Premium requis
                          </Button>
                        ) : (
                          <Button
                            className="w-full"
                            onClick={() => router.push(`/learn/quiz/${skill.slug}`)}
                          >
                            Passer le quiz
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}

              {skills.length === 0 && (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun quiz disponible pour le moment</p>
                </div>
              )}
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Premium Modal */}
      <PremiumModal
        open={showPremiumModal}
        onOpenChange={setShowPremiumModal}
      />
    </div>
  );
}

// Wrapper with Suspense for useSearchParams
export default function LearnPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
          >
            <Sparkles className="h-8 w-8 text-primary-400" />
          </motion.div>
        </div>
      }
    >
      <LearnPageContent />
    </Suspense>
  );
}
