# PLAN : Scénarios Pédagogiques Cohérents V2

**Objectif** : Rendre les sessions d'entraînement réalistes avec des produits complets, des concurrents, des preuves sociales, et une fin de conversation automatique.

**Décisions prises** :
- Champion V1 = upsell B2B entreprises (désactivé pour users normaux)
- V2 Skills/Cours = système principal
- Scripts pré-définis par skill + adaptation sectorielle sans API

---

## PROGRESSION DES PHASES

| Phase | Statut | Description |
|-------|--------|-------------|
| 1 | [x] Terminé | Structure données enrichie (ProductInfo, ProofElements, CompetitionInfo) |
| 2 | [x] Terminé | Détection fin conversation + redirect auto |
| 3 | [x] Terminé | Page rapport de session `/training/report/[id]` |
| 4 | [x] Terminé | Templates scénarios par skill (17 skills × 2-3 variants) - 40 templates créés |
| 5 | [x] Terminé | Adaptation sectorielle sans API |
| 6 | [x] Terminé | Désactiver Champion V1 → upsell B2B Enterprise |
| 7 | [x] Terminé | Mode vocal avancé (parseur annotations, émotions TTS, actions visuelles) |

---

## PHASE 1 : Structure de données enrichie

### Objectif
Ajouter au scénario toutes les informations nécessaires pour un vendeur réaliste.

### Nouveau schéma ScenarioComplet

```python
# backend/models.py - Ajouter ces modèles

class ProductInfo(Base):
    """Informations détaillées sur le produit à vendre."""
    __tablename__ = "product_infos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # Ex: "MarketAuto Pro"
    tagline: Mapped[str]  # Ex: "Automatisez 80% de vos tâches marketing"

    # COMMENT ÇA MARCHE (ce qui manque actuellement)
    how_it_works: Mapped[dict] = mapped_column(JSON)
    # {
    #   "summary": "Solution SaaS qui automatise...",
    #   "key_features": ["Emails automatiques", "Scoring leads", "Analytics"],
    #   "technical_requirements": "Navigateur web, connexion API CRM",
    #   "implementation_time": "2-5 jours selon complexité"
    # }

    # INTÉGRATIONS
    integrations: Mapped[list] = mapped_column(JSON)
    # ["Salesforce", "HubSpot", "Pipedrive", "Zapier", "API REST"]

    # SUPPORT & ONBOARDING
    support_included: Mapped[dict] = mapped_column(JSON)
    # {
    #   "onboarding": "Formation 2h incluse",
    #   "support": "Chat + Email 9h-18h",
    #   "documentation": "Base de connaissances complète",
    #   "csm": "Customer Success Manager dédié (plan Pro)"
    # }

    # PRICING
    pricing: Mapped[dict] = mapped_column(JSON)
    # {
    #   "model": "par_utilisateur",  # flat, par_utilisateur, usage
    #   "entry_price": "49€/mois",
    #   "popular_plan": "Pro à 149€/mois",
    #   "enterprise": "Sur devis",
    #   "engagement": "Mensuel ou annuel (-20%)",
    #   "free_trial": "14 jours sans CB"
    # }


class ProofElements(Base):
    """Preuves sociales et témoignages."""
    __tablename__ = "proof_elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product_infos.id"))

    # TÉMOIGNAGES CLIENTS
    testimonials: Mapped[list] = mapped_column(JSON)
    # [
    #   {
    #     "name": "Sophie Martin",
    #     "role": "Directrice Marketing",
    #     "company": "TechCorp (150 employés)",
    #     "quote": "On a doublé nos leads qualifiés en 3 mois",
    #     "result": "+120% de leads, -40% de temps admin"
    #   }
    # ]

    # ÉTUDES DE CAS
    case_studies: Mapped[list] = mapped_column(JSON)
    # [
    #   {
    #     "client": "LogiStart",
    #     "sector": "E-commerce",
    #     "problem": "Équipe marketing de 2 personnes débordée",
    #     "solution": "Automatisation des emails et nurturing",
    #     "results": {"leads": "+85%", "time_saved": "15h/semaine", "roi_months": 2}
    #   }
    # ]

    # STATISTIQUES
    stats: Mapped[dict] = mapped_column(JSON)
    # {
    #   "clients_count": "2000+ entreprises",
    #   "satisfaction": "4.8/5 sur G2",
    #   "nps": "72",
    #   "uptime": "99.9%"
    # }

    # CLIENTS NOTABLES (logos)
    notable_clients: Mapped[list] = mapped_column(JSON)
    # ["BlaBlaCar", "Doctolib", "ManoMano", "Qonto"]


class CompetitionInfo(Base):
    """Informations sur la concurrence."""
    __tablename__ = "competition_infos"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product_infos.id"))

    # CONCURRENTS PRINCIPAUX
    main_competitors: Mapped[list] = mapped_column(JSON)
    # [
    #   {
    #     "name": "HubSpot",
    #     "positioning": "Leader établi, très complet",
    #     "strengths": ["Écosystème complet", "Brand recognition"],
    #     "weaknesses": ["Prix élevé", "Complexe à configurer", "Support US"],
    #     "price_comparison": "2-3x plus cher à fonctionnalités égales"
    #   },
    #   {
    #     "name": "Brevo (ex-Sendinblue)",
    #     "positioning": "Alternative française accessible",
    #     "strengths": ["Prix attractif", "Made in France"],
    #     "weaknesses": ["Moins de fonctionnalités avancées", "Pas de CRM natif"],
    #     "price_comparison": "Similaire mais moins de features"
    #   }
    # ]

    # NOTRE DIFFÉRENCIATEUR
    our_differentiator: Mapped[str]
    # "Seule solution qui combine automation marketing ET IA prédictive
    #  à un prix PME. Setup en 2 jours vs 2 semaines chez les concurrents."

    # FACILITÉ DE MIGRATION
    switch_cost: Mapped[dict] = mapped_column(JSON)
    # {
    #   "migration_time": "1-2 jours",
    #   "data_import": "Import automatique depuis HubSpot, Mailchimp, etc.",
    #   "training_needed": "2h de formation suffisent",
    #   "risk": "Migration assistée gratuite, on récupère vos données"
    # }
```

### Fichiers à modifier

| Fichier | Action |
|---------|--------|
| `backend/models.py` | Ajouter ProductInfo, ProofElements, CompetitionInfo |
| `backend/schemas.py` | Ajouter schémas Pydantic correspondants |
| `backend/agents/content_agent/prompts.py` | Enrichir prompt avec nouvelle structure |

