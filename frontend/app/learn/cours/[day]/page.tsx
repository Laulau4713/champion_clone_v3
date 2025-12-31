"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Clock,
  CheckCircle2,
  Lightbulb,
  AlertTriangle,
  MessageSquare,
  Sparkles,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { learningAPI, authAPI } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { User, Cours } from "@/types";

const levelConfig = {
  easy: { label: "Facile", color: "bg-green-500/20 text-green-400" },
  medium: { label: "Moyen", color: "bg-yellow-500/20 text-yellow-400" },
  expert: { label: "Expert", color: "bg-red-500/20 text-red-400" },
};

export default function CoursePage() {
  const params = useParams();
  const router = useRouter();
  const day = Number(params.day);

  const [course, setCourse] = useState<Cours | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState(0);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);

  const isFreeUser = user?.subscription_plan === "free";
  const isLocked = isFreeUser && day > 1;

  useEffect(() => {
    loadCourse();
    loadUser();
  }, [day]);

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

  const loadCourse = async () => {
    try {
      setLoading(true);
      const res = await learningAPI.getCourseByDay(day);
      setCourse(res.data);
    } catch (err) {
      setError("Cours non trouvé");
    } finally {
      setLoading(false);
    }
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
                Ce cours est réservé aux abonnés Pro et Entreprise.
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

  if (error || !course) {
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

  const config = levelConfig[course.level as keyof typeof levelConfig] || levelConfig.easy;
  const keyPoints = course.key_points || [];
  const commonMistakes = course.common_mistakes || [];
  const emotionalTips = course.emotional_tips || [];
  const takeaways = course.takeaways || [];

  const sections = [
    { id: "intro", label: "Introduction" },
    ...keyPoints.map((kp, i) => ({ id: `point-${i}`, label: kp.title })),
    { id: "mistakes", label: "Erreurs courantes" },
    { id: "tips", label: "Conseils" },
    { id: "summary", label: "Résumé" },
  ];

  const progress = ((currentSection + 1) / sections.length) * 100;

  const handleNext = () => {
    if (currentSection < sections.length - 1) {
      setCurrentSection(currentSection + 1);
    }
  };

  const handlePrev = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1);
    }
  };

  const handleComplete = () => {
    router.push("/learn");
  };

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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

          <div className="flex items-center gap-3 mb-4">
            <Badge variant="outline">Jour {course.day}</Badge>
            <Badge className={config.color}>{config.label}</Badge>
            <span className="flex items-center text-sm text-muted-foreground">
              <Clock className="h-4 w-4 mr-1" />
              {course.duration_minutes} min
            </span>
          </div>

          <h1 className="text-3xl font-bold mb-2">{course.title}</h1>
          <p className="text-muted-foreground">{course.objective}</p>
        </motion.div>

        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-muted-foreground mb-2">
            <span>{sections[currentSection].label}</span>
            <span>{currentSection + 1} / {sections.length}</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Content */}
        <motion.div
          key={currentSection}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Introduction */}
          {currentSection === 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-primary-400" />
                  Introduction
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-lg">{course.objective}</p>
                <div className="p-4 rounded-lg bg-primary-500/10 border border-primary-500/20">
                  <h4 className="font-semibold mb-2">Ce que vous allez apprendre :</h4>
                  <ul className="space-y-2">
                    {keyPoints.map((kp, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle2 className="h-5 w-5 text-primary-400 mt-0.5 shrink-0" />
                        <span>{kp.title}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Key Points */}
          {currentSection > 0 && currentSection <= keyPoints.length && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-400" />
                  {keyPoints[currentSection - 1].title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-lg leading-relaxed">
                  {keyPoints[currentSection - 1].summary}
                </p>

                {keyPoints[currentSection - 1].example_dialogue && (
                  <div className="space-y-4">
                    <h4 className="font-semibold flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Exemple de dialogue
                    </h4>
                    <p className="text-sm text-muted-foreground italic">
                      {keyPoints[currentSection - 1].example_dialogue?.context}
                    </p>

                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                      <p className="text-sm font-medium text-red-400 mb-1">Ce qu&apos;il ne faut PAS faire :</p>
                      <p className="text-sm">{keyPoints[currentSection - 1].example_dialogue?.bad}</p>
                    </div>

                    <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                      <p className="text-sm font-medium text-green-400 mb-1">Ce qu&apos;il faut faire :</p>
                      <p className="text-sm">{keyPoints[currentSection - 1].example_dialogue?.good}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Common Mistakes */}
          {currentSection === keyPoints.length + 1 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-400" />
                  Erreurs courantes à éviter
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4">
                  {commonMistakes.map((mistake, i) => (
                    <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-orange-500/10">
                      <span className="text-orange-400 font-bold">{i + 1}.</span>
                      <span>{mistake}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Emotional Tips */}
          {currentSection === keyPoints.length + 2 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-400" />
                  Conseils pour gérer vos émotions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4">
                  {emotionalTips.map((tip, i) => (
                    <li key={i} className="flex items-start gap-3 p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                      <Lightbulb className="h-5 w-5 text-purple-400 shrink-0 mt-0.5" />
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Summary */}
          {currentSection === sections.length - 1 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-400" />
                  Ce qu&apos;il faut retenir
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  {takeaways.map((takeaway, i) => (
                    <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                      <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                      <span>{takeaway}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-6 text-center">
                  <p className="text-muted-foreground mb-4">
                    Vous avez terminé ce cours ! Prêt à passer au quiz ?
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={handlePrev}
            disabled={currentSection === 0}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Précédent
          </Button>

          {currentSection < sections.length - 1 ? (
            <Button
              className="bg-gradient-primary hover:opacity-90 text-white"
              onClick={handleNext}
            >
              Suivant
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button
              className="bg-gradient-primary hover:opacity-90 text-white"
              onClick={handleComplete}
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Terminer
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
