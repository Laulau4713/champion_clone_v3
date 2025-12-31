"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Play,
  Target,
  BookOpen,
  Briefcase,
  Sparkles,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { learningAPI, authAPI } from "@/lib/api";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { Skill, DifficultyLevel, User } from "@/types";

interface Sector {
  id: number;
  slug: string;
  name: string;
  description: string;
  icon?: string;
}

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

export default function TrainingSetupPage() {
  const router = useRouter();

  const [step, setStep] = useState<"skill" | "level" | "sector" | "ready">("skill");
  const [skills, setSkills] = useState<Skill[]>([]);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<DifficultyLevel>("easy");
  const [selectedSector, setSelectedSector] = useState<Sector | null>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);

  const isFreeUser = user?.subscription_plan === "free";
  const trialSessionsUsed = user?.trial_sessions_used || 0;
  const trialSessionsMax = user?.trial_sessions_max || 3;
  const canStartSession = !isFreeUser || trialSessionsUsed < trialSessionsMax;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [skillsRes, sectorsRes, userRes] = await Promise.all([
        learningAPI.getSkills(),
        learningAPI.getSectors().catch(() => ({ data: [] })),
        authAPI.me().catch(() => ({ data: null })),
      ]);
      setSkills(skillsRes.data || []);
      setSectors(sectorsRes.data || []);
      if (userRes.data) {
        setUser(userRes.data);
      }
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSkill = (skill: Skill) => {
    // Free users can only access first skill
    if (isFreeUser && skills.indexOf(skill) > 0) {
      setShowPremiumModal(true);
      return;
    }
    setSelectedSkill(skill);
    setSelectedLevel(skill.level);
    setStep("level");
  };

  const handleSelectLevel = (level: DifficultyLevel) => {
    setSelectedLevel(level);
    if (level === "expert") {
      setStep("sector");
    } else {
      setStep("ready");
    }
  };

  const handleSelectSector = (sector: Sector) => {
    setSelectedSector(sector);
    setStep("ready");
  };

  const handleStartTraining = () => {
    if (!canStartSession) {
      setShowPremiumModal(true);
      return;
    }

    const params = new URLSearchParams();
    params.set("level", selectedLevel);
    if (selectedSkill) {
      params.set("skill", selectedSkill.slug);
    }
    if (selectedSector) {
      params.set("sector", selectedSector.slug);
    }

    router.push(`/training/session/new?${params.toString()}`);
  };

  const handleBack = () => {
    if (step === "level") {
      setStep("skill");
    } else if (step === "sector") {
      setStep("level");
    } else if (step === "ready") {
      if (selectedLevel === "expert") {
        setStep("sector");
      } else {
        setStep("level");
      }
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

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          {step !== "skill" && (
            <Button variant="ghost" className="mb-4" onClick={handleBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
          )}
          <h1 className="text-3xl font-bold gradient-text mb-2">
            Configurer votre session
          </h1>
          <p className="text-muted-foreground">
            {step === "skill" && "Choisissez la compétence à travailler"}
            {step === "level" && "Sélectionnez le niveau de difficulté"}
            {step === "sector" && "Choisissez votre secteur d'activité"}
            {step === "ready" && "Tout est prêt !"}
          </p>
        </motion.div>

        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {["skill", "level", "sector", "ready"].map((s, i) => {
            const isCurrent = s === step;
            const isPast = ["skill", "level", "sector", "ready"].indexOf(step) > i;
            const isHidden = s === "sector" && selectedLevel !== "expert";

            if (isHidden) return null;

            return (
              <div
                key={s}
                className={cn(
                  "w-3 h-3 rounded-full transition-all",
                  isCurrent
                    ? "bg-primary-500 w-8"
                    : isPast
                    ? "bg-primary-500"
                    : "bg-white/20"
                )}
              />
            );
          })}
        </div>

        {/* Step: Select Skill */}
        {step === "skill" && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          >
            {skills.map((skill, index) => {
              const isLocked = isFreeUser && index > 0;
              const levelConfig = difficultyConfig[skill.level];

              return (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      "cursor-pointer transition-all h-full",
                      isLocked
                        ? "opacity-60"
                        : "hover:border-primary-500/50"
                    )}
                    onClick={() => handleSelectSkill(skill)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge className={levelConfig.color}>
                          {levelConfig.label}
                        </Badge>
                        {isLocked && <Lock className="h-4 w-4 text-yellow-500" />}
                      </div>
                      <CardTitle className="text-lg">{skill.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="line-clamp-2">
                        {skill.description}
                      </CardDescription>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* Step: Select Level */}
        {step === "level" && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="grid gap-4 md:grid-cols-3"
          >
            {(["easy", "medium", "expert"] as DifficultyLevel[]).map((level) => {
              const config = difficultyConfig[level];
              const isSelected = selectedLevel === level;
              const isRecommended = selectedSkill?.level === level;

              return (
                <Card
                  key={level}
                  className={cn(
                    "cursor-pointer transition-all",
                    isSelected
                      ? "border-primary-500 bg-primary-500/10"
                      : "hover:border-white/20"
                  )}
                  onClick={() => handleSelectLevel(level)}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <Badge className={config.color}>{config.label}</Badge>
                      {isRecommended && (
                        <Badge variant="outline" className="text-primary-400 border-primary-500/50">
                          Recommandé
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg mt-2">
                      Niveau {config.label}
                    </CardTitle>
                    <CardDescription>{config.description}</CardDescription>
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
                            Indices et conseils activés
                          </li>
                        </>
                      )}
                      {level === "medium" && (
                        <>
                          <li className="flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4 text-yellow-400" />
                            Objections imprévues
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
                            Secteur spécifique requis
                          </li>
                        </>
                      )}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </motion.div>
        )}

        {/* Step: Select Sector (Expert only) */}
        {step === "sector" && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          >
            {sectors.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Briefcase className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">Aucun secteur disponible</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => setStep("ready")}
                >
                  Continuer sans secteur
                </Button>
              </div>
            ) : (
              sectors.map((sector, index) => (
                <motion.div
                  key={sector.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      "cursor-pointer transition-all h-full",
                      selectedSector?.id === sector.id
                        ? "border-primary-500 bg-primary-500/10"
                        : "hover:border-white/20"
                    )}
                    onClick={() => handleSelectSector(sector)}
                  >
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <Briefcase className="h-5 w-5 text-primary-400" />
                        <CardTitle className="text-lg">{sector.name}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{sector.description}</CardDescription>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* Step: Ready */}
        {step === "ready" && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Card className="glass">
              <CardContent className="py-8">
                <div className="text-center mb-8">
                  <div className="inline-flex p-4 rounded-full bg-primary-500/20 mb-4">
                    <Target className="h-8 w-8 text-primary-400" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">Configuration terminée</h2>
                  <p className="text-muted-foreground">
                    Voici le récapitulatif de votre session
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3 mb-8">
                  <div className="p-4 rounded-lg bg-white/5 text-center">
                    <BookOpen className="h-6 w-6 mx-auto mb-2 text-blue-400" />
                    <p className="text-sm text-muted-foreground">Compétence</p>
                    <p className="font-semibold">{selectedSkill?.name || "Général"}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 text-center">
                    <Target className="h-6 w-6 mx-auto mb-2 text-yellow-400" />
                    <p className="text-sm text-muted-foreground">Niveau</p>
                    <p className="font-semibold">{difficultyConfig[selectedLevel].label}</p>
                  </div>
                  {selectedSector && (
                    <div className="p-4 rounded-lg bg-white/5 text-center">
                      <Briefcase className="h-6 w-6 mx-auto mb-2 text-purple-400" />
                      <p className="text-sm text-muted-foreground">Secteur</p>
                      <p className="font-semibold">{selectedSector.name}</p>
                    </div>
                  )}
                </div>

                {isFreeUser && (
                  <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 mb-6 text-center">
                    <p className="text-sm text-yellow-200">
                      <strong>Essai gratuit</strong> — {trialSessionsUsed}/{trialSessionsMax} sessions utilisées
                    </p>
                  </div>
                )}

                <div className="flex justify-center">
                  <Button
                    size="lg"
                    className="bg-gradient-primary hover:opacity-90 text-white px-12"
                    onClick={handleStartTraining}
                    disabled={!canStartSession}
                  >
                    <Play className="h-5 w-5 mr-2" />
                    Lancer la session
                  </Button>
                </div>

                {!canStartSession && (
                  <p className="text-center text-sm text-yellow-400 mt-4">
                    Vous avez atteint la limite de sessions gratuites.{" "}
                    <button
                      className="underline hover:no-underline"
                      onClick={() => setShowPremiumModal(true)}
                    >
                      Passez à Pro
                    </button>
                  </p>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      <PremiumModal open={showPremiumModal} onOpenChange={setShowPremiumModal} />
    </div>
  );
}