### Checklist Phase 1

- [x] Créer modèle `ProductInfo` dans models.py
- [x] Créer modèle `ProofElements` dans models.py
- [x] Créer modèle `CompetitionInfo` dans models.py
- [x] Créer les schémas Pydantic dans schemas.py
- [x] Mettre à jour `SCENARIO_GENERATION_PROMPT` dans prompts.py
- [ ] Tester la génération avec le nouveau format

---

## PHASE 2 : Détection fin de conversation + redirect

### Objectif
Terminer automatiquement la session quand l'utilisateur ET le prospect disent au revoir.

### Logique de détection

```python
# backend/services/training_service_v2.py

END_PATTERNS_FR = [
    # Formules de politesse
    "au revoir", "à bientôt", "bonne journée", "bonne fin de journée",
    "bonne continuation", "à la prochaine", "à très vite",
    # Remerciements de fin
    "merci pour votre temps", "merci de m'avoir reçu",
    "je vous laisse", "je ne vous retiens pas plus",
    # Anglais (au cas où)
    "goodbye", "bye", "see you", "take care"
]

END_PATTERNS_PROSPECT = [
    # Le prospect met fin
    "je dois vous laisser", "j'ai un autre appel",
    "on se rappelle", "envoyez-moi ça par email",
    "je reviendrai vers vous", "merci, au revoir",
    "bonne journée à vous aussi"
]

def detect_conversation_end(
    user_message: str,
    prospect_response: str,
    exchange_count: int,
    min_exchanges: int = 4
) -> tuple[bool, str]:
    """
    Détecte si la conversation est terminée.

    Returns:
        (is_ended, end_type)
        end_type: "mutual_goodbye" | "prospect_ended" | "user_ended" | None
    """
    if exchange_count < min_exchanges:
        return False, None

    user_lower = user_message.lower()
    prospect_lower = prospect_response.lower()

    user_said_bye = any(p in user_lower for p in END_PATTERNS_FR)
    prospect_said_bye = any(p in prospect_lower for p in END_PATTERNS_FR + END_PATTERNS_PROSPECT)

    if user_said_bye and prospect_said_bye:
        return True, "mutual_goodbye"
    elif prospect_said_bye and not user_said_bye:
        # Le prospect veut partir mais l'user n'a pas dit au revoir
        # On laisse l'user répondre une dernière fois
        return False, "prospect_ending"
    elif user_said_bye and not prospect_said_bye:
        # L'user dit au revoir, le prospect devrait répondre poliment
        return False, "user_ending"

    return False, None
```

### Modification de la réponse API

```python
# backend/api/routers/training.py ou learning.py

class SessionRespondResponse(BaseModel):
    # ... existant ...
    session_ended: bool = False
    end_type: str | None = None  # mutual_goodbye, prospect_ended, etc.
    redirect_url: str | None = None  # /training/report/{session_id}
```

### Frontend - Gestion de la fin

```typescript
// frontend/app/training/session/[id]/page.tsx

// Dans le handler de réponse
if (response.session_ended) {
  // Afficher un modal de fin
  setShowEndModal(true);

  // Après 3 secondes, rediriger vers le rapport
  setTimeout(() => {
    router.push(response.redirect_url || `/training/report/${sessionId}`);
  }, 3000);
}
```

### Checklist Phase 2

- [x] Ajouter constantes `END_PATTERNS_FR` et `END_PATTERNS_PROSPECT`
- [x] Créer fonction `detect_conversation_end()` dans training_service_v2.py
- [x] Appeler la fonction après chaque échange
- [x] Modifier le schéma de réponse pour inclure `session_ended`
- [x] Côté frontend: détecter `session_ended: true`
- [x] Afficher modal "Conversation terminée"
- [x] Implémenter redirect automatique vers `/training/report/[id]`
- [ ] Tester avec différentes formules de politesse

---

## PHASE 3 : Page rapport de session

### Objectif
Afficher un rapport complet et actionnable après chaque session.

### Route
`/training/report/[id]`

### Composants à créer

```
frontend/
├── app/training/report/[id]/
│   └── page.tsx              # Page principale
└── components/training/
    ├── SessionReport.tsx      # Container du rapport
    ├── ScoreOverview.tsx      # Score global + progression
    ├── ConversationReplay.tsx # Messages avec annotations
    ├── PatternAnalysis.tsx    # Points forts/faibles détectés
    ├── ObjectionReview.tsx    # Objections gérées vs ratées
    └── NextSteps.tsx          # Conseils + boutons d'action
```

### Structure du rapport

```typescript
interface SessionReport {
  // HEADER
  session_id: number;
  skill_name: string;
  sector_name: string;
  level: "easy" | "medium" | "expert";
  duration_seconds: number;
  completed_at: string;

  // SCORE GLOBAL
  final_score: number;  // 0-100
  final_gauge: number;  // 0-100
  starting_gauge: number;
  gauge_progression: number;  // final - start
  converted: boolean;

  // PATTERNS DÉTECTÉS
  positive_patterns: Array<{
    pattern: string;      // ex: "good_open_question"
    label: string;        // ex: "Bonne question ouverte"
    count: number;
    examples: string[];   // Extraits de la conversation
  }>;

  negative_patterns: Array<{
    pattern: string;
    label: string;
    count: number;
    examples: string[];
    advice: string;       // Conseil d'amélioration
  }>;

  // OBJECTIONS
  objections_handled: Array<{
    objection: string;
    response: string;
    quality: "good" | "average" | "poor";
    advice?: string;
  }>;

  hidden_objections: Array<{
    expressed: string;
    hidden: string;
    discovered: boolean;
    discovery_tip?: string;
  }>;

  // ÉVÉNEMENTS (si niveau medium/expert)
  events_triggered: Array<{
    type: string;
    handled: boolean;
    user_response?: string;
  }>;

  // BLOQUEURS
  conversion_blockers: string[];

  // CONSEILS PERSONNALISÉS
  personalized_tips: string[];

  // CONVERSATION COMPLÈTE
  messages: Array<{
    role: "user" | "prospect";
    content: string;
    gauge_after: number;
    patterns_detected: string[];
    timestamp: string;
  }>;
}
```

