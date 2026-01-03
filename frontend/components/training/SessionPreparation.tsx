"use client";

import { motion } from "framer-motion";
import {
  User,
  Building2,
  Briefcase,
  Target,
  AlertCircle,
  MessageSquare,
  CheckCircle2,
  Lightbulb,
  FileText,
  ArrowRight,
  Package,
  Star,
  DollarSign,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ProspectInfo {
  name?: string;
  role?: string;
  company?: string;
  personality?: string;
}

interface SolutionInfo {
  product_name?: string;
  value_proposition?: string;
  key_benefits?: string[];
  pricing_hint?: string;
  differentiator?: string;
}

interface ScenarioInfo {
  title?: string;
  context?: string;
  prospect?: ProspectInfo;
  opening_message?: string | { text: string; audio_base64?: string };
  pain_points?: string[];
  hidden_need?: string;
  objections?: Array<{ expressed: string; hidden?: string }>;
  solution?: SolutionInfo;
  product_pitch?: string;
}

interface SessionPreparationProps {
  scenario: ScenarioInfo | null;
  skillName: string;
  level: string;
  onStart: () => void;
  isLoading?: boolean;
}

/**
 * Page de préparation avant une session de training.
 * Affiche les infos du prospect, le contexte, et un script guide.
 */
export function SessionPreparation({
  scenario,
  skillName,
  level,
  onStart,
  isLoading = false,
}: SessionPreparationProps) {
  if (!scenario) {
    return null;
  }

  const prospect = scenario.prospect || {};
  const painPoints = scenario.pain_points || [];
  const objections = scenario.objections || [];
  const solution = scenario.solution;
  const productPitch = scenario.product_pitch;

  // Générer un script guide basé sur le contexte
  const generateScript = () => {
    const scripts: string[] = [];

    // Phrase d'accroche personnalisée
    if (prospect.name && prospect.company) {
      scripts.push(
        `"Bonjour ${prospect.name}, je vous appelle concernant ${prospect.company}. Est-ce un bon moment pour échanger ?"`
      );
    }

    // Questions de découverte basées sur les pain points
    if (painPoints.length > 0) {
      scripts.push(
        `"Quels sont les principaux défis que vous rencontrez actuellement dans votre activité ?"`
      );
      scripts.push(
        `"J'imagine que vous êtes confronté à ${painPoints[0].toLowerCase()}. Comment gérez-vous cela aujourd'hui ?"`
      );
    }

    // Question pour découvrir le besoin caché
    if (scenario.hidden_need) {
      scripts.push(
        `"Au-delà de l'aspect technique, qu'est-ce qui serait vraiment important pour vous dans une solution ?"`
      );
    }

    // Gérer les objections potentielles
    if (objections.length > 0) {
      scripts.push(
        `"Je comprends votre préoccupation. Pouvez-vous m'en dire plus sur ce qui vous freine ?"`
      );
    }

    // Phrases de closing
    scripts.push(
      `"Si je comprends bien, vous cherchez une solution qui... C'est bien cela ?"`
    );
    scripts.push(
      `"Qu'est-ce qui vous aiderait à prendre une décision aujourd'hui ?"`
    );

    return scripts;
  };

  const scriptPhrases = generateScript();

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-4xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold gradient-text mb-2">
              Préparation de Session
            </h1>
            <p className="text-muted-foreground">
              Prenez connaissance du contexte avant de commencer
            </p>
            <div className="flex items-center justify-center gap-2 mt-4">
              <Badge variant="outline">{skillName}</Badge>
              <Badge
                className={cn(
                  level === "easy" && "bg-green-500/20 text-green-400",
                  level === "medium" && "bg-yellow-500/20 text-yellow-400",
                  level === "expert" && "bg-red-500/20 text-red-400"
                )}
              >
                {level === "easy" && "Facile"}
                {level === "medium" && "Moyen"}
                {level === "expert" && "Expert"}
              </Badge>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Infos du prospect */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="glass rounded-2xl p-6"
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <User className="h-5 w-5 text-primary-400" />
                Le Prospect
              </h2>

              <div className="space-y-4">
                {prospect.name && (
                  <div className="flex items-start gap-3">
                    <User className="h-4 w-4 text-muted-foreground mt-1" />
                    <div>
                      <p className="text-sm text-muted-foreground">Nom</p>
                      <p className="font-medium">{prospect.name}</p>
                    </div>
                  </div>
                )}

                {prospect.role && (
                  <div className="flex items-start gap-3">
                    <Briefcase className="h-4 w-4 text-muted-foreground mt-1" />
                    <div>
                      <p className="text-sm text-muted-foreground">Fonction</p>
                      <p className="font-medium">{prospect.role}</p>
                    </div>
                  </div>
                )}

                {prospect.company && (
                  <div className="flex items-start gap-3">
                    <Building2 className="h-4 w-4 text-muted-foreground mt-1" />
                    <div>
                      <p className="text-sm text-muted-foreground">Entreprise</p>
                      <p className="font-medium">{prospect.company}</p>
                    </div>
                  </div>
                )}

                {prospect.personality && (
                  <div className="flex items-start gap-3">
                    <MessageSquare className="h-4 w-4 text-muted-foreground mt-1" />
                    <div>
                      <p className="text-sm text-muted-foreground">Personnalité</p>
                      <Badge variant="outline" className="mt-1">
                        {prospect.personality === "skeptical" && "Sceptique"}
                        {prospect.personality === "friendly" && "Amical"}
                        {prospect.personality === "busy" && "Pressé"}
                        {prospect.personality === "analytical" && "Analytique"}
                        {prospect.personality === "impatient" && "Impatient"}
                        {prospect.personality === "neutral" && "Neutre"}
                        {!["skeptical", "friendly", "busy", "analytical", "impatient", "neutral"].includes(prospect.personality || "") && prospect.personality}
                      </Badge>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Contexte et besoins */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-2xl p-6"
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="h-5 w-5 text-primary-400" />
                Contexte & Besoins
              </h2>

              {scenario.context && (
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground mb-2">Situation</p>
                  <p className="text-sm bg-white/5 rounded-lg p-3">
                    {scenario.context}
                  </p>
                </div>
              )}

              {painPoints.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground mb-2">
                    Problématiques identifiées
                  </p>
                  <ul className="space-y-2">
                    {painPoints.map((point, i) => (
                      <li
                        key={i}
                        className="text-sm flex items-start gap-2 bg-orange-500/10 rounded-lg p-2"
                      >
                        <AlertCircle className="h-4 w-4 text-orange-400 mt-0.5 flex-shrink-0" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {scenario.hidden_need && (
                <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="h-4 w-4 text-yellow-400 mt-0.5" />
                    <div>
                      <p className="text-xs text-yellow-400 font-medium">
                        Besoin caché potentiel
                      </p>
                      <p className="text-sm text-yellow-200">
                        {scenario.hidden_need}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* Votre Solution - LA section clé pour le commercial */}
          {solution && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
              className="glass rounded-2xl p-6 border-2 border-primary-500/30"
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Package className="h-5 w-5 text-primary-400" />
                Votre Solution à Proposer
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Infos produit */}
                <div className="space-y-4">
                  {solution.product_name && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Produit / Service</p>
                      <p className="text-xl font-bold text-primary-400">{solution.product_name}</p>
                    </div>
                  )}

                  {solution.value_proposition && (
                    <div className="p-3 rounded-lg bg-primary-500/10 border border-primary-500/20">
                      <p className="text-sm font-medium text-primary-300">
                        {solution.value_proposition}
                      </p>
                    </div>
                  )}

                  {solution.key_benefits && solution.key_benefits.length > 0 && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-2 flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        Bénéfices clés
                      </p>
                      <ul className="space-y-2">
                        {solution.key_benefits.map((benefit, i) => (
                          <li
                            key={i}
                            className="text-sm flex items-start gap-2 bg-green-500/10 rounded-lg p-2"
                          >
                            <CheckCircle2 className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                            <span>{benefit}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Prix et différenciation */}
                <div className="space-y-4">
                  {solution.pricing_hint && (
                    <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                      <div className="flex items-start gap-2">
                        <DollarSign className="h-4 w-4 text-yellow-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-yellow-400 font-medium">Positionnement prix</p>
                          <p className="text-sm text-yellow-200">{solution.pricing_hint}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {solution.differentiator && (
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                      <div className="flex items-start gap-2">
                        <Star className="h-4 w-4 text-blue-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-blue-400 font-medium">Ce qui vous différencie</p>
                          <p className="text-sm text-blue-200">{solution.differentiator}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Pitch commercial prêt à l'emploi */}
              {productPitch && (
                <div className="mt-6 pt-4 border-t border-white/10">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-primary-400" />
                    Votre pitch pour ce prospect
                  </h3>
                  <div className="p-4 rounded-lg bg-gradient-to-r from-primary-500/10 to-secondary-500/10 border border-primary-500/20">
                    <p className="text-sm italic leading-relaxed">&quot;{productPitch}&quot;</p>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Script Guide */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary-400" />
              Script & Phrases Clés
            </h2>

            <p className="text-sm text-muted-foreground mb-4">
              Voici des phrases que vous pouvez adapter pour guider la conversation :
            </p>

            <ScrollArea className="h-[200px] pr-4">
              <div className="space-y-3">
                {scriptPhrases.map((phrase, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center text-xs text-primary-400 font-medium">
                      {i + 1}
                    </div>
                    <p className="text-sm italic">{phrase}</p>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Objections à anticiper */}
            {objections.length > 0 && (
              <div className="mt-6 pt-4 border-t border-white/10">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-orange-400" />
                  Objections à anticiper
                </h3>
                <div className="space-y-2">
                  {objections.slice(0, 3).map((obj, i) => (
                    <div
                      key={i}
                      className="text-sm p-2 rounded-lg bg-orange-500/10"
                    >
                      <span className="text-orange-300">{obj.expressed}</span>
                      {obj.hidden && (
                        <span className="text-muted-foreground ml-2">
                          → Vraie raison : {obj.hidden}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>

          {/* Conseils rapides */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-400" />
              Conseils pour Réussir
            </h2>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-green-400">
                  Ce qui fonctionne
                </h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-3 w-3 text-green-400 mt-1" />
                    Poser des questions ouvertes
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-3 w-3 text-green-400 mt-1" />
                    Reformuler pour montrer que vous écoutez
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-3 w-3 text-green-400 mt-1" />
                    Creuser les besoins avant de proposer
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-3 w-3 text-green-400 mt-1" />
                    Rester calme face aux objections
                  </li>
                </ul>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-red-400">
                  Ce qu&apos;il faut éviter
                </h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <AlertCircle className="h-3 w-3 text-red-400 mt-1" />
                    Parler du prix trop tôt
                  </li>
                  <li className="flex items-start gap-2">
                    <AlertCircle className="h-3 w-3 text-red-400 mt-1" />
                    Enchaîner les questions fermées
                  </li>
                  <li className="flex items-start gap-2">
                    <AlertCircle className="h-3 w-3 text-red-400 mt-1" />
                    Interrompre le prospect
                  </li>
                  <li className="flex items-start gap-2">
                    <AlertCircle className="h-3 w-3 text-red-400 mt-1" />
                    Dénigrer la concurrence
                  </li>
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Bouton de démarrage */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-center pt-4"
          >
            <Button
              size="lg"
              onClick={onStart}
              disabled={isLoading}
              className="bg-gradient-primary px-8 py-6 text-lg"
            >
              {isLoading ? (
                "Préparation..."
              ) : (
                <>
                  Commencer la Session
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </Button>
            <p className="text-xs text-muted-foreground mt-3">
              La session démarrera avec le message d&apos;ouverture du prospect
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
