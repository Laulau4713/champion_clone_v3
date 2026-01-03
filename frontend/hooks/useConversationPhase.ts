/**
 * Hook pour détecter la phase de conversation et le contexte
 * Intelligence contextuelle pour l'aide à la vente
 */

import { useMemo } from "react";
import type {
  ConversationContext,
  ConversationPhase,
  ObjectionResponse,
} from "@/types/playbook";

// ============================================
// PATTERNS DE DÉTECTION D'OBJECTIONS
// ============================================

const OBJECTION_PATTERNS: Record<ObjectionResponse["type"], RegExp[]> = {
  budget: [
    /trop cher/i,
    /pas le budget/i,
    /budget.*(serr|limit)/i,
    /coût|prix.*(élevé|important)/i,
    /on (ne )?peut pas se permettre/i,
    /combien (ça|cela) coûte/i,
    /c'est (un )?budget/i,
    /investissement (trop )?important/i,
  ],
  timing: [
    /pas (le )?moment/i,
    /rappelez.*(plus tard|dans)/i,
    /pas maintenant/i,
    /en ce moment/i,
    /(plein|milieu).*(rush|travail|projet)/i,
    /l'année prochaine/i,
    /dans (quelques |6 )?mois/i,
    /on verra/i,
    /revenez vers/i,
  ],
  competition: [
    /on a déjà/i,
    /déjà (un |quelqu'un|une solution)/i,
    /on utilise/i,
    /on travaille (déjà )?avec/i,
    /notre prestataire/i,
    /on est équipé/i,
    /concurrent/i,
    /autre (solution|fournisseur)/i,
  ],
  trust: [
    /connais pas/i,
    /jamais entendu/i,
    /c'est quoi (votre|cette)/i,
    /vous êtes (qui|fiable)/i,
    /référence/i,
    /garantie/i,
    /comment (je peux |on peut )?être sûr/i,
    /preuve/i,
  ],
  decision: [
    /pas (moi qui|à moi de) décide/i,
    /en parler à/i,
    /mon (associé|patron|chef|dg|directeur)/i,
    /faut (que je |qu'on )?valide/i,
    /décision.*(collective|pas seul)/i,
    /comité/i,
    /hiérarchie/i,
  ],
  status_quo: [
    /fonctionne (bien |très )?comme ça/i,
    /toujours fait comme ça/i,
    /pourquoi changer/i,
    /on s'en sort/i,
    /pas besoin/i,
    /ça (va|marche) (très )?bien/i,
    /on (se |s'en )?débrouille/i,
    /changement/i,
  ],
  adoption: [
    /équipe.*(jamais|pas).*(utiliser|adopter)/i,
    /trop compliqué/i,
    /personne (ne )?va l'utiliser/i,
    /déjà essayé/i,
    /formation/i,
    /apprendre/i,
    /habitudes/i,
  ],
};

// ============================================
// PATTERNS DE FIN DE CONVERSATION
// ============================================

const END_PATTERNS = [
  /au revoir/i,
  /bonne (journée|continuation)/i,
  /à bientôt/i,
  /merci.*(temps|appel)/i,
  /on (se |vous )rappelle/i,
];

// ============================================
// PATTERNS DE SIGNAUX D'ACHAT
// ============================================

const BUYING_SIGNALS = [
  /comment (ça |on )?procède/i,
  /quelles sont les (étapes|prochaines)/i,
  /c'est quoi (les |la )?démarche/i,
  /on (peut |pourrait )?commencer/i,
  /délai.*(mise en place|installation)/i,
  /contrat/i,
  /signer/i,
  /quand (peut-on|pourrait-on)/i,
];

// ============================================
// HOOK PRINCIPAL
// ============================================

interface UseConversationPhaseProps {
  messages: { role: string; text: string }[];
  currentJauge: number;
  conversionPossible: boolean;
  prospectMood: string;
}

export function useConversationPhase({
  messages,
  currentJauge,
  conversionPossible,
  prospectMood,
}: UseConversationPhaseProps): ConversationContext {
  return useMemo(() => {
    const exchangeCount = messages.filter((m) => m.role === "user").length;
    const lastProspectMessage = [...messages]
      .reverse()
      .find((m) => m.role === "prospect" || m.role === "assistant");
    const lastUserMessage = [...messages]
      .reverse()
      .find((m) => m.role === "user");

    // Texte combiné des derniers messages pour analyse
    const recentText = [lastProspectMessage?.text || "", lastUserMessage?.text || ""]
      .join(" ")
      .toLowerCase();

    // 1. Détecter une objection
    let detectedObjectionType: ObjectionResponse["type"] | undefined;
    for (const [type, patterns] of Object.entries(OBJECTION_PATTERNS)) {
      if (patterns.some((pattern) => pattern.test(lastProspectMessage?.text || ""))) {
        detectedObjectionType = type as ObjectionResponse["type"];
        break;
      }
    }

    // 2. Détecter les signaux d'achat
    const hasBuyingSignal = BUYING_SIGNALS.some((pattern) =>
      pattern.test(lastProspectMessage?.text || "")
    );

    // 3. Détecter fin de conversation
    const isEnding = END_PATTERNS.some((pattern) => pattern.test(recentText));

    // 4. Déterminer la phase
    let phase: ConversationPhase = "opening";

    if (isEnding) {
      phase = "closing";
    } else if (detectedObjectionType) {
      phase = "objection";
    } else if (hasBuyingSignal || (conversionPossible && currentJauge >= 80)) {
      phase = "closing";
    } else if (currentJauge >= 70 && exchangeCount >= 6) {
      phase = "negotiation";
    } else if (exchangeCount >= 7 || currentJauge >= 60) {
      phase = "presentation";
    } else if (exchangeCount >= 3) {
      phase = "discovery";
    } else {
      phase = "opening";
    }

    // Ajuster selon le mood du prospect
    if (
      prospectMood === "hostile" ||
      prospectMood === "aggressive" ||
      prospectMood === "skeptical"
    ) {
      // Si prospect négatif et pas d'objection explicite, considérer comme objection
      if (!detectedObjectionType && exchangeCount >= 2) {
        phase = "objection";
      }
    }

    return {
      phase,
      exchangeCount,
      currentJauge,
      detectedObjectionType,
      prospectMood,
      conversionPossible,
    };
  }, [messages, currentJauge, conversionPossible, prospectMood]);
}

// ============================================
// HELPER: Convertir les données scénario en playbook
// ============================================

export function convertScenarioToPlaybook(
  scenario: Record<string, unknown> | undefined | null
): Record<string, unknown> | null {
  if (!scenario) return null;

  const prospect = scenario.prospect as Record<string, unknown> | undefined;
  const solution = scenario.solution as Record<string, unknown> | undefined;
  const objections = scenario.objections as Array<Record<string, unknown>> | undefined;

  return {
    prospect: prospect
      ? {
          firstName: (prospect.name as string)?.split(" ")[0] || "Prospect",
          lastName: (prospect.name as string)?.split(" ").slice(1).join(" ") || "",
          role: prospect.role || "Professionnel",
          company: prospect.company || "Entreprise",
          sector: prospect.sector || "Non défini",
          companySize: prospect.company_size || "PME",
          personality: prospect.personality || "neutral",
          need: {
            currentSituation: prospect.current_situation || "Non défini",
            pain:
              (prospect.pain_points as string[])?.[0] ||
              (scenario.pain_points as string[])?.[0] ||
              "Non défini",
            stakes:
              prospect.hidden_need ||
              scenario.hidden_need ||
              "Non défini",
            trigger: undefined,
          },
          likelyObjections:
            objections?.map((obj) => ({
              type: (obj.type as string) || "status_quo",
              expressed: (obj.expressed as string) || (obj.objection as string) || "",
              hidden: (obj.hidden as string) || "",
              intensity: "medium" as const,
            })) || [],
        }
      : undefined,

    product: solution
      ? {
          name: solution.product_name || "Solution",
          type: "Solution",
          problemSolved: {
            title: solution.value_proposition || "",
            description: "",
            impacts: [],
          },
          howItWorks: {
            summary: solution.differentiator || "",
            steps: [],
          },
          benefits: {
            main: solution.value_proposition || "",
            byCategory: [
              {
                category: "quality" as const,
                label: "Bénéfices",
                items: (solution.key_benefits as string[]) || [],
              },
            ],
          },
          pricing: {
            model: "",
            offers: solution.pricing_hint
              ? [{ name: "Offre", price: solution.pricing_hint as string, includes: [] }]
              : [],
            guarantees: [],
          },
          differentiator: solution.differentiator || "",
        }
      : undefined,

    pitch: {
      hook30s: scenario.product_pitch || "",
      pitch2min: "",
      keyPhrases: {
        hooks: ["Quels sont vos principaux défis actuellement ?"],
        transitions: ["Ce que vous décrivez, c'est exactement..."],
        proofs: [],
        closings: ["On planifie un essai ?"],
      },
      discoveryQuestions: [
        {
          category: "situation" as const,
          label: "Situation",
          questions: [
            "Comment gérez-vous cela aujourd'hui ?",
            "Quels outils utilisez-vous actuellement ?",
          ],
        },
        {
          category: "pain" as const,
          label: "Douleur",
          questions: [
            "Qu'est-ce qui vous pose le plus de problème ?",
            "Quel impact cela a sur votre quotidien ?",
          ],
        },
        {
          category: "impact" as const,
          label: "Impact",
          questions: [
            "Combien cela vous coûte en temps/argent ?",
            "Que se passe-t-il si rien ne change ?",
          ],
        },
        {
          category: "decision" as const,
          label: "Décision",
          questions: [
            "Qui d'autre serait impliqué dans la décision ?",
            "Qu'est-ce qui vous ferait dire oui ?",
          ],
        },
      ],
    },

    objectionResponses:
      objections?.map((obj) => ({
        type: (obj.type as string) || "status_quo",
        label:
          (obj.type as string)?.charAt(0).toUpperCase() +
            (obj.type as string)?.slice(1) || "Objection",
        variants: [(obj.expressed as string) || (obj.objection as string) || ""],
        hiddenMeaning: (obj.hidden as string) || "Le prospect a des doutes",
        response: "Utilisez vos preuves et références clients",
        proofToUse: "Témoignage client",
      })) || [],

    proofs: {
      globalStats: {
        clients: "Plusieurs clients",
        satisfaction: "Satisfaction élevée",
        mainResult: "Résultats prouvés",
      },
      testimonials: [],
      references: [],
      certifications: [],
    },
  };
}