### Design du rapport

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Session terminée - [Skill Name]                         │
│  Secteur: Immobilier | Niveau: Intermédiaire | Durée: 8min  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    SCORE    │  │    JAUGE    │  │  CONVERTI?  │         │
│  │     72%     │  │   45 → 78   │  │     ✅      │         │
│  │             │  │    (+33)    │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ✅ POINTS FORTS (5)                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🎯 Bonne reformulation (x3)                             ││
│  │ 💬 Questions ouvertes pertinentes (x2)                  ││
│  │ 🤝 Empathie démontrée                                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ⚠️ POINTS À AMÉLIORER (2)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ❌ Interruption détectée                                ││
│  │    → "Attendez, laissez-moi finir..."                   ││
│  │    💡 Conseil: Attendez 2 secondes après que le         ││
│  │       prospect ait fini de parler                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  🔄 REPLAY CONVERSATION (cliquer pour déplier)              │
├─────────────────────────────────────────────────────────────┤
│  📝 CONSEILS POUR PROGRESSER                                │
│  • Pratiquez l'écoute active avant de répondre             │
│  • Utilisez plus de silences stratégiques                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  🔄 Refaire  │  │  ➡️ Suivant  │  │  📚 Retour   │      │
│  │  ce scénario │  │   scénario   │  │  aux cours   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Checklist Phase 3

- [x] Créer endpoint GET `/voice/session/{id}/report`
- [x] Calculer les stats dans le backend (patterns, objections, etc.)
- [x] Créer `frontend/app/training/report/[id]/page.tsx`
- [x] Créer composant `ScoreOverview` (intégré dans page.tsx)
- [x] Créer composant `PatternAnalysis` (intégré dans page.tsx)
- [x] Créer composant `ConversationReplay` (intégré dans page.tsx)
- [x] Créer composant `NextSteps` (intégré dans page.tsx)
- [x] Implémenter les boutons d'action (refaire, suivant, retour)
- [ ] Tester le rapport complet en conditions réelles

---

## PHASE 4 : Templates scénarios par skill

### Objectif
Créer des scénarios pré-définis riches pour chaque skill, éliminant le besoin d'appels API pour la génération.

### Structure des fichiers

```
backend/
└── data/
    └── scenario_templates/
        ├── _products/           # Produits réutilisables
        │   ├── saas_marketing.json
        │   ├── crm_pme.json
        │   ├── rh_solution.json
        │   └── ...
        ├── preparation_ciblage/
        │   ├── template_1.json
        │   └── template_2.json
        ├── script_accroche/
        │   ├── template_1.json
        │   └── template_2.json
        └── ... (un dossier par skill)
```

### Mapping Skills → Scénarios

| Skill | Niveau | Contexte type | Produit type | Difficulté prospect |
|-------|--------|---------------|--------------|---------------------|
| preparation_ciblage | easy | Premier contact | SaaS générique | Curieux |
| script_accroche | easy | Cold call | CRM PME | Occupé |
| cold_calling | easy | Barrage secrétaire | Solution RH | Méfiant |
| ecoute_active | easy | Découverte | Outil analytics | Bavard |
| decouverte_compir | medium | RDV qualification | ERP PME | Réservé |
| checklist_bebedc | medium | RDV avancé | Solution cybersec | Evasif |
| qualification_columbo | medium | Qualification | Cloud/Infra | Pressé |
| cartographie_decideurs | medium | Multi-interlocuteurs | Logiciel enterprise | Politique |
| profils_psychologiques | medium | Adaptation | Varie | 6 profils |
| argumentation_bac | medium | Présentation | Solution métier | Sceptique |
| demonstration_produit | medium | Démo | SaaS | Impatient |
| objections_cnz | expert | Objections | Varie | Agressif |
| negociation | expert | Négociation prix | Varie | Dur en affaires |
| closing_ponts_brules | expert | Closing | Varie | Hésitant |
| relance_suivi | expert | Relance | Varie | Ghosteur |
| recommandation | expert | Post-vente | Varie | Satisfait |
| situations_difficiles | expert | Crise | Varie | En colère |

### Structure d'un template

