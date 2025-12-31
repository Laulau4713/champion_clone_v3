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
import { learningAPI, voiceAPI } from "@/lib/api";
import type { Cours, Quiz, DifficultyLevel } from "@/types";

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

export default function LearnPage() {
  const router = useRouter();
  const [cours, setCours] = useState<Cours[]>([]);
  const [quiz, setQuiz] = useState<Quiz[]>([]);
  const [completedCourses, setCompletedCourses] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<DifficultyLevel>("easy");

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      const [coursRes, quizRes, progressRes] = await Promise.all([
        learningAPI.getCours(),
        learningAPI.getQuiz(),
        learningAPI.getProgress().catch(() => ({ data: { completed_courses: [] } })),
      ]);

      setCours(coursRes.data.cours || []);
      setQuiz(quizRes.data.quiz || []);
      setCompletedCourses(progressRes.data.completed_courses || []);
    } catch (error) {
      console.error("Error loading content:", error);
    } finally {
      setLoading(false);
    }
  };

  const startVoiceTraining = (level: DifficultyLevel) => {
    router.push(`/training/session/new?level=${level}`);
  };

  const progressPercentage = cours.length > 0
    ? (completedCourses.length / cours.length) * 100
    : 0;

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
          <h1 className="text-3xl font-bold gradient-text mb-2">
            Parcours d&apos;Apprentissage
          </h1>
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
                  {completedCourses.length} / {cours.length} cours complétés
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
                const isCompleted = completedCourses.includes(course.id);

                return (
                  <motion.div
                    key={course.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="h-full hover:border-primary-500/30 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <Badge
                            className={cn(
                              difficultyConfig[course.difficulty as DifficultyLevel]?.color ||
                              "bg-gray-500/20"
                            )}
                          >
                            {difficultyConfig[course.difficulty as DifficultyLevel]?.label ||
                              course.difficulty}
                          </Badge>
                          {isCompleted && (
                            <CheckCircle2 className="h-5 w-5 text-green-400" />
                          )}
                        </div>
                        <CardTitle className="text-lg mt-2">
                          {course.title}
                        </CardTitle>
                        <CardDescription>{course.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {course.duration_minutes} min
                          </div>
                          <Badge variant="outline">{course.category}</Badge>
                        </div>
                        <Button
                          className="w-full mt-4"
                          variant={isCompleted ? "outline" : "default"}
                          onClick={() => router.push(`/learn/cours/${course.id}`)}
                        >
                          {isCompleted ? "Revoir" : "Commencer"}
                        </Button>
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
              {quiz.map((q, index) => (
                <motion.div
                  key={q.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="h-full hover:border-primary-500/30 transition-colors">
                    <CardHeader>
                      <CardTitle className="text-lg">{q.title}</CardTitle>
                      <CardDescription>
                        {q.questions.length} questions
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button
                        className="w-full"
                        onClick={() => router.push(`/learn/quiz/${q.id}`)}
                      >
                        Passer le quiz
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}

              {quiz.length === 0 && (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun quiz disponible pour le moment</p>
                </div>
              )}
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
