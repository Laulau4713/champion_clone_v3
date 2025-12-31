"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Trophy,
  RotateCcw,
  Sparkles,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { learningAPI, authAPI } from "@/lib/api";
import { PremiumModal } from "@/components/ui/premium-modal";
import { cn } from "@/lib/utils";
import type { User, Quiz, QuizResult } from "@/types";

export default function QuizPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [skillIndex, setSkillIndex] = useState<number>(0);

  const isFreeUser = user?.subscription_plan === "free";
  const isLocked = isFreeUser && skillIndex > 0;

  useEffect(() => {
    loadQuiz();
    loadUser();
    loadSkillIndex();
  }, [slug]);

  const loadUser = async () => {
    try {
      const res = await authAPI.me();
      if (res.data) {
        setUser(res.data);
      }
    } catch {
      // Not logged in
    }
  };

  const loadSkillIndex = async () => {
    try {
      const res = await learningAPI.getSkills();
      const skills = res.data || [];
      const index = skills.findIndex((s) => s.slug === slug);
      setSkillIndex(index >= 0 ? index : 0);
    } catch {
      // Ignore
    }
  };

  const loadQuiz = async () => {
    try {
      setLoading(true);
      const res = await learningAPI.getQuizBySkill(slug);
      setQuiz(res.data);
      setAnswers(new Array(res.data.questions.length).fill(""));
    } catch {
      setError("Quiz non trouvé");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAnswer = (answer: string) => {
    setSelectedAnswer(answer);
  };

  const handleNextQuestion = () => {
    if (selectedAnswer) {
      const newAnswers = [...answers];
      newAnswers[currentQuestion] = selectedAnswer;
      setAnswers(newAnswers);
      setSelectedAnswer(null);

      if (currentQuestion < (quiz?.questions.length || 0) - 1) {
        setCurrentQuestion(currentQuestion + 1);
      }
    }
  };

  const handlePrevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setSelectedAnswer(answers[currentQuestion - 1] || null);
    }
  };

  const handleSubmit = async () => {
    if (!quiz) return;

    const finalAnswers = [...answers];
    if (selectedAnswer) {
      finalAnswers[currentQuestion] = selectedAnswer;
    }

    // Check all questions answered
    if (finalAnswers.some((a) => !a)) {
      setError("Veuillez répondre à toutes les questions");
      return;
    }

    setSubmitting(true);
    try {
      const res = await learningAPI.submitQuiz(slug, finalAnswers);
      setResult(res.data);
    } catch {
      setError("Erreur lors de la soumission");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setResult(null);
    setCurrentQuestion(0);
    setAnswers(new Array(quiz?.questions.length || 0).fill(""));
    setSelectedAnswer(null);
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

  if (isLocked) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4">
          <Card className="glass border-yellow-500/30">
            <CardContent className="py-12 text-center">
              <div className="inline-flex p-4 rounded-full bg-yellow-500/20 mb-6">
                <Lock className="h-8 w-8 text-yellow-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Contenu Premium</h2>
              <p className="text-muted-foreground mb-6">
                Ce quiz est réservé aux abonnés Pro et Entreprise.
              </p>
              <div className="flex gap-4 justify-center">
                <Button variant="outline" onClick={() => router.back()}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Retour
                </Button>
                <Button
                  className="bg-gradient-primary hover:opacity-90 text-white"
                  onClick={() => setShowPremiumModal(true)}
                >
                  Passer à Pro
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        <PremiumModal open={showPremiumModal} onOpenChange={setShowPremiumModal} />
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">{error}</h1>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
        </div>
      </div>
    );
  }

  // Show results
  if (result) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <Card className="glass">
              <CardHeader className="text-center">
                <div
                  className={cn(
                    "inline-flex p-4 rounded-full mx-auto mb-4",
                    result.passed ? "bg-green-500/20" : "bg-red-500/20"
                  )}
                >
                  {result.passed ? (
                    <Trophy className="h-12 w-12 text-green-400" />
                  ) : (
                    <XCircle className="h-12 w-12 text-red-400" />
                  )}
                </div>
                <CardTitle className="text-2xl">
                  {result.passed ? "Bravo !" : "Pas encore..."}
                </CardTitle>
                <p className="text-muted-foreground">
                  {result.passed
                    ? "Vous avez réussi ce quiz !"
                    : "Continuez à vous entraîner !"}
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="text-center">
                  <div className="text-5xl font-bold mb-2">
                    {Math.round(result.score)}%
                  </div>
                  <p className="text-muted-foreground">
                    {result.correct_count} / {result.total_questions} bonnes réponses
                  </p>
                  <Badge
                    className={cn(
                      "mt-2",
                      result.passed
                        ? "bg-green-500/20 text-green-400"
                        : "bg-red-500/20 text-red-400"
                    )}
                  >
                    {result.passed ? "Réussi" : "80% requis pour valider"}
                  </Badge>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold">Détail des réponses :</h3>
                  {result.details.map((detail, i) => (
                    <div
                      key={i}
                      className={cn(
                        "p-4 rounded-lg border",
                        detail.is_correct
                          ? "bg-green-500/10 border-green-500/20"
                          : "bg-red-500/10 border-red-500/20"
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {detail.is_correct ? (
                          <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                        )}
                        <div>
                          <p className="font-medium mb-1">
                            Question {i + 1}
                          </p>
                          {!detail.is_correct && (
                            <p className="text-sm text-muted-foreground mb-2">
                              Votre réponse : {detail.your_answer} | Bonne réponse : {detail.correct_answer}
                            </p>
                          )}
                          <p className="text-sm">{detail.explanation}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-4 justify-center pt-4">
                  {!result.passed && (
                    <Button variant="outline" onClick={handleRetry}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Réessayer
                    </Button>
                  )}
                  <Button
                    className="bg-gradient-primary hover:opacity-90 text-white"
                    onClick={() => router.push("/learn")}
                  >
                    Retour aux cours
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;
  const isLastQuestion = currentQuestion === quiz.questions.length - 1;
  const currentAnswerSelected = selectedAnswer || answers[currentQuestion];

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Button
            variant="ghost"
            className="mb-4"
            onClick={() => router.push("/learn")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour aux cours
          </Button>

          <h1 className="text-2xl font-bold mb-2">Quiz</h1>

          <div className="flex justify-between text-sm text-muted-foreground mb-2">
            <span>Question {currentQuestion + 1} sur {quiz.questions.length}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </motion.div>

        {/* Question */}
        <motion.div
          key={currentQuestion}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-xl leading-relaxed">
                {question.question}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {question.options.map((option, i) => {
                const letter = String.fromCharCode(65 + i); // A, B, C, D
                const isSelected = currentAnswerSelected === letter;

                return (
                  <button
                    key={i}
                    onClick={() => handleSelectAnswer(letter)}
                    className={cn(
                      "w-full p-4 rounded-lg text-left transition-all border",
                      isSelected
                        ? "bg-primary-500/20 border-primary-500"
                        : "bg-white/5 border-white/10 hover:border-white/20"
                    )}
                  >
                    <span className="font-medium">{option}</span>
                  </button>
                );
              })}
            </CardContent>
          </Card>
        </motion.div>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={handlePrevQuestion}
            disabled={currentQuestion === 0}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Précédent
          </Button>

          {isLastQuestion ? (
            <Button
              className="bg-gradient-primary hover:opacity-90 text-white"
              onClick={handleSubmit}
              disabled={!currentAnswerSelected || submitting}
            >
              {submitting ? (
                <Sparkles className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Valider le quiz
            </Button>
          ) : (
            <Button
              className="bg-gradient-primary hover:opacity-90 text-white"
              onClick={handleNextQuestion}
              disabled={!currentAnswerSelected}
            >
              Suivant
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