```json
{
  "template_id": "cold_calling_1",
  "skill_slug": "cold_calling",
  "name": "Barrage Secrétaire - PME Tech",
  "description": "Passer le barrage d'une assistante pour joindre le DG",

  "product": {
    "name": "CloudSec Pro",
    "tagline": "La cybersécurité simple pour les PME",
    "how_it_works": {
      "summary": "Solution de sécurité cloud tout-en-un: antivirus, firewall, backup automatique, formation équipe. Installation en 30 minutes, géré depuis un tableau de bord unique.",
      "key_features": [
        "Protection endpoint pour tous les postes",
        "Backup cloud automatique chiffré",
        "Détection ransomware en temps réel",
        "Formation phishing pour les employés"
      ],
      "technical_requirements": "Windows/Mac, 2Go RAM minimum, connexion internet",
      "implementation_time": "30 minutes à 2 heures selon nombre de postes"
    },
    "integrations": ["Microsoft 365", "Google Workspace", "Slack", "Active Directory"],
    "support": {
      "onboarding": "Installation assistée gratuite",
      "support": "Support FR 24/7 par téléphone",
      "sla": "Réponse en moins d'1h pour incidents critiques"
    },
    "pricing": {
      "model": "par_poste",
      "entry_price": "8€/poste/mois",
      "popular_plan": "Pro à 15€/poste/mois (inclut backup)",
      "minimum": "5 postes",
      "engagement": "Mensuel sans engagement ou annuel -20%"
    }
  },

  "proof": {
    "testimonials": [
      {
        "name": "Marc Dubois",
        "role": "DG",
        "company": "InnoTech (45 employés)",
        "quote": "On a bloqué une attaque ransomware le mois dernier. CloudSec nous a sauvés.",
        "result": "0 incident en 2 ans, équipe formée au phishing"
      }
    ],
    "case_studies": [
      {
        "client": "Cabinet Leroy Avocats",
        "problem": "Données clients sensibles, peur du piratage, pas d'équipe IT",
        "solution": "CloudSec Pro + formation équipe de 12 personnes",
        "results": {
          "security_score": "de 35 à 92/100",
          "incidents": "0 en 18 mois",
          "time_saved": "2h/semaine (plus de gestion antivirus)"
        }
      }
    ],
    "stats": {
      "clients": "1200+ PME en France",
      "satisfaction": "4.7/5",
      "attacks_blocked": "50 000+ menaces bloquées/mois"
    },
    "notable_clients": ["Alan", "Swile", "Payfit", "Spendesk"]
  },

  "competition": {
    "main_competitors": [
      {
        "name": "Norton Business",
        "positioning": "Grand public adapté aux entreprises",
        "strengths": ["Marque connue", "Prix bas"],
        "weaknesses": ["Pas de support dédié PME", "Pas de backup intégré", "Interface datée"],
        "price_comparison": "Moins cher mais beaucoup moins complet"
      },
      {
        "name": "CrowdStrike",
        "positioning": "Leader enterprise",
        "strengths": ["Technologie top", "Réputation"],
        "weaknesses": ["Prix prohibitif pour PME", "Complexe à gérer", "Minimum 100 postes"],
        "price_comparison": "5x plus cher, surdimensionné pour PME"
      }
    ],
    "our_differentiator": "Seule solution tout-en-un (protection + backup + formation) pensée pour les PME sans équipe IT. Prix PME, support enterprise.",
    "switch_cost": {
      "migration_time": "30 minutes",
      "difficulty": "Très simple, on désinstalle l'ancien et on installe le nouveau",
      "risk": "Aucune interruption de service"
    }
  },

  "prospect": {
    "gatekeeper": {
      "name": "Nathalie",
      "role": "Assistante de direction",
      "personality": "protective",
      "typical_responses": [
        "M. Martin est en réunion",
        "De la part de qui?",
        "C'est à quel sujet?",
        "Envoyez un email, il vous rappellera",
        "On a déjà un prestataire informatique"
      ]
    },
    "decision_maker": {
      "name": "Philippe Martin",
      "role": "Directeur Général",
      "company": "LogiPro",
      "company_size": "35 employés",
      "sector": "Logistique",
      "personality": "busy",
      "current_situation": "Utilise un antivirus grand public, pas de backup formalisé",
      "pain_points": [
        "A eu une frayeur avec un email de phishing le mois dernier",
        "Données clients sensibles (contrats transporteurs)",
        "Pas d'équipe IT, c'est lui qui gère 'l'informatique'"
      ],
      "hidden_need": "Veut se protéger mais ne veut pas perdre de temps à gérer ça"
    }
  },

  "scenario_flow": {
    "opening": {
      "gatekeeper_first_response": "LogiPro, bonjour?",
      "context": "Vous appelez pour la première fois, vous avez trouvé le contact sur LinkedIn"
    },
    "objectives": [
      "Passer le barrage de l'assistante",
      "Obtenir le décideur en ligne OU un créneau de rappel",
      "Si décideur en ligne: qualifier l'opportunité (TAI)"
    ],
    "success_criteria": [
      "RDV téléphonique fixé",
      "OU: décideur qualifié avec intérêt confirmé",
      "ET: pas d'agressivité, relation préservée avec l'assistante"
    ],
    "difficulty_modifiers": {
      "easy": {
        "gatekeeper_resistance": "low",
        "dm_availability": "Après 2-3 tentatives, l'assistante passe l'appel"
      },
      "medium": {
        "gatekeeper_resistance": "medium",
        "dm_availability": "Il faut une vraie raison pour être passé"
      },
      "expert": {
        "gatekeeper_resistance": "high",
        "dm_availability": "L'assistante protège farouchement, il faut être créatif"
      }
    }
  },

  "conversation_rules": {
    "end_triggers": ["au revoir", "merci, bonne journée", "je vous laisse"],
    "min_exchanges": 5,
    "max_exchanges": 15,
    "auto_end_enabled": true
  }
}
```

### Checklist Phase 4

Pour chaque skill (17 total), créer 2-3 templates :

**Niveau EASY (4 skills)** ✅ TERMINÉ
- [x] preparation_ciblage : 2 templates
- [x] script_accroche : 2 templates
- [x] cold_calling : 3 templates (barrage, objection rapide, succès)
- [x] ecoute_active : 2 templates

**Niveau MEDIUM (7 skills)** ✅ TERMINÉ
- [x] decouverte_compir : 2 templates
- [x] checklist_bebedc : 2 templates
- [x] qualification_columbo : 2 templates
- [x] cartographie_decideurs : 2 templates (avec organigramme)
- [x] profils_psychologiques : 6 templates (1 par profil SÉDAIÉ)
- [x] argumentation_bac : 2 templates
- [x] demonstration_produit : 2 templates

**Niveau EXPERT (6 skills)** ✅ TERMINÉ
- [x] objections_cnz : 3 templates (prix, timing, concurrent)
- [x] negociation : 2 templates
- [x] closing_ponts_brules : 2 templates
- [x] relance_suivi : 2 templates
- [x] recommandation : 2 templates
- [x] situations_difficiles : 3 templates (agressif, erreur, désabonnement)

**Infrastructure** ✅ TERMINÉ
- [x] Créer dossier `backend/data/scenario_templates/`
- [x] Créer fonction `load_scenario_template(skill_slug, variant=None)`
- [x] Créer fonction `adapt_template_to_sector(template, sector)`
- [x] Intégrer dans `training_service_v2.py`
- [ ] Tests unitaires

---

## PHASE 5 : Adaptation sectorielle sans API

### Objectif
Adapter les templates génériques au secteur choisi par l'utilisateur, sans appel API.

### Logique d'adaptation

```python
# backend/services/scenario_adapter.py

from copy import deepcopy
import random

def adapt_scenario_to_sector(
    base_template: dict,
    sector: Sector,
    difficulty: str
) -> dict:
    """
    Adapte un template de scénario au secteur choisi.
    Aucun appel API - tout est basé sur les données du secteur.
    """
    scenario = deepcopy(base_template)

    # 1. Choisir un persona aléatoire du secteur
    if sector.prospect_personas:
        persona = random.choice(sector.prospect_personas)
        scenario["prospect"]["name"] = persona.get("name", scenario["prospect"]["name"])
        scenario["prospect"]["role"] = persona.get("role", scenario["prospect"]["role"])
        scenario["prospect"]["personality"] = persona.get("personality", "neutral")
        scenario["prospect"]["psychology"] = persona.get("psychology", {})

    # 2. Adapter le vocabulaire
    if sector.vocabulary:
        scenario["sector_vocabulary"] = sector.vocabulary

    # 3. Injecter les objections typiques du secteur
    if sector.typical_objections:
        scenario["possible_objections"] = sector.typical_objections

    # 4. Adapter les objections cachées du persona
    if persona and persona.get("hidden_objections"):
        scenario["hidden_objections"] = persona["hidden_objections"]

    # 5. Adapter les triggers de conversion
    if persona and persona.get("conversion_triggers"):
        scenario["conversion_triggers"] = persona["conversion_triggers"]

    # 6. Utiliser le prompt contextuel du secteur
    scenario["agent_context_prompt"] = sector.agent_context_prompt

    # 7. Appliquer les adaptations de scénario du secteur
    if sector.scenario_adaptations:
        if difficulty == "expert" and sector.scenario_adaptations.get("prospect_difficile"):
            scenario["difficulty_context"] = sector.scenario_adaptations["prospect_difficile"]

    return scenario
```

