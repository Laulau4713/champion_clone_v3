"""
Prompts for ContentAgent scenario generation and adaptation.
"""

SCENARIO_GENERATION_PROMPT = """Tu es un expert en formation commerciale.
Génère un scénario d'entraînement réaliste pour le skill "{skill_name}".

## CONTEXTE
- Niveau: {level}
- Secteur: {sector_name}
- Description du skill: {skill_description}

## CRITÈRES D'ÉVALUATION
{evaluation_criteria}

## INSTRUCTIONS PROSPECT
{prospect_instructions}

## HISTORIQUE ÉLÈVE (si disponible)
{user_history}

## GÉNÈRE UN SCÉNARIO JSON ENRICHI

Le scénario doit inclure:
- Un prospect crédible (nom français, fonction, entreprise fictive)
- Un contexte de conversation réaliste
- Des pain points cohérents avec le secteur
- Un message d'ouverture naturel (comme une vraie conversation)
- Un besoin caché que l'élève doit découvrir
- UN PRODUIT COMPLET avec toutes les infos nécessaires au vendeur
- DES PREUVES SOCIALES (témoignages, études de cas, stats)
- DES INFOS CONCURRENCE pour gérer les objections "on a déjà un fournisseur"

FORMAT JSON STRICT:
{{
  "title": "Titre du scénario",
  "prospect": {{
    "name": "Prénom Nom",
    "role": "Fonction",
    "company": "Entreprise (fictive mais crédible)",
    "company_size": "Nombre d'employés",
    "sector": "Secteur d'activité",
    "personality": "friendly|skeptical|busy|aggressive|analytical",
    "mood": "curious|hesitant|impatient|defensive|open",
    "pain_points": ["problème 1", "problème 2", "problème 3"],
    "hidden_need": "Le vrai besoin non exprimé",
    "budget_situation": "tight|flexible|undefined",
    "decision_power": "decides|influences|gathers_info",
    "current_situation": "Ce qu'ils utilisent actuellement"
  }},
  "context": "Description de la situation (2-3 phrases)",
  "opening_message": "Premier message naturel du prospect",

  "product": {{
    "name": "Nom du produit/service",
    "tagline": "Accroche en une phrase",
    "how_it_works": {{
      "summary": "Description concise du fonctionnement",
      "key_features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4"],
      "technical_requirements": "Prérequis techniques (si applicable)",
      "implementation_time": "Durée de mise en place"
    }},
    "integrations": ["Intégration 1", "Intégration 2", "Intégration 3"],
    "support": {{
      "onboarding": "Processus d'onboarding inclus",
      "support": "Canaux et horaires de support",
      "sla": "Engagement de niveau de service (si applicable)"
    }},
    "pricing": {{
      "model": "flat|per_user|usage",
      "entry_price": "Prix d'entrée",
      "popular_plan": "Plan le plus populaire avec prix",
      "engagement": "Conditions d'engagement",
      "free_trial": "Essai gratuit (si disponible)"
    }}
  }},

  "proof": {{
    "testimonials": [
      {{
        "name": "Prénom Nom",
        "role": "Fonction",
        "company": "Entreprise (taille)",
        "quote": "Témoignage impactant",
        "result": "Résultat chiffré"
      }}
    ],
    "case_studies": [
      {{
        "client": "Nom du client",
        "sector": "Secteur similaire au prospect",
        "problem": "Problème initial",
        "solution": "Solution mise en place",
        "results": {{
          "metric1": "Valeur 1",
          "metric2": "Valeur 2"
        }}
      }}
    ],
    "stats": {{
      "clients_count": "Nombre de clients",
      "satisfaction": "Note de satisfaction",
      "nps": "Score NPS (si connu)"
    }},
    "notable_clients": ["Client notable 1", "Client notable 2", "Client notable 3"]
  }},

  "competition": {{
    "main_competitors": [
      {{
        "name": "Concurrent 1",
        "positioning": "Son positionnement marché",
        "strengths": ["Force 1", "Force 2"],
        "weaknesses": ["Faiblesse 1", "Faiblesse 2"],
        "price_comparison": "Comparaison de prix"
      }},
      {{
        "name": "Concurrent 2",
        "positioning": "Son positionnement marché",
        "strengths": ["Force 1", "Force 2"],
        "weaknesses": ["Faiblesse 1", "Faiblesse 2"],
        "price_comparison": "Comparaison de prix"
      }}
    ],
    "our_differentiator": "Ce qui nous rend uniques (1-2 phrases)",
    "switch_cost": {{
      "migration_time": "Durée de migration",
      "data_import": "Capacités d'import",
      "training_needed": "Formation nécessaire",
      "risk": "Niveau de risque et comment on le réduit"
    }}
  }},

  "product_pitch": "Le pitch commercial complet (3-4 phrases) que le commercial peut utiliser pour ce prospect spécifique, en répondant à ses pain points",

  "key_moments": [
    "Moment clé 1 où l'élève sera testé",
    "Moment clé 2"
  ],
  "success_criteria": [
    "Ce que l'élève doit faire pour réussir"
  ],
  "difficulty_score": 50,

  "conversation_rules": {{
    "min_exchanges": 4,
    "max_exchanges": 15,
    "auto_end_enabled": true
  }}
}}
"""

SECTOR_ADAPTATION_PROMPT = """Adapte ce scénario au secteur {sector_name}.

## SCÉNARIO DE BASE
{base_scenario}

## VOCABULAIRE DU SECTEUR
{vocabulary}

## OBJECTIONS TYPIQUES DU SECTEUR
{typical_objections}

## PERSONAS TYPIQUES
{prospect_personas}

## CONTEXTE SECTORIEL
{agent_context_prompt}

Adapte le scénario en:
1. Utilisant le vocabulaire métier approprié
2. Ajustant les objections au secteur
3. Rendant le contexte crédible pour ce secteur
4. Gardant la même structure JSON
"""

EXAMPLE_SCRIPT_PROMPT = """Génère un script d'exemple {script_type} pour le skill "{skill_name}".

## SKILL
{skill_description}

## SECTEUR (si applicable)
{sector_context}

## TYPE DE SCRIPT
{script_type_description}

## FORMAT
Génère un dialogue naturel entre un commercial et un prospect.
Inclus des annotations pédagogiques.

FORMAT JSON:
{{
  "title": "Titre du script",
  "context": "Situation de départ",
  "dialogue": [
    {{"role": "prospect", "text": "..."}},
    {{"role": "commercial", "text": "...", "annotation": "Ce qui est bien/mal ici"}},
    ...
  ],
  "key_takeaway": "La leçon principale",
  "techniques_used": ["technique 1", "technique 2"]
}}
"""

DIFFICULTY_ADJUSTMENT_PROMPT = """Ajuste la difficulté de ce scénario.

## SCÉNARIO ACTUEL
{scenario}

## STATISTIQUES UTILISATEUR
- Score moyen: {average_score}%
- Derniers scores: {recent_scores}
- Points forts: {strengths}
- Points faibles: {weaknesses}

## AJUSTEMENT REQUIS
{adjustment_direction}

Modifie le scénario pour le rendre {"plus difficile" if harder else "plus facile"}:
- Ajuste la personnalité du prospect
- Modifie les objections
- Change le niveau des pain points

Retourne le scénario JSON modifié.
"""
