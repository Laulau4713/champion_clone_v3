"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  User,
  MessageSquare,
  HelpCircle,
  Package,
  Trophy,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Target,
  DollarSign,
  Clock,
  Users,
  Building,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  SalesPlaybook,
  ConversationContext,
  ConversationPhase,
  HelperSectionId,
  ObjectionResponse,
  PHASE_SECTION_RELEVANCE,
  PHASE_SECTION_HIGHLIGHT,
} from "@/types/playbook";

// ============================================
// TYPES
// ============================================

interface SalesHelperAccordionProps {
  playbook: Partial<SalesPlaybook>;
  context: ConversationContext;
  level: "easy" | "medium" | "expert";
  className?: string;
}

interface SectionConfig {
  id: HelperSectionId;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

// ============================================
// CONFIGURATION DES SECTIONS
// ============================================

const SECTIONS: SectionConfig[] = [
  {
    id: "prospect",
    label: "Prospect",
    icon: <User className="h-4 w-4" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  {
    id: "pitch",
    label: "Mon Pitch",
    icon: <MessageSquare className="h-4 w-4" />,
    color: "text-primary-400",
    bgColor: "bg-primary-500/10",
  },
  {
    id: "questions",
    label: "Questions",
    icon: <HelpCircle className="h-4 w-4" />,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
  },
  {
    id: "solution",
    label: "Ma Solution",
    icon: <Package className="h-4 w-4" />,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
  },
  {
    id: "proofs",
    label: "Mes Preuves",
    icon: <Trophy className="h-4 w-4" />,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
  },
  {
    id: "objections",
    label: "Objections",
    icon: <Shield className="h-4 w-4" />,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
  },
];

// ============================================
// MAPPING PHASE -> SECTIONS
// ============================================

const PHASE_RELEVANCE: Record<ConversationPhase, HelperSectionId[]> = {
  opening: ["prospect", "pitch"],
  discovery: ["prospect", "questions", "solution"],
  presentation: ["solution", "proofs", "pitch"],
  objection: ["objections", "proofs"],
  negotiation: ["proofs", "solution", "objections"],
  closing: ["proofs", "pitch"],
};

const PHASE_HIGHLIGHT: Record<ConversationPhase, HelperSectionId> = {
  opening: "pitch",
  discovery: "questions",
  presentation: "solution",
  objection: "objections",
  negotiation: "proofs",
  closing: "pitch",
};

const PHASE_LABELS: Record<ConversationPhase, string> = {
  opening: "Accroche",
  discovery: "Découverte",
  presentation: "Présentation",
  objection: "Objection",
  negotiation: "Négociation",
  closing: "Closing",
};

// ============================================
// COMPOSANT PRINCIPAL
// ============================================

export function SalesHelperAccordion({
  playbook,
  context,
  level,
  className,
}: SalesHelperAccordionProps) {
  // Sections ouvertes (accordéon multi-ouvert possible)
  const [openSections, setOpenSections] = useState<string[]>(["prospect"]);

  // Détermine les sections pertinentes et highlighted
  const { relevantSections, highlightedSection } = useMemo(() => {
    const relevant = PHASE_RELEVANCE[context.phase] || [];
    let highlighted = PHASE_HIGHLIGHT[context.phase];

    // Si objection détectée, forcer highlight sur objections
    if (context.detectedObjectionType) {
      highlighted = "objections";
    }

    // Si conversion possible, highlight closing/pitch
    if (context.conversionPossible && context.currentJauge >= 75) {
      highlighted = "pitch";
    }

    return { relevantSections: relevant, highlightedSection: highlighted };
  }, [context]);

  // Auto-ouvrir la section highlighted quand elle change
  useEffect(() => {
    if (highlightedSection) {
      setOpenSections((prev) =>
        prev.includes(highlightedSection) ? prev : [...prev, highlightedSection]
      );
    }
  }, [highlightedSection]);

  // Trouver l'objection correspondante si détectée
  const matchedObjection = useMemo(() => {
    if (!context.detectedObjectionType || !playbook.objectionResponses) {
      return null;
    }
    return playbook.objectionResponses.find(
      (obj) => obj.type === context.detectedObjectionType
    );
  }, [context.detectedObjectionType, playbook.objectionResponses]);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header avec indicateur de phase */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Target className="h-4 w-4 text-primary-400" />
            Aide à la vente
          </h3>
          <Badge
            variant="outline"
            className={cn(
              "text-xs",
              context.phase === "objection" && "border-red-500/50 text-red-400",
              context.phase === "closing" && "border-green-500/50 text-green-400",
              context.phase === "discovery" && "border-yellow-500/50 text-yellow-400"
            )}
          >
            {PHASE_LABELS[context.phase]}
          </Badge>
        </div>

        {/* Barre de progression conversation */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{context.exchangeCount} échanges</span>
          <span>•</span>
          <span>Jauge: {context.currentJauge}%</span>
          {context.conversionPossible && (
            <>
              <span>•</span>
              <span className="text-green-400 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Conversion possible
              </span>
            </>
          )}
        </div>
      </div>

      {/* Alerte objection détectée */}
      <AnimatePresence>
        {matchedObjection && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mt-3"
          >
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-medium text-red-400 mb-1">
                    Objection détectée : {matchedObjection.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {matchedObjection.hiddenMeaning}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Accordéon principal */}
      <ScrollArea className="flex-1 px-4 py-3">
        <Accordion
          type="multiple"
          value={openSections}
          onValueChange={setOpenSections}
          className="space-y-2"
        >
          {SECTIONS.map((section) => {
            const isRelevant = relevantSections.includes(section.id);
            const isHighlighted = highlightedSection === section.id;

            return (
              <AccordionItem
                key={section.id}
                value={section.id}
                className={cn(
                  "border rounded-lg overflow-hidden transition-all duration-200",
                  isHighlighted
                    ? "border-primary-500/50 bg-primary-500/5"
                    : isRelevant
                    ? "border-white/20 bg-white/5"
                    : "border-white/10 bg-white/[0.02] opacity-60"
                )}
              >
                <AccordionTrigger
                  className={cn(
                    "px-3 py-2 text-sm hover:no-underline",
                    isHighlighted && "text-primary-400"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className={section.color}>{section.icon}</span>
                    <span>{section.label}</span>
                    {isHighlighted && (
                      <Badge className="ml-2 bg-primary-500/20 text-primary-400 text-[10px] px-1.5 py-0">
                        Utile maintenant
                      </Badge>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-3 pb-3">
                  <SectionContent
                    sectionId={section.id}
                    playbook={playbook}
                    context={context}
                    level={level}
                    matchedObjection={matchedObjection}
                  />
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </ScrollArea>
    </div>
  );
}

// ============================================
// CONTENU DES SECTIONS
// ============================================

interface SectionContentProps {
  sectionId: HelperSectionId;
  playbook: Partial<SalesPlaybook>;
  context: ConversationContext;
  level: "easy" | "medium" | "expert";
  matchedObjection: ObjectionResponse | null;
}

function SectionContent({
  sectionId,
  playbook,
  context,
  level,
  matchedObjection,
}: SectionContentProps) {
  switch (sectionId) {
    case "prospect":
      return <ProspectSection prospect={playbook.prospect} />;
    case "pitch":
      return <PitchSection pitch={playbook.pitch} level={level} />;
    case "questions":
      return <QuestionsSection pitch={playbook.pitch} phase={context.phase} />;
    case "solution":
      return <SolutionSection product={playbook.product} />;
    case "proofs":
      return <ProofsSection proofs={playbook.proofs} />;
    case "objections":
      return (
        <ObjectionsSection
          objections={playbook.objectionResponses}
          matchedObjection={matchedObjection}
        />
      );
    default:
      return null;
  }
}

// ============================================
// SECTION: PROSPECT
// ============================================

function ProspectSection({ prospect }: { prospect?: SalesPlaybook["prospect"] }) {
  if (!prospect) {
    return <p className="text-xs text-muted-foreground">Données prospect non disponibles</p>;
  }

  return (
    <div className="space-y-3">
      {/* Identité */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
          <User className="h-5 w-5 text-blue-400" />
        </div>
        <div>
          <p className="font-medium text-sm">
            {prospect.firstName} {prospect.lastName}
          </p>
          <p className="text-xs text-muted-foreground">{prospect.role}</p>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <Building className="h-3 w-3" />
            {prospect.company} ({prospect.companySize})
          </p>
        </div>
      </div>

      {/* Personnalité */}
      <div className="p-2 rounded bg-blue-500/10">
        <p className="text-xs text-blue-400 font-medium mb-1">Personnalité</p>
        <p className="text-xs text-muted-foreground capitalize">{prospect.personality}</p>
      </div>

      {/* Besoin */}
      <div className="space-y-2">
        <p className="text-xs text-orange-400 font-medium">Son besoin</p>
        <div className="space-y-1.5">
          <div className="p-2 rounded bg-white/5">
            <p className="text-[10px] text-muted-foreground uppercase mb-0.5">Situation</p>
            <p className="text-xs">{prospect.need.currentSituation}</p>
          </div>
          <div className="p-2 rounded bg-orange-500/10">
            <p className="text-[10px] text-orange-400 uppercase mb-0.5">Douleur</p>
            <p className="text-xs">{prospect.need.pain}</p>
          </div>
          <div className="p-2 rounded bg-white/5">
            <p className="text-[10px] text-muted-foreground uppercase mb-0.5">Enjeu</p>
            <p className="text-xs">{prospect.need.stakes}</p>
          </div>
          {prospect.need.trigger && (
            <div className="p-2 rounded bg-green-500/10">
              <p className="text-[10px] text-green-400 uppercase mb-0.5">Déclencheur</p>
              <p className="text-xs">{prospect.need.trigger}</p>
            </div>
          )}
        </div>
      </div>

      {/* Objections probables */}
      {prospect.likelyObjections && prospect.likelyObjections.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-red-400 font-medium">Objections probables</p>
          {prospect.likelyObjections.map((obj, i) => (
            <div key={i} className="p-2 rounded bg-red-500/5 border border-red-500/20">
              <p className="text-xs">&quot;{obj.expressed}&quot;</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                → {obj.hidden}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================
// SECTION: PITCH
// ============================================

function PitchSection({
  pitch,
  level,
}: {
  pitch?: SalesPlaybook["pitch"];
  level: string;
}) {
  if (!pitch) {
    return <p className="text-xs text-muted-foreground">Pitch non disponible</p>;
  }

  return (
    <div className="space-y-3">
      {/* Accroche 30s */}
      <div className="p-3 rounded-lg bg-gradient-to-r from-primary-500/10 to-secondary-500/10 border border-primary-500/20">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-3 w-3 text-primary-400" />
          <p className="text-xs text-primary-400 font-medium">Accroche 30 secondes</p>
        </div>
        <p className="text-xs leading-relaxed whitespace-pre-line">{pitch.hook30s}</p>
      </div>

      {/* Pitch 2min (visible en easy/medium) */}
      {(level === "easy" || level === "medium") && (
        <div className="p-3 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="h-3 w-3 text-muted-foreground" />
            <p className="text-xs text-muted-foreground font-medium">Pitch complet (2 min)</p>
          </div>
          <p className="text-xs leading-relaxed whitespace-pre-line text-muted-foreground">
            {pitch.pitch2min}
          </p>
        </div>
      )}

      {/* Phrases clés */}
      {level === "easy" && (
        <div className="space-y-2">
          <p className="text-xs text-yellow-400 font-medium">Phrases clés</p>

          {pitch.keyPhrases.hooks.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-muted-foreground uppercase">Accroches</p>
              {pitch.keyPhrases.hooks.slice(0, 2).map((phrase, i) => (
                <p key={i} className="text-xs p-1.5 rounded bg-white/5 italic">
                  &quot;{phrase}&quot;
                </p>
              ))}
            </div>
          )}

          {pitch.keyPhrases.closings.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-muted-foreground uppercase">Closing</p>
              {pitch.keyPhrases.closings.slice(0, 2).map((phrase, i) => (
                <p key={i} className="text-xs p-1.5 rounded bg-green-500/10 italic">
                  &quot;{phrase}&quot;
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================
// SECTION: QUESTIONS
// ============================================

function QuestionsSection({
  pitch,
  phase,
}: {
  pitch?: SalesPlaybook["pitch"];
  phase: ConversationPhase;
}) {
  if (!pitch?.discoveryQuestions) {
    return <p className="text-xs text-muted-foreground">Questions non disponibles</p>;
  }

  // Filtrer les questions pertinentes selon la phase
  const relevantCategories =
    phase === "discovery"
      ? ["situation", "pain"]
      : phase === "presentation"
      ? ["impact", "decision"]
      : ["situation", "pain", "impact", "decision"];

  return (
    <div className="space-y-3">
      {pitch.discoveryQuestions
        .filter((cat) => relevantCategories.includes(cat.category))
        .map((category) => (
          <div key={category.category} className="space-y-1.5">
            <p className="text-xs text-yellow-400 font-medium">{category.label}</p>
            {category.questions.slice(0, 3).map((q, i) => (
              <div
                key={i}
                className="p-2 rounded bg-yellow-500/5 border border-yellow-500/20"
              >
                <p className="text-xs">{q}</p>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}

// ============================================
// SECTION: SOLUTION
// ============================================

function SolutionSection({ product }: { product?: SalesPlaybook["product"] }) {
  if (!product) {
    return <p className="text-xs text-muted-foreground">Solution non disponible</p>;
  }

  return (
    <div className="space-y-3">
      {/* Header produit */}
      <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
        <div className="flex items-center gap-2 mb-1">
          <Package className="h-4 w-4 text-green-400" />
          <p className="font-medium text-sm text-green-400">{product.name}</p>
        </div>
        <p className="text-xs text-muted-foreground">{product.type}</p>
      </div>

      {/* Problème résolu */}
      <div className="space-y-1.5">
        <p className="text-xs text-orange-400 font-medium">Problème résolu</p>
        <p className="text-xs">{product.problemSolved.title}</p>
        <ul className="space-y-0.5">
          {product.problemSolved.impacts.slice(0, 3).map((impact, i) => (
            <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
              <span className="text-orange-400">•</span>
              {impact}
            </li>
          ))}
        </ul>
      </div>

      {/* Comment ça marche */}
      <div className="space-y-1.5">
        <p className="text-xs text-blue-400 font-medium">Comment ça marche</p>
        <p className="text-xs text-muted-foreground">{product.howItWorks.summary}</p>
        {product.howItWorks.steps.slice(0, 3).map((step, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-xs text-blue-400 font-bold">{i + 1}.</span>
            <div>
              <p className="text-xs font-medium">{step.title}</p>
              <p className="text-[10px] text-muted-foreground">{step.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Bénéfices clés */}
      <div className="space-y-1.5">
        <p className="text-xs text-green-400 font-medium">Bénéfices clés</p>
        <p className="text-xs p-2 rounded bg-green-500/10 font-medium">
          {product.benefits.main}
        </p>
      </div>

      {/* Prix */}
      <div className="space-y-1.5">
        <p className="text-xs text-primary-400 font-medium flex items-center gap-1">
          <DollarSign className="h-3 w-3" />
          Tarifs
        </p>
        {product.pricing.offers.slice(0, 2).map((offer, i) => (
          <div key={i} className="p-2 rounded bg-white/5">
            <div className="flex justify-between items-center">
              <p className="text-xs font-medium">{offer.name}</p>
              <p className="text-xs text-primary-400">{offer.price}</p>
            </div>
            {offer.targetAudience && (
              <p className="text-[10px] text-muted-foreground">{offer.targetAudience}</p>
            )}
          </div>
        ))}
        {product.pricing.guarantees.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {product.pricing.guarantees.slice(0, 2).map((g, i) => (
              <Badge key={i} variant="outline" className="text-[10px]">
                {g}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Différenciateur */}
      <div className="p-2 rounded bg-gradient-to-r from-primary-500/10 to-green-500/10 border border-primary-500/20">
        <p className="text-[10px] text-primary-400 uppercase mb-1">Différenciateur</p>
        <p className="text-xs">{product.differentiator}</p>
      </div>
    </div>
  );
}

// ============================================
// SECTION: PREUVES
// ============================================

function ProofsSection({ proofs }: { proofs?: SalesPlaybook["proofs"] }) {
  if (!proofs) {
    return <p className="text-xs text-muted-foreground">Preuves non disponibles</p>;
  }

  return (
    <div className="space-y-3">
      {/* Stats globales */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-2 rounded bg-orange-500/10 text-center">
          <p className="text-sm font-bold text-orange-400">{proofs.globalStats.clients}</p>
          <p className="text-[10px] text-muted-foreground">Clients</p>
        </div>
        <div className="p-2 rounded bg-green-500/10 text-center">
          <p className="text-sm font-bold text-green-400">{proofs.globalStats.satisfaction}</p>
          <p className="text-[10px] text-muted-foreground">Satisfaction</p>
        </div>
        <div className="p-2 rounded bg-primary-500/10 text-center">
          <p className="text-[10px] font-bold text-primary-400">{proofs.globalStats.mainResult}</p>
        </div>
      </div>

      {/* Témoignages */}
      {proofs.testimonials.slice(0, 2).map((testimonial, i) => (
        <div key={i} className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
              <Users className="h-4 w-4 text-orange-400" />
            </div>
            <div>
              <p className="text-xs font-medium">{testimonial.clientName}</p>
              <p className="text-[10px] text-muted-foreground">
                {testimonial.clientRole} - {testimonial.company}
              </p>
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-[10px] text-orange-400">Avant:</p>
            <p className="text-xs text-muted-foreground">{testimonial.problemBefore}</p>
          </div>

          <div className="space-y-1">
            <p className="text-[10px] text-green-400">Résultats:</p>
            {testimonial.results.slice(0, 2).map((r, j) => (
              <p key={j} className="text-xs flex items-start gap-1">
                <CheckCircle2 className="h-3 w-3 text-green-400 mt-0.5 flex-shrink-0" />
                {r}
              </p>
            ))}
          </div>

          <div className="p-2 rounded bg-white/5 italic">
            <p className="text-xs">&quot;{testimonial.quote}&quot;</p>
          </div>
        </div>
      ))}

      {/* Certifications */}
      {proofs.certifications.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {proofs.certifications.map((cert, i) => (
            <Badge key={i} variant="outline" className="text-[10px]">
              {cert}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================
// SECTION: OBJECTIONS
// ============================================

function ObjectionsSection({
  objections,
  matchedObjection,
}: {
  objections?: ObjectionResponse[];
  matchedObjection: ObjectionResponse | null;
}) {
  if (!objections || objections.length === 0) {
    return <p className="text-xs text-muted-foreground">Objections non disponibles</p>;
  }

  // Si une objection est détectée, l'afficher en premier
  const sortedObjections = matchedObjection
    ? [matchedObjection, ...objections.filter((o) => o.type !== matchedObjection.type)]
    : objections;

  return (
    <div className="space-y-3">
      {sortedObjections.map((objection, i) => {
        const isMatched = matchedObjection?.type === objection.type;

        return (
          <div
            key={i}
            className={cn(
              "p-3 rounded-lg border space-y-2",
              isMatched
                ? "bg-red-500/10 border-red-500/30"
                : "bg-white/5 border-white/10"
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <p className={cn("text-xs font-medium", isMatched && "text-red-400")}>
                {objection.label}
              </p>
              {isMatched && (
                <Badge className="bg-red-500/20 text-red-400 text-[10px]">
                  Détectée !
                </Badge>
              )}
            </div>

            {/* Ce qu'il dit */}
            <div>
              <p className="text-[10px] text-muted-foreground mb-0.5">Il dit :</p>
              {objection.variants.slice(0, 2).map((v, j) => (
                <p key={j} className="text-xs italic">&quot;{v}&quot;</p>
              ))}
            </div>

            {/* Ce qu'il pense */}
            <div className="p-2 rounded bg-white/5">
              <p className="text-[10px] text-yellow-400 mb-0.5">Il pense vraiment :</p>
              <p className="text-xs">{objection.hiddenMeaning}</p>
            </div>

            {/* Réponse */}
            <div className={cn("p-2 rounded", isMatched ? "bg-green-500/10" : "bg-primary-500/10")}>
              <p className="text-[10px] text-green-400 mb-0.5 flex items-center gap-1">
                <Lightbulb className="h-3 w-3" />
                Votre réponse :
              </p>
              <p className="text-xs whitespace-pre-line">{objection.response}</p>
            </div>

            {/* Preuve à utiliser */}
            <div className="flex items-center gap-1 text-[10px] text-orange-400">
              <Trophy className="h-3 w-3" />
              <span>Preuve : {objection.proofToUse}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