### Mapping secteur → produit par défaut

```python
SECTOR_DEFAULT_PRODUCTS = {
    "immo": {
        "name": "Mandat de vente",
        "type": "service",
        "value_proposition": "Accompagnement complet pour vendre au meilleur prix"
    },
    "b2b_saas": {
        "name": "Solution SaaS",
        "type": "subscription",
        "value_proposition": "Automatisation et gain de productivité"
    },
    "assurance": {
        "name": "Contrat d'assurance",
        "type": "subscription",
        "value_proposition": "Protection adaptée à votre situation"
    },
    "auto": {
        "name": "Véhicule",
        "type": "one_time",
        "value_proposition": "Le véhicule adapté à vos besoins et budget"
    },
    "energie": {
        "name": "Travaux de rénovation",
        "type": "one_time",
        "value_proposition": "Économies d'énergie et confort amélioré"
    },
    "generic": {
        "name": "Solution",
        "type": "generic",
        "value_proposition": "Réponse à votre problème métier"
    }
}
```

### Checklist Phase 5

- [x] Créer `backend/services/scenario_adapter.py`
- [x] Implémenter `adapt_scenario_to_sector()`
- [x] Créer mapping `SECTOR_DEFAULT_PRODUCTS`
- [x] Intégrer dans le flow de création de session
- [x] Tester avec chaque secteur
- [x] Vérifier que les objections cachées sont correctement injectées

---

## PHASE 6 : Désactiver Champion V1 (upsell B2B)

### Objectif
Le système Champion (analyse de vidéos) devient un upsell pour les entreprises, pas le système par défaut.

### Changements à effectuer

```python
# backend/api/routers/training.py

# Ajouter un check au début des endpoints Champion
async def check_champion_access(user: User, db: AsyncSession):
    """Vérifie si l'utilisateur a accès aux fonctionnalités Champion."""
    # Champion = réservé aux plans Enterprise ou feature flag
    if user.subscription_plan != "enterprise":
        raise HTTPException(
            status_code=403,
            detail="La fonctionnalité Champion est réservée aux comptes Enterprise. "
                   "Utilisez les sessions Skills pour vous entraîner."
        )
```

### Frontend - Masquer/Adapter l'UI

```typescript
// Masquer les options Champion pour les non-enterprise
const showChampionFeatures = user.subscription_plan === 'enterprise';
```

### Points d'attention

- [ ] Identifier tous les endpoints qui utilisent Champion/TrainingSession
- [ ] Ajouter le check d'accès Enterprise
- [ ] Modifier le frontend pour masquer les options Champion
- [ ] Ajouter un CTA "Découvrir Champion pour votre équipe" (upsell)
- [ ] Créer une page /enterprise avec les features Champion
- [ ] Migrer les utilisateurs existants ? (ou grandfather clause)

### Checklist Phase 6

- [x] Lister tous les endpoints Champion
- [x] Créer decorator/middleware `@requires_enterprise`
- [x] Appliquer à tous les endpoints Champion
- [x] Modifier navigation frontend
- [x] Créer page/section upsell Enterprise
- [x] Tester que les users normaux n'ont plus accès
- [x] Tester que les Enterprise ont toujours accès

---

## NOTES DE SESSION

### Session 1 (date: _______)
- [ ] Phase commencée: ___
- [ ] Avancement: ___
- [ ] Bloqueurs: ___

### Session 2 (date: _______)
- [ ] Phase commencée: ___
- [ ] Avancement: ___
- [ ] Bloqueurs: ___

(Ajouter une section par session de travail)

---

## DÉCISIONS PRISES

| Question | Décision |
|----------|----------|
| **Produits par secteur** | Générique (Easy) → Adapté (Medium) → Spécifique (Expert) |
| **Migration données** | Garder les 2 modèles (TrainingSession + VoiceTrainingSession), restreindre V1 à Enterprise |
| **IA locale** | Plus tard, quand les templates seront stables |
| **Fichiers training.py** | Garder pour l'instant, renommer en Phase 6 (champion.py) |

---

## PHASE 7 : Mode Vocal Avancé (Future)

### Problème actuel

Le TTS actuel ne "joue" pas les émotions. Les annotations comme `(soupir)` ou `(agacée)` sont juste lues comme du texte ou affichées entre parenthèses. Ce n'est pas réaliste.

**Exemple du problème** :
```
Texte généré: "(soupir et agacée) La société c'est TechStar, pas Textar."
Ce que le TTS fait: Lit "(soupir et agacée)" littéralement
Ce qu'on voudrait: Un vrai soupir audio + ton agacé
```

### Solutions possibles

| Solution | Complexité | Qualité | Coût |
|----------|------------|---------|------|
| **ElevenLabs Voice Design** | Moyenne | Haute | $$$ |
| **Azure SSML avancé** | Moyenne | Moyenne | $$ |
| **Sons pré-enregistrés** | Facile | Variable | $ |
| **IA vocale locale (Bark, Tortoise)** | Haute | Variable | Gratuit |

### Architecture cible (future)

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIO PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Texte + Annotations                                        │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PARSEUR D'ANNOTATIONS                                │   │
│  │ "(soupir)" → {type: "sound", file: "sigh_01.mp3"}   │   │
│  │ "(agacée)" → {type: "emotion", style: "annoyed"}    │   │
│  └─────────────────────────────────────────────────────┘   │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ASSEMBLEUR AUDIO                                     │   │
│  │ 1. Jouer son "sigh_01.mp3"                          │   │
│  │ 2. Générer TTS avec style "annoyed"                 │   │
│  │ 3. Mixer les deux                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│       ↓                                                     │
│  Audio final réaliste                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Structure voice_config complète dans les templates

