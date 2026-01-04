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
  BookOpen,
  Package,
  GraduationCap,
  ArrowRight,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { trainingV3API, authAPI } from "@/lib/api";
import { TrialBadge } from "@/components/ui/trial-badge";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { PlaybookSummary, ModuleSummary, User } from "@/types";

// Configuration des modules avec icônes et couleurs
const moduleConfig: Record<string, {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}> = {
  bebedc: {
    icon: <Target className="h-5 w-5" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/20 border-blue-500/30",
  },
  spin_selling: {
    icon: <BookOpen className="h-5 w-5" />,
    color: "text-purple-400",
    bgColor: "bg-purple-500/20 border-purple-500/30",
  },
  closing: {
    icon: <CheckCircle2 className="h-5 w-5" />,
    color: "text-green-400",
    bgColor: "bg-green-500/20 border-green-500/30",
  },
  objection_handling: {
    icon: <GraduationCap className="h-5 w-5" />,
    color: "text-orange-400",
    bgColor: "bg-orange-500/20 border-orange-500/30",
  },
};

export default function TrainingPage() {
  const router = useRouter();

  const [playbooks, setPlaybooks] = useState<PlaybookSummary[]>([]);
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);

  // Sélection
  const [selectedPlaybook, setSelectedPlaybook] = useState<string | null>(null);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      const [playbooksRes, modulesRes, userRes] = await Promise.all([
        trainingV3API.getPlaybooks(),
        trainingV3API.getModules(),
        authAPI.me().catch(() => ({ data: null })),
      ]);

      setPlaybooks(playbooksRes.data || []);
      setModules(modulesRes.data || []);

      // Sélectionner le premier par défaut
      if (playbooksRes.data?.length) {
        setSelectedPlaybook(playbooksRes.data[0].id);
      }
      if (modulesRes.data?.length) {
        setSelectedModule(modulesRes.data[0].id);
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

  const isFreeUser = user?.subscription_plan === "free";
  const trialExpired = isFreeUser && (user?.trial_sessions_used ?? 0) >= (user?.trial_sessions_max ?? 3);

  const handleStartSession = async () => {
    if (!selectedPlaybook || !selectedModule) return;

    // Check trial
    if (trialExpired) {
      setShowPremiumModal(true);
      return;
    }

    setStarting(true);
    try {
      const response = await trainingV3API.startSession({
        playbook_id: selectedPlaybook,
        module_id: selectedModule,
      });

      if (response.data?.success) {
        // Store session data for the session page
        sessionStorage.setItem(
          `v3_session_${response.data.session_id}`,
          JSON.stringify(response.data)
        );
        // Navigate to session page with V3 session ID
        router.push(`/training/session/${response.data.session_id}`);
      }
    } catch (error: unknown) {
      console.error("Error starting session:", error);
      // Check if trial expired
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 402) {
          setShowPremiumModal(true);
        }
      }
    } finally {
      setStarting(false);
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

  const selectedPlaybookData = playbooks.find(p => p.id === selectedPlaybook);
  const selectedModuleData = modules.find(m => m.id === selectedModule);

  return (
    <div className="min-h-screen bg-gradient-dark pt-8 pb-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
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
                Entraînement V3
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
            Choisissez un produit et une méthode de vente pour commencer
          </p>
        </motion.div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Playbook Selection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center gap-2 mb-4">
              <Package className="h-5 w-5 text-primary-400" />
              <h2 className="text-lg font-semibold">1. Choisir le produit</h2>
            </div>
            <div className="space-y-3">
              {playbooks.map((playbook, index) => {
                const isSelected = selectedPlaybook === playbook.id;
                const isLocked = isFreeUser && index > 0;

                return (
                  <Card
                    key={playbook.id}
                    className={cn(
                      "cursor-pointer transition-all",
                      isSelected
                        ? "border-primary-500 bg-primary-500/10"
                        : "hover:border-primary-500/50",
                      isLocked && "opacity-60"
                    )}
                    onClick={() => !isLocked && setSelectedPlaybook(playbook.id)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          {isSelected && (
                            <CheckCircle2 className="h-4 w-4 text-primary-400" />
                          )}
                          {playbook.name}
                        </CardTitle>
                        {isLocked && <Lock className="h-4 w-4 text-yellow-500" />}
                      </div>
                      <CardDescription>
                        {playbook.company} • {playbook.sector}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}

              {playbooks.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun playbook disponible</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Module Selection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="h-5 w-5 text-primary-400" />
              <h2 className="text-lg font-semibold">2. Choisir la méthode</h2>
            </div>
            <div className="space-y-3">
              {modules.map((module) => {
                const isSelected = selectedModule === module.id;
                const config = moduleConfig[module.id] || {
                  icon: <BookOpen className="h-5 w-5" />,
                  color: "text-gray-400",
                  bgColor: "bg-gray-500/20 border-gray-500/30",
                };

                return (
                  <Card
                    key={module.id}
                    className={cn(
                      "cursor-pointer transition-all",
                      isSelected
                        ? "border-primary-500 bg-primary-500/10"
                        : "hover:border-primary-500/50"
                    )}
                    onClick={() => setSelectedModule(module.id)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          {isSelected ? (
                            <CheckCircle2 className="h-4 w-4 text-primary-400" />
                          ) : (
                            <span className={config.color}>{config.icon}</span>
                          )}
                          {module.name}
                        </CardTitle>
                        <Badge className={cn(config.bgColor, config.color, "text-xs")}>
                          {module.category || "Méthode"}
                        </Badge>
                      </div>
                      <CardDescription className="line-clamp-2">
                        {module.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}

              {modules.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <GraduationCap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun module disponible</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Summary and Start */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8"
        >
          <Card className="border-primary-500/30 bg-primary-500/5">
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl bg-primary-500/20">
                    <Target className="h-6 w-6 text-primary-400" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {selectedPlaybookData?.name || "Aucun produit"} × {selectedModuleData?.name || "Aucune méthode"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Prêt à démarrer votre session d&apos;entraînement
                    </p>
                  </div>
                </div>

                <Button
                  size="lg"
                  className="bg-gradient-primary min-w-[200px]"
                  disabled={!selectedPlaybook || !selectedModule || starting}
                  onClick={handleStartSession}
                >
                  {starting ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                    >
                      <Sparkles className="h-5 w-5" />
                    </motion.div>
                  ) : (
                    <>
                      Démarrer
                      <ArrowRight className="h-5 w-5 ml-2" />
                    </>
                  )}
                </Button>
              </div>

              {/* Info box */}
              <div className="mt-4 p-3 rounded-lg bg-muted/50 flex items-start gap-3">
                <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                <div className="text-sm text-muted-foreground">
                  <p>
                    Le prospect sera généré automatiquement avec un besoin réel et des objections cachées.
                    Vous serez évalué selon la méthode choisie.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
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
