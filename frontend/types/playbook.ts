/**
 * Types pour le Playbook Commercial
 * Structure complète pour l'aide à la vente pendant les sessions
 */

// ============================================
// SOCIÉTÉ & VENDEUR
// ============================================

export interface Company {
  name: string;
  baseline?: string;
  sector: string;
  creation?: string;
  size?: string;
  location?: string;
  positioning: string;
  values?: string[];
}

export interface Seller {
  name: string;
  role: string;
  experience?: "junior" | "confirmed" | "senior";
}

// ============================================
// PRODUIT / SOLUTION
// ============================================

export interface ProductProblem {
  title: string;
  description: string;
  impacts: string[];
  painsByPersona?: {
    persona: string;
    pains: string[];
  }[];
}

export interface ProductHowItWorks {
  summary: string;
  steps: {
    title: string;
    description: string;
  }[];
  technology?: string;
  differentiator?: string;
}

export interface ProductBenefits {
  main: string;
  byCategory: {
    category: "time" | "money" | "quality" | "human" | "compliance";
    label: string;
    items: string[];
  }[];
}

export interface ProductPricing {
  model: string;
  offers: {
    name: string;
    price: string;
    includes: string[];
    targetAudience?: string;
  }[];
  engagement?: string;
  guarantees: string[];
}

export interface Product {
  name: string;
  type: string;
  problemSolved: ProductProblem;
  howItWorks: ProductHowItWorks;
  benefits: ProductBenefits;
  pricing: ProductPricing;
  differentiator: string;
}

// ============================================
// PITCH COMMERCIAL
// ============================================

export interface SalesPitch {
  hook30s: string;
  pitch2min: string;
  keyPhrases: {
    hooks: string[];
    transitions: string[];
    proofs: string[];
    closings: string[];
  };
  discoveryQuestions: {
    category: "situation" | "pain" | "impact" | "decision";
    label: string;
    questions: string[];
  }[];
}

// ============================================
// OBJECTIONS
// ============================================

export interface ObjectionResponse {
  type: "budget" | "timing" | "competition" | "trust" | "decision" | "status_quo" | "adoption";
  label: string;
  variants: string[];
  hiddenMeaning: string;
  response: string;
  proofToUse: string;
}

// ============================================
// PREUVES
// ============================================

export interface ClientTestimonial {
  clientName: string;
  clientRole: string;
  company: string;
  sector: string;
  size: string;
  problemBefore: string;
  solutionApplied: string;
  results: string[];
  quote: string;
}

export interface Proofs {
  globalStats: {
    clients: string;
    satisfaction: string;
    mainResult: string;
  };
  testimonials: ClientTestimonial[];
  references: string[];
  certifications: string[];
}

// ============================================
// PROSPECT (généré dynamiquement)
// ============================================

export interface ProspectNeed {
  currentSituation: string;
  pain: string;
  stakes: string;
  trigger?: string;
}

export interface ProspectObjection {
  type: ObjectionResponse["type"];
  expressed: string;
  hidden: string;
  intensity: "low" | "medium" | "high";
}

export interface Prospect {
  firstName: string;
  lastName: string;
  role: string;
  company: string;
  sector: string;
  companySize: string;
  personality: "analytical" | "pragmatic" | "speed" | "friendly" | "suspicious" | "emotional";
  need: ProspectNeed;
  likelyObjections: ProspectObjection[];
}

// ============================================
// PLAYBOOK COMPLET
// ============================================

export interface SalesPlaybook {
  company: Company;
  seller?: Seller;
  product: Product;
  pitch: SalesPitch;
  objectionResponses: ObjectionResponse[];
  proofs: Proofs;
  prospect: Prospect;
}

// ============================================
// CONTEXTE DE CONVERSATION (pour intelligence)
// ============================================

export type ConversationPhase =
  | "opening"        // 0-2 échanges : accroche
  | "discovery"      // 3-6 échanges : découverte besoins
  | "presentation"   // 7-10 échanges : présentation solution
  | "objection"      // Objection détectée
  | "negotiation"    // Jauge haute, discussion prix/conditions
  | "closing";       // Jauge très haute, prêt à conclure

export interface ConversationContext {
  phase: ConversationPhase;
  exchangeCount: number;
  currentJauge: number;
  detectedObjectionType?: ObjectionResponse["type"];
  prospectMood: string;
  conversionPossible: boolean;
}

// ============================================
// SECTION D'AIDE (pour l'accordéon)
// ============================================

export type HelperSectionId =
  | "prospect"
  | "pitch"
  | "questions"
  | "solution"
  | "proofs"
  | "objections";

export interface HelperSection {
  id: HelperSectionId;
  label: string;
  icon: string;
  isRelevant: boolean;      // Pertinent pour la phase actuelle
  isHighlighted: boolean;   // Mis en avant (auto-ouvert)
  priority: number;         // Ordre d'affichage (1 = plus important)
}

// ============================================
// MAPPING PHASE -> SECTIONS PERTINENTES
// ============================================

export const PHASE_SECTION_RELEVANCE: Record<ConversationPhase, HelperSectionId[]> = {
  opening: ["prospect", "pitch"],
  discovery: ["prospect", "questions", "solution"],
  presentation: ["solution", "proofs", "pitch"],
  objection: ["objections", "proofs"],
  negotiation: ["proofs", "solution", "objections"],
  closing: ["proofs", "pitch"],
};

export const PHASE_SECTION_HIGHLIGHT: Record<ConversationPhase, HelperSectionId> = {
  opening: "pitch",
  discovery: "questions",
  presentation: "solution",
  objection: "objections",
  negotiation: "proofs",
  closing: "pitch",
};