```json
{
  "voice_config": {

    "prospect_voice_profile": {
      "gender": "female",
      "age_range": "40-50",
      "accent": "parisien",
      "base_tone": "professional",
      "speaking_pace": "medium",
      "voice_id": "elevenlabs_sophie"
    },

    "emotional_voice_mapping": {
      "hostile": {
        "tone": "cold",
        "pace": "fast",
        "volume": "loud",
        "pitch": "low",
        "pauses": "short",
        "sighs": true,
        "interruption_probability": 0.8,
        "tts_style": "angry"
      },
      "skeptical": {
        "tone": "doubtful",
        "pace": "slow",
        "volume": "normal",
        "pitch": "rising_at_end",
        "pauses": "long_before_response",
        "hmm_probability": 0.5,
        "tts_style": "unfriendly"
      },
      "neutral": {
        "tone": "professional",
        "pace": "medium",
        "volume": "normal",
        "pitch": "stable",
        "pauses": "normal",
        "tts_style": "neutral"
      },
      "interested": {
        "tone": "warm",
        "pace": "engaged",
        "volume": "slightly_higher",
        "pitch": "varied",
        "pauses": "short",
        "laughs_probability": 0.2,
        "tts_style": "friendly"
      },
      "ready_to_buy": {
        "tone": "enthusiastic",
        "pace": "fast",
        "volume": "higher",
        "pitch": "high",
        "pauses": "minimal",
        "tts_style": "excited"
      }
    },

    "non_verbal_sounds": {
      "sigh": {
        "files": ["sigh_light.mp3", "sigh_heavy.mp3", "sigh_annoyed.mp3"],
        "trigger_gauge_below": 40
      },
      "hmm": {
        "files": ["hmm_thinking.mp3", "hmm_doubtful.mp3"],
        "trigger": "before_objection"
      },
      "laugh": {
        "files": ["laugh_polite.mp3", "laugh_genuine.mp3"],
        "trigger_gauge_above": 70
      },
      "throat_clear": {
        "files": ["throat_clear.mp3"],
        "trigger": "before_important_statement"
      },
      "typing": {
        "files": ["keyboard_typing.mp3"],
        "trigger": "distraction_event"
      },
      "phone_buzz": {
        "files": ["phone_notification.mp3"],
        "trigger": "interruption_event"
      }
    },

    "verbal_tics": {
      "fillers": ["euh", "donc", "voilà", "bon"],
      "thinking_sounds": ["hmm", "ah"],
      "agreement_sounds": ["mm-hmm", "d'accord", "ok"],
      "doubt_sounds": ["mouais", "bof", "pfff"]
    },

    "interruption_patterns": {
      "when_gauge_below_30": {
        "probability": 0.7,
        "triggers": ["pitch", "long_sentence", "product_name"],
        "phrases": [
          "Attendez, attendez...",
          "Oui mais...",
          "Non mais écoutez...",
          "Je vous arrête tout de suite"
        ]
      },
      "when_gauge_above_70": {
        "probability": 0.1,
        "style": "eager_to_continue"
      }
    },

    "silence_reactions": {
      "after_user_silence_3s": {
        "sounds": ["throat_clear"],
        "phrases": ["Vous êtes toujours là ?", "Allô ?"]
      },
      "after_user_silence_5s": {
        "sounds": ["sigh_annoyed"],
        "phrases": ["Bon, je n'ai pas que ça à faire...", "Vous réfléchissez ?"]
      }
    },

    "background_ambiance": {
      "environment": "office",
      "base_sounds": ["office_ambiance_low.mp3"],
      "random_events": [
        {
          "sound": "phone_ring_distant.mp3",
          "probability_per_minute": 0.1
        },
        {
          "sound": "door_close.mp3",
          "probability_per_minute": 0.05
        }
      ]
    },

    "emotional_transitions": {
      "gauge_drop_sudden": {
        "sound_before": "sigh_heavy",
        "voice_change": "colder",
        "pace_change": "slower"
      },
      "gauge_rise_10_points": {
        "voice_change": "warmer",
        "remove_doubt_sounds": true,
        "pace_change": "more_engaged"
      },
      "objection_moment": {
        "sound_before": "hmm_doubtful",
        "voice_change": "firmer",
        "pace": "deliberate"
      }
    },

    "turn_taking_rules": {
      "max_user_speech_seconds": 45,
      "warning_at_30s": {
        "sound": "paper_shuffle",
        "visual": "*le prospect commence à s'agiter*"
      },
      "interrupt_at_45s": {
        "phrase": "D'accord, d'accord, j'ai compris l'idée...",
        "tone": "impatient"
      },
      "natural_response_delay_ms": [800, 2000],
      "thinking_delay_for_complex_question_ms": [2000, 4000]
    }
  }
}
```

### Implémentation par phases

**Phase 7a - Quick Win (sans infra complexe)** :
- [ ] Créer bibliothèque de sons (soupirs, hmm, rires, etc.)
- [ ] Parser les annotations `(soupir)` et les remplacer par lecture audio
- [ ] Insérer les sons AVANT le texte TTS
- [ ] Résultat: `[sigh.mp3] + [TTS du texte]`

**Phase 7b - Émotions TTS (si ElevenLabs/Azure)** :
- [ ] Utiliser les paramètres de style ElevenLabs (stability, similarity_boost)
- [ ] Mapper les humeurs (hostile, interested) vers des styles TTS
- [ ] Tester avec différentes configurations

**Phase 7c - Pipeline complet (avancé)** :
- [ ] Créer le parseur d'annotations
- [ ] Créer l'assembleur audio (mixage sons + TTS)
- [ ] Gérer les transitions fluides
- [ ] Ambiance de fond

### Fichiers de sons nécessaires

```
backend/
└── audio/
    └── voice_effects/
        ├── sighs/
        │   ├── sigh_light.mp3
        │   ├── sigh_heavy.mp3
        │   └── sigh_annoyed.mp3
        ├── reactions/
        │   ├── hmm_thinking.mp3
        │   ├── hmm_doubtful.mp3
        │   ├── laugh_polite.mp3
        │   └── throat_clear.mp3
        ├── interruptions/
        │   ├── wait_wait.mp3
        │   └── let_me_finish.mp3
        └── ambiance/
            ├── office_quiet.mp3
            ├── phone_ring_distant.mp3
            └── keyboard_typing.mp3
```

### Checklist Phase 7

**7a - Sons basiques** :
- [x] Créer structure dossiers `audio/voice_effects/` (sighs, reactions, interruptions, ambiance)
- [x] Créer fonction `parse_annotations(text)` - parse (soupir), (agacée), etc.
- [x] Créer fonction `clean_text_for_tts(text)` - retire les annotations
- [x] Créer fonction `prepare_tts_response()` - prépare tout pour le TTS
- [x] Intégrer dans `training_service_v2.py`
- [ ] Enregistrer/sourcer les fichiers audio réels (MP3)

