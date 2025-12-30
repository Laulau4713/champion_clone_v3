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

## GÉNÈRE UN SCÉNARIO JSON

Le scénario doit inclure:
- Un prospect crédible (nom français, fonction, entreprise fictive)
- Un contexte de conversation réaliste
- Des pain points cohérents avec le secteur
- Un message d'ouverture naturel (comme une vraie conversation)
- Un besoin caché que l'élève doit découvrir

FORMAT JSON STRICT:
{{
  "title": "Titre du scénario",
  "prospect": {{
    "name": "Prénom Nom",
    "role": "Fonction",
    "company": "Entreprise (fictive mais crédible)",
    "personality": "friendly|skeptical|busy|aggressive|analytical",
    "mood": "curious|hesitant|impatient|defensive|open",
    "pain_points": ["problème 1", "problème 2", "problème 3"],
    "hidden_need": "Le vrai besoin non exprimé",
    "budget_situation": "tight|flexible|undefined",
    "decision_power": "decides|influences|gathers_info"
  }},
  "context": "Description de la situation (2-3 phrases)",
  "opening_message": "Premier message naturel du prospect",
  "key_moments": [
    "Moment clé 1 où l'élève sera testé",
    "Moment clé 2"
  ],
  "success_criteria": [
    "Ce que l'élève doit faire pour réussir"
  ],
  "difficulty_score": 50
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
