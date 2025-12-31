"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Play,
  Trophy,
  Clock,
  CheckCircle2,
  Lock,
  Mic,
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

const difficultyConfig: Record<DifficultyLevel, { label: string; color: string; description: string }> = {
  easy: {
    label: "Facile",
    color: "bg-green-500/20 text-green-400 border-green-500/30",
    description: "Jauge visible, indices activés, prospect bienveillant",
  },
  medium: {
    label: "Moyen",
    color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    description: "Objections cachées, événements situationnels",
  },
  expert: {
    label: "Expert",
    color: "bg-red-500/20 text-red-400 border-red-500/30",
    description: "Jauge cachée, reversals, prospect agressif",
  },
};

interface UserProgressData {
  current_day: number;
  skills_validated: number;
  skills_total: number;
}

export default function LearnPage() {
  const router = useRouter();
  const [cours, setCours] = useState<Cours[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [progress, setProgress] = useState<UserProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<DifficultyLevel>("easy");
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

  const startVoiceTraining = (level: DifficultyLevel) => {
    router.push(`/training/setup?level=${level}`);
  };

  const progressPercentage = progress && progress.skills_total > 0
    ? (progress.skills_validated / progress.skills_total) * 100
    : 0;

  const currentDay = progress?.current_day || 1;

  // Trial users (free plan) have limited access
  const isFreeUser = user?.subscription_plan === "free";
  const TRIAL_MAX_COURSE_DAY = 1; // Only day 1 course accessible
  const TRIAL_MAX_QUIZ_INDEX = 0; // Only first quiz accessible

  const canAccessCourse = (day: number) => {
    if (!isFreeUser) return true;
    return day <= TRIAL_MAX_COURSE_DAY;
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
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold gradient-text">
              Parcours d&apos;Apprentissage
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
            Maîtrisez les techniques de vente avec nos cours et entraînements vocaux
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
        <Tabs defaultValue="training" className="space-y-6">
          <TabsList className="glass">
            <TabsTrigger value="training" className="gap-2">
              <Mic className="h-4 w-4" />
              Entraînement Vocal
            </TabsTrigger>
            <TabsTrigger value="courses" className="gap-2">
              <BookOpen className="h-4 w-4" />
              Cours
            </TabsTrigger>
            <TabsTrigger value="quiz" className="gap-2">
              <Target className="h-4 w-4" />
              Quiz
            </TabsTrigger>
          </TabsList>

          {/* Voice Training Tab */}
          <TabsContent value="training">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              <h3 className="text-xl font-semibold">Choisissez votre niveau</h3>

              <div className="grid gap-4 md:grid-cols-3">
                {(["easy", "medium", "expert"] as DifficultyLevel[]).map((level) => {
                  const config = difficultyConfig[level];
                  const isSelected = selectedLevel === level;

                  return (
                    <motion.div
                      key={level}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card
                        className={cn(
                          "cursor-pointer transition-all border-2",
                          isSelected
                            ? "border-primary-500 bg-primary-500/10"
                            : "border-transparent hover:border-white/10"
                        )}
                        onClick={() => setSelectedLevel(level)}
                      >
                        <CardHeader>
                          <Badge className={cn("w-fit", config.color)}>
                            {config.label}
                          </Badge>
                          <CardTitle className="mt-2">
                            Niveau {config.label}
                          </CardTitle>
                          <CardDescription>
                            {config.description}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm text-muted-foreground">
                            {level === "easy" && (
                              <>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                                  Jauge émotionnelle visible
                                </li>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                                  Indices et conseils
                                </li>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                                  Prospect réceptif
                                </li>
                              </>
                            )}
                            {level === "medium" && (
                              <>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-yellow-400" />
                                  Objections cachées
                                </li>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-yellow-400" />
                                  Événements imprévus
                                </li>
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-yellow-400" />
                                  Indices limités
                                </li>
                              </>
                            )}
                            {level === "expert" && (
                              <>
                                <li className="flex items-center gap-2">
                                  <Lock className="h-4 w-4 text-red-400" />
                                  Jauge cachée
                                </li>
                                <li className="flex items-center gap-2">
                                  <Lock className="h-4 w-4 text-red-400" />
                                  Reversals de dernière minute
                                </li>
                                <li className="flex items-center gap-2">
                                  <Lock className="h-4 w-4 text-red-400" />
                                  Aucun indice
                                </li>
                              </>
                            )}
                          </ul>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>

              <div className="flex justify-center pt-4">
                <Button
                  onClick={() => startVoiceTraining(selectedLevel)}
                  size="lg"
                  className="bg-gradient-primary hover:opacity-90 text-white gap-2"
                >
                  <Play className="h-5 w-5" />
                  Démarrer l&apos;entraînement {difficultyConfig[selectedLevel].label}
                </Button>
              </div>
            </motion.div>
          </TabsContent>

          {/* Courses Tab */}
          <TabsContent value="courses">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              {cours.map((course, index) => {
                const isCompleted = course.day < currentDay;
                const levelConfig = difficultyConfig[course.level];
                const isLocked = !canAccessCourse(course.day);

                return (
                  <motion.div
                    key={course.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className={cn(
                      "h-full transition-colors",
                      isLocked ? "opacity-60" : "hover:border-primary-500/30"
                    )}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">Jour {course.day}</Badge>
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
                        <CardDescription>{course.objective}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Clock className="h-4 w-4 mr-1" />
                          {course.duration_minutes} min
                        </div>
                        {isLocked ? (
                          <Button
                            className="w-full mt-4"
                            variant="outline"
                            onClick={handleLockedContent}
                          >
                            <Lock className="h-4 w-4 mr-2" />
                            Premium requis
                          </Button>
                        ) : (
                          <Button
                            className="w-full mt-4"
                            variant={isCompleted ? "outline" : "default"}
                            onClick={() => router.push(`/learn/cours/${course.day}`)}
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
                      "h-full transition-colors",
                      isLocked ? "opacity-60" : "hover:border-primary-500/30"
                    )}>
                      <CardHeader>
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
                      <CardContent>
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