**7b - Émotions TTS** :
- [x] Mapping humeur → paramètres TTS (stability, similarity_boost, style)
- [x] 11 émotions mappées: angry, annoyed, cold, skeptical, impatient, bored, neutral, interested, amused, friendly, enthusiastic
- [x] Ajustements dynamiques basés sur la jauge
- [x] Intégrer dans l'appel `voice_service.text_to_speech()`

**7c - Sons réels (Future - amélioration immersion)** :
- [ ] Sourcer/créer fichiers MP3 (~10 fichiers) :
  - `sighs/`: sigh_light.mp3, sigh_heavy.mp3, sigh_annoyed.mp3
  - `reactions/`: hmm_thinking.mp3, hmm_doubtful.mp3, laugh_polite.mp3, throat_clear.mp3
  - `interruptions/`: wait_wait.mp3
- [ ] Frontend : jouer `sounds_before[]` AVANT l'audio TTS (Web Audio API)
  - Avantage : latence perçue réduite (son joue pendant génération TTS)
- [ ] Optionnel futur : ambiance de fond (office_quiet.mp3)

**Note** : Les actions visuelles (prend des notes, fronce les sourcils) sont parsées mais non utilisées
car le prospect n'est pas visible. Le parsing reste actif (coût nul) au cas où on voudrait
afficher des indices textuels enrichis plus tard.

---

## NOTES DE SESSION

### Session 1 (date: 2026-01-02)
- [x] Phase commencée: Planification
- [x] Avancement: PLAN_SCENARIOS.md créé avec 7 phases
- [x] Bloqueurs: Aucun

### Session 2 (date: 2026-01-02)
- [x] Phase commencée: Phase 2 (Détection fin conversation)
- [x] Avancement: Implémentation complète
  - Backend: `detect_conversation_end()` + `END_PATTERNS_FR/PROSPECT`
  - WebSocket: Messages `session_ended`, `end_type`, `redirect_url`
  - Frontend: `ConversationEndModal.tsx` + auto-redirect 3s
- [x] Bloqueurs: Aucun

### Session 3 (date: 2026-01-02)
- [x] Phase commencée: Phase 3 (Page rapport de session)
- [x] Avancement: Implémentation complète
  - Backend: `get_session_report()` dans TrainingServiceV2 + endpoint `/voice/session/{id}/report`
  - Agrégation patterns avec comptage et exemples
  - Messages annotés avec gauge_impact et patterns_detected
  - Conseils personnalisés générés
  - Frontend: `/training/report/[id]/page.tsx` avec composants intégrés
    - ScoreOverview: Score, jauge, conversion
    - PatternAnalysis: Points forts/faibles avec détails
    - ConversationReplay: Messages avec annotations
    - NextSteps: Conseils et boutons d'action
- [x] Bloqueurs: Aucun

### Session 4 (date: 2026-01-02)
- [x] Phase commencée: Phase 4 (Templates scénarios par skill)
- [x] Avancement: Niveau EASY terminé + Infrastructure
  - Créé `backend/services/scenario_loader.py` avec:
    - `load_scenario_template(skill_slug, variant, difficulty)`
    - `adapt_template_to_sector(template, sector, difficulty)`
    - `convert_template_to_scenario(template)`
    - `list_available_templates()`, `get_template_count()`
  - Créé 3 produits réutilisables dans `_products/`:
    - `saas_marketing.json`, `crm_pme.json`, `cybersec_pme.json`
  - Créé 9 templates pour les 4 skills EASY:
    - preparation_ciblage: 2 templates
    - script_accroche: 2 templates
    - cold_calling: 3 templates (barrage, objection rapide, succès)
    - ecoute_active: 2 templates
  - Intégré le loader dans `training_service_v2.py` (priorité templates, fallback API)
- [x] Bloqueurs: Aucun

### Session 5 (date: 2026-01-03)
- [x] Phase commencée: Phase 4 (Templates scénarios par skill - suite)
- [x] Avancement: Niveau MEDIUM terminé (17 templates)
  - decouverte_compir: 2 templates (Dir Commercial PME, DRH en transformation)
  - checklist_bebedc: 2 templates (Projet cybersec PME, Projet ERP industriel)
  - qualification_columbo: 2 templates (Prospect pressé, Prospect méfiant)
  - cartographie_decideurs: 2 templates (Projet multi-décideurs ETI, Groupe familial)
  - profils_psychologiques: 6 templates (Sécuritaire, Économe, Dominant, Affectif, Innovateur, Expressif)
  - argumentation_bac: 2 templates (Solution RH sceptique, SaaS devant comité)
  - demonstration_produit: 2 templates (Prospect impatient, Audience technique)
- [x] Bloqueurs: Aucun

### Session 6 (date: 2026-01-03)
- [x] Phase commencée: Phase 4 (Templates scénarios par skill - EXPERT)
- [x] Avancement: Niveau EXPERT terminé (14 templates)
  - objections_cnz: 3 templates (prix, timing, concurrent)
    - Méthodologie CNZ (Creuser-Neutraliser-Zoomer)
    - Objection prix avec DAF dur en affaires
    - Objection timing avec DSI procrastinateur
    - Objection concurrent avec fidélité au fournisseur
  - negociation: 2 templates
    - Demande de remise agressive 30% (acheteur pro)
    - Négociation multi-enjeux (prix + délai + périmètre + conditions)
  - closing_ponts_brules: 2 templates
    - Prospect hésitant individuel
    - Comité de décision multi-personnes
  - relance_suivi: 2 templates
    - Prospect qui ghost après bonne démo
    - Réactivation ancien prospect après 6 mois
  - recommandation: 2 templates
    - Demander références à client satisfait
    - Introduction à cible stratégique spécifique
  - situations_difficiles: 3 templates
    - Client agressif en colère (incident service)
    - Annoncer proactivement une erreur
    - Demande de résiliation (rétention)
- [x] Total templates Phase 4: 40 templates (9 easy + 17 medium + 14 expert)
- [x] Bloqueurs: Aucun

