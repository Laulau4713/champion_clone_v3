"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Mic,
  Target,
  Sparkles,
  Lock,
  CheckCircle2,
  Zap,
  Eye,
  EyeOff,
  Lightbulb,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { learningAPI, authAPI } from "@/lib/api";
import { TrialBadge } from "@/components/ui/trial-badge";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { Skill, DifficultyLevel, User } from "@/types";

const difficultyConfig: Record<DifficultyLevel, {
  label: string;
  color: string;
  bgColor: string;
  description: string;
  features: { icon: React.ReactNode; text: string }[];
}> = {
  easy: {
    label: "Facile",
    color: "text-green-400",
    bgColor: "bg-green-500/20 border-green-500/30",
    description: "Idéal pour débuter",
    features: [
      { icon: <Eye className="h-4 w-4" />, text: "Jauge visible" },
      { icon: <Lightbulb className="h-4 w-4" />, text: "Indices activés" },
      { icon: <CheckCircle2 className="h-4 w-4" />, text: "Prospect bienveillant" },
    ],
  },
  medium: {
    label: "Moyen",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/20 border-yellow-500/30",
    description: "Pour progresser",
    features: [
      { icon: <Eye className="h-4 w-4" />, text: "Jauge visible" },
      { icon: <AlertTriangle className="h-4 w-4" />, text: "Objections cachées" },
      { icon: <Zap className="h-4 w-4" />, text: "Événements imprévus" },
    ],
  },
  expert: {
    label: "Expert",
    color: "text-red-400",
    bgColor: "bg-red-500/20 border-red-500/30",
    description: "Le vrai défi",
    features: [
      { icon: <EyeOff className="h-4 w-4" />, text: "Jauge cachée" },
      { icon: <AlertTriangle className="h-4 w-4" />, text: "Reversals possibles" },
      { icon: <Lock className="h-4 w-4" />, text: "Aucun indice" },
    ],
  },
};

export default function TrainingPage() {
  const router = useRouter();

  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      const [skillsRes, userRes] = await Promise.all([
        learningAPI.getSkills(),
        authAPI.me().catch(() => ({ data: null })),
      ]);

      setSkills(skillsRes.data || []);
      if (userRes.data) {
        setUser(userRes.data);
      }
    } catch (error) {
      console.error("Error loading content:", error);
    } finally {
      setLoading(false);
    }
  };

  const isFreeUser = user?.subscription_plan === "free";

  const handleSkillClick = (skill: Skill, index: number) => {
    // Free users can only access first skill
    if (isFreeUser && index > 0) {
      setShowPremiumModal(true);
      return;
    }
    // Navigate to session with skill pre-selected
    router.push(`/training/session/new?skill=${skill.slug}`);
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
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary-500/20">
                <Mic className="h-6 w-6 text-primary-400" />
              </div>
              <h1 className="text-3xl font-bold gradient-text">
                Entraînement
              </h1>
            </div>
            {user && (
              <TrialBadge
                sessionsUsed={user.trial_sessions_used}
                sessionsMax={user.trial_sessions_max}
                isPremium={user.subscription_plan !== "free"}
              />
            )}
          </div>
          <p className="text-muted-foreground">
            Choisissez une compétence et entraînez-vous avec des simulations de vente
          </p>
        </motion.div>

        {/* Difficulty Levels Reminder */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold mb-4">Niveaux de difficulté</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {(["easy", "medium", "expert"] as DifficultyLevel[]).map((level, index) => {
              const config = difficultyConfig[level];
              return (
                <motion.div
                  key={level}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + index * 0.05 }}
                >
                  <Card className={cn("border", config.bgColor)}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge className={cn(config.bgColor, config.color)}>
                          {config.label}
                        </Badge>
                      </div>
                      <CardDescription className={config.color}>
                        {config.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <ul className="space-y-1">
                        {config.features.map((feature, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span className={config.color}>{feature.icon}</span>
                            {feature.text}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Skills List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-lg font-semibold mb-4">Compétences à travailler</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {skills.map((skill, index) => {
              const isLocked = isFreeUser && index > 0;

              return (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.03 }}
                >
                  <Card
                    className={cn(
                      "h-full flex flex-col cursor-pointer transition-all",
                      isLocked
                        ? "opacity-60"
                        : "hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/10"
                    )}
                    onClick={() => handleSkillClick(skill, index)}
                  >
                    <CardHeader className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <CardTitle className="text-lg">{skill.name}</CardTitle>
                        {isLocked && (
                          <Lock className="h-5 w-5 text-yellow-500" />
                        )}
                      </div>
                      <CardDescription className="line-clamp-2">
                        {skill.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          {skill.scenarios_required} scénarios requis
                        </span>
                        {isLocked ? (
                          <Button size="sm" variant="outline" onClick={(e) => {
                            e.stopPropagation();
                            setShowPremiumModal(true);
                          }}>
                            <Lock className="h-4 w-4 mr-1" />
                            Premium
                          </Button>
                        ) : (
                          <Button size="sm" className="bg-gradient-primary">
                            <Target className="h-4 w-4 mr-1" />
                            S&apos;entraîner
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}

            {skills.length === 0 && (
              <div className="col-span-full text-center py-12 text-muted-foreground">
                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Aucune compétence disponible pour le moment</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Premium Modal */}
      <PremiumModal
        open={showPremiumModal}
        onOpenChange={setShowPremiumModal}
      />
    </div>
  );
}