### Session 7 (date: 2026-01-03)
- [x] Phase commencée: Phase 5 (Adaptation sectorielle sans API)
- [x] Avancement: Implémentation complète
  - Créé `backend/services/scenario_adapter.py` avec:
    - `adapt_scenario_to_sector(template, sector_slug, difficulty)` - fonction d'adaptation enrichie
    - `SECTOR_DEFAULT_PRODUCTS` - mapping des 6 produits par défaut (immo, b2b_saas, assurance, auto, energie, generic)
    - `get_sector_data()`, `get_sector_objections()`, `get_sector_personas()`, `get_sector_vocabulary()`
    - `list_available_sectors()` - liste tous les secteurs disponibles
  - L'adaptation injecte:
    - Persona aléatoire du secteur avec psychologie complète
    - Objections cachées du persona (1-3 selon difficulté)
    - Vocabulaire sectoriel (jusqu'à 18 termes)
    - Objections typiques du secteur
    - Triggers de conversion du persona
    - Prompt contextuel pour l'agent
    - Produit par défaut si non défini
    - Contexte marché du secteur
  - Intégré dans `training_service_v2.py` (create_session)
  - Tests validés: 6 secteurs, 18 personas, adaptation dynamique
- [x] Bloqueurs: Aucun

### Session 8 (date: 2026-01-03)
- [x] Phase commencée: Phase 6 (Désactiver Champion V1 → upsell B2B Enterprise)
- [x] Avancement: Implémentation complète
  - **Backend:**
    - Créé dépendance `require_enterprise_access` dans `api/routers/auth.py`
    - Retourne 403 avec message d'upsell pour non-Enterprise
    - Appliqué à tous les endpoints Champion V1:
      - `champions.py`: `/upload`, `/analyze/{id}`, `/champions`, `/champions/{id}`, `DELETE /champions/{id}`
      - `training.py`: `/scenarios/{champion_id}`, `/training/start`, `/training/respond`, `/training/end`, `/training/sessions`
    - Les endpoints V2 (`/voice/*`) restent accessibles aux premium/trial
  - **Frontend:**
    - Modifié Header: ajout `enterpriseOnly: true` pour le lien Champion
    - Logique de filtrage: Enterprise-only masqué pour non-Enterprise
    - Créé page `/enterprise` avec:
      - Présentation des fonctionnalités Champion (analyse vidéo, extraction patterns, clonage style)
      - Avantages Enterprise (formation équipe, analytics, sécurité, support dédié)
      - Section pricing avec liste des features
      - CTAs vers demande de démo/devis
    - Modifié page `/upload`: blocage non-Enterprise avec CTA vers `/enterprise`
  - Tests: build frontend validé, imports backend validés
- [x] Bloqueurs: Aucun

### Session 9 (date: 2026-01-03)
- [x] Phase commencée: Phase 1 (Structure données enrichie)
- [x] Avancement: Implémentation complète
  - **Backend models.py:**
    - Créé modèle `ProductInfo` avec champs: slug, name, tagline, category, how_it_works (JSON), integrations (JSON), support_included (JSON), pricing (JSON)
    - Créé modèle `ProofElements` avec champs: testimonials (JSON), case_studies (JSON), stats (JSON), notable_clients (JSON)
    - Créé modèle `CompetitionInfo` avec champs: main_competitors (JSON), our_differentiator, switch_cost (JSON)
    - Relations: ProductInfo ↔ ProofElements, ProductInfo ↔ CompetitionInfo
  - **Backend schemas.py:**
    - Créé schémas Pydantic: HowItWorksSchema, SupportSchema, PricingSchema, ProductInfoCreate/Response
    - Créé schémas: TestimonialSchema, CaseStudySchema, StatsSchema, ProofElementsCreate/Response
    - Créé schémas: CompetitorSchema, SwitchCostSchema, CompetitionInfoCreate/Response
    - Créé EnrichedScenarioData pour combiner product + proof + competition
    - Créé ProductInfoWithRelations pour l'API avec données associées
  - **Backend prompts.py:**
    - Enrichi `SCENARIO_GENERATION_PROMPT` avec structure complète:
      - Prospect avec company_size, sector, current_situation
      - Product avec how_it_works, integrations, support, pricing
      - Proof avec testimonials, case_studies, stats, notable_clients
      - Competition avec main_competitors, our_differentiator, switch_cost
      - Ajouté conversation_rules pour auto-end
- [x] Bloqueurs: Aucun
- [ ] Reste à faire: Tester la génération avec le nouveau format

### Session 10 (date: 2026-01-03)
- [x] Phase commencée: Phase 7 (Mode vocal avancé)
- [x] Avancement: Implémentation 7a + 7b complète
  - **Structure dossiers:**
    - Créé `backend/audio/voice_effects/` avec sous-dossiers: sighs, reactions, interruptions, ambiance
  - **Nouveau service `services/voice_effects.py`:**
    - `VoiceAnnotation` dataclass pour les annotations parsées
    - `TTSSettings` dataclass avec stability, similarity_boost, style
    - `parse_annotations(text)` - détecte 40+ patterns (soupir, agacée, hmm, rire, etc.)
    - `clean_text_for_tts(text)` - retire toutes les annotations pour le TTS
    - `extract_primary_emotion(text)` - extrait l'émotion principale
    - `extract_sounds(text)` - liste les sons à jouer
    - `extract_actions(text)` - liste les actions visuelles (prend des notes, fronce les sourcils)
    - `get_tts_settings(mood, emotion, gauge)` - paramètres ElevenLabs dynamiques
    - `prepare_tts_response(text, mood, gauge)` - point d'entrée principal
    - `get_default_voice_config()` - config complète pour templates
  - **Mapping émotions → TTS (11 émotions):**
    - angry: stability=0.3, similarity=0.8, style=0.7
    - annoyed: stability=0.4, similarity=0.75, style=0.5
    - cold: stability=0.7, similarity=0.6, style=0.3
    - skeptical/impatient/bored: variations selon intensité
    - neutral: stability=0.5, similarity=0.75, style=0.0
    - interested/amused/friendly/enthusiastic: plus naturels
  - **Intégration `training_service_v2.py`:**
    - Import `voice_effects_service`
    - `create_session()`: utilise `prepare_tts_response()` pour l'ouverture
    - `process_user_message()`: utilise `prepare_tts_response()` pour chaque réponse
    - Passage des paramètres TTS dynamiques à `voice_service.text_to_speech()`
  - **Enrichissement `ProspectResponseV2`:**
    - Nouveaux champs: `sounds_before`, `visual_actions`, `detected_emotion`
  - **WebSocket:**
    - Envoie `sounds_before`, `visual_actions`, `detected_emotion` au frontend
- [x] Bloqueurs: Aucun
- [ ] Reste à faire (7c):
  - Télécharger/créer fichiers audio MP3 réels
  - Implémenter lecture des sons côté frontend
  - Pipeline mixeur audio complet

(Ajouter une section par session de travail)

---

*Dernière mise à jour : 2026-01-03*
