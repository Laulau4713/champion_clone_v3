"""
Service de chargement des templates de scénarios.

Phase 4 du plan: Templates scénarios pré-définis par skill.
Élimine le besoin d'appels API pour la génération de scénarios.
"""

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Chemin vers les templates
TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "scenario_templates"


def load_scenario_template(skill_slug: str, variant: int | None = None, difficulty: str = "easy") -> dict | None:
    """
    Charge un template de scénario pour un skill donné.

    Args:
        skill_slug: Le slug du skill (ex: "cold_calling")
        variant: Numéro du variant (1, 2, 3...). Si None, choix aléatoire.
        difficulty: Niveau de difficulté pour adapter le template

    Returns:
        Le template chargé ou None si non trouvé
    """
    skill_dir = TEMPLATES_DIR / skill_slug

    if not skill_dir.exists():
        logger.warning("scenario_template_dir_not_found", skill=skill_slug)
        return None

    # Lister les templates disponibles
    templates = list(skill_dir.glob("template_*.json"))

    if not templates:
        logger.warning("no_templates_found", skill=skill_slug)
        return None

    # Sélectionner le template
    if variant is not None:
        template_file = skill_dir / f"template_{variant}.json"
        if not template_file.exists():
            logger.warning("template_variant_not_found", skill=skill_slug, variant=variant)
            template_file = random.choice(templates)
    else:
        template_file = random.choice(templates)

    try:
        with open(template_file, encoding="utf-8") as f:
            template = json.load(f)

        # Appliquer les modificateurs de difficulté
        template = apply_difficulty_modifiers(template, difficulty)

        logger.info("scenario_template_loaded", skill=skill_slug, template=template_file.name, difficulty=difficulty)

        return template

    except json.JSONDecodeError as e:
        logger.error("template_json_error", file=str(template_file), error=str(e))
        return None
    except Exception as e:
        logger.error("template_load_error", file=str(template_file), error=str(e))
        return None


def apply_difficulty_modifiers(template: dict, difficulty: str) -> dict:
    """
    Applique les modificateurs de difficulté au template.

    Args:
        template: Le template de base
        difficulty: easy, medium, ou expert

    Returns:
        Le template modifié selon la difficulté
    """
    result = deepcopy(template)

    # Récupérer les modificateurs spécifiques à la difficulté
    modifiers = template.get("scenario_flow", {}).get("difficulty_modifiers", {})
    difficulty_config = modifiers.get(difficulty, {})

    if difficulty_config:
        # Appliquer la résistance du gatekeeper
        if "gatekeeper_resistance" in difficulty_config:
            if "prospect" in result and "gatekeeper" in result["prospect"]:
                result["prospect"]["gatekeeper"]["resistance_level"] = difficulty_config["gatekeeper_resistance"]

        # Appliquer la disponibilité du décideur
        if "dm_availability" in difficulty_config:
            result["difficulty_context"] = difficulty_config["dm_availability"]

    # Ajuster les paramètres généraux selon la difficulté
    if difficulty == "easy":
        # Prospect plus coopératif
        if "prospect" in result:
            result["prospect"]["cooperation_level"] = "high"
            result["prospect"]["objection_intensity"] = "low"
    elif difficulty == "medium":
        if "prospect" in result:
            result["prospect"]["cooperation_level"] = "medium"
            result["prospect"]["objection_intensity"] = "medium"
    elif difficulty == "expert":
        if "prospect" in result:
            result["prospect"]["cooperation_level"] = "low"
            result["prospect"]["objection_intensity"] = "high"

    return result


def adapt_template_to_sector(
    template: dict,
    sector: Any,  # Modèle Sector de la DB
    difficulty: str = "easy",
) -> dict:
    """
    Adapte un template de scénario au secteur choisi.
    Aucun appel API - tout est basé sur les données du secteur.

    Args:
        template: Le template de base
        sector: L'objet Sector de la base de données
        difficulty: Niveau de difficulté

    Returns:
        Le template adapté au secteur
    """
    if not sector:
        return template

    scenario = deepcopy(template)

    # 1. Adapter les infos de l'entreprise si le secteur a des exemples
    if hasattr(sector, "example_companies") and sector.example_companies:
        company = random.choice(sector.example_companies)
        if "prospect" in scenario:
            scenario["prospect"]["company"] = company.get("name", scenario["prospect"].get("company"))
            scenario["prospect"]["company_size"] = company.get("size", "PME")

    # 2. Choisir un persona aléatoire du secteur
    if hasattr(sector, "prospect_personas") and sector.prospect_personas:
        persona = random.choice(sector.prospect_personas)
        if "prospect" in scenario:
            # Fusionner plutôt que remplacer
            if "decision_maker" in scenario["prospect"]:
                dm = scenario["prospect"]["decision_maker"]
                dm["name"] = persona.get("name", dm.get("name"))
                dm["role"] = persona.get("role", dm.get("role"))
                dm["personality"] = persona.get("personality", dm.get("personality", "neutral"))
                if "psychology" in persona:
                    dm["psychology"] = persona["psychology"]

    # 3. Adapter le vocabulaire
    if hasattr(sector, "vocabulary") and sector.vocabulary:
        scenario["sector_vocabulary"] = sector.vocabulary

    # 4. Injecter les objections typiques du secteur
    if hasattr(sector, "typical_objections") and sector.typical_objections:
        scenario["sector_objections"] = sector.typical_objections

    # 5. Utiliser le prompt contextuel du secteur
    if hasattr(sector, "agent_context_prompt") and sector.agent_context_prompt:
        scenario["agent_context_prompt"] = sector.agent_context_prompt

    # 6. Appliquer les adaptations de scénario du secteur
    if hasattr(sector, "scenario_adaptations") and sector.scenario_adaptations:
        if difficulty == "expert" and sector.scenario_adaptations.get("prospect_difficile"):
            scenario["difficulty_context"] = sector.scenario_adaptations["prospect_difficile"]

    logger.info(
        "template_adapted_to_sector",
        sector=sector.slug if hasattr(sector, "slug") else "unknown",
        difficulty=difficulty,
    )

    return scenario


def list_available_templates(skill_slug: str | None = None) -> dict:
    """
    Liste les templates disponibles.

    Args:
        skill_slug: Si fourni, liste uniquement pour ce skill

    Returns:
        Dict avec les skills et leurs templates
    """
    result = {}

    if skill_slug:
        skill_dir = TEMPLATES_DIR / skill_slug
        if skill_dir.exists():
            templates = list(skill_dir.glob("template_*.json"))
            result[skill_slug] = [t.stem for t in templates]
    else:
        # Lister tous les skills
        for skill_dir in TEMPLATES_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                templates = list(skill_dir.glob("template_*.json"))
                if templates:
                    result[skill_dir.name] = [t.stem for t in templates]

    return result


def get_template_count() -> dict:
    """
    Compte les templates par skill et niveau.

    Returns:
        Statistiques sur les templates
    """
    stats = {"total": 0, "by_skill": {}, "easy": [], "medium": [], "expert": []}

    SKILL_LEVELS = {
        # Easy
        "preparation_ciblage": "easy",
        "script_accroche": "easy",
        "cold_calling": "easy",
        "ecoute_active": "easy",
        # Medium
        "decouverte_compir": "medium",
        "checklist_bebedc": "medium",
        "qualification_columbo": "medium",
        "cartographie_decideurs": "medium",
        "profils_psychologiques": "medium",
        "argumentation_bac": "medium",
        "demonstration_produit": "medium",
        # Expert
        "objections_cnz": "expert",
        "negociation": "expert",
        "closing_ponts_brules": "expert",
        "relance_suivi": "expert",
        "recommandation": "expert",
        "situations_difficiles": "expert",
    }

    for skill_dir in TEMPLATES_DIR.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            templates = list(skill_dir.glob("template_*.json"))
            count = len(templates)
            if count > 0:
                stats["by_skill"][skill_dir.name] = count
                stats["total"] += count

                level = SKILL_LEVELS.get(skill_dir.name, "unknown")
                if level in stats:
                    stats[level].append(skill_dir.name)

    return stats


def convert_template_to_scenario(template: dict) -> dict:
    """
    Convertit un template en format scénario compatible avec training_service_v2.

    Le format de sortie doit correspondre à ce que ContentAgent.generate_scenario() retourne.

    Args:
        template: Le template chargé

    Returns:
        Scénario au format attendu par create_session()
    """
    # Extraire les infos du prospect
    prospect_info = template.get("prospect", {})
    decision_maker = prospect_info.get("decision_maker", {})
    gatekeeper = prospect_info.get("gatekeeper", {})

    # Construire le scénario
    scenario = {
        "title": template.get("name", "Scénario d'entraînement"),
        "context": template.get("description", ""),
        "template_id": template.get("template_id"),
        "skill_slug": template.get("skill_slug"),
        "prospect": {
            "name": decision_maker.get("name", "Le prospect"),
            "role": decision_maker.get("role", "Professionnel"),
            "company": decision_maker.get("company", "Entreprise"),
            "company_size": decision_maker.get("company_size", "PME"),
            "sector": prospect_info.get("sector", decision_maker.get("sector")),
            "personality": decision_maker.get("personality", "neutral"),
            "pain_points": decision_maker.get("pain_points", []),
            "hidden_need": decision_maker.get("hidden_need"),
            "current_situation": decision_maker.get("current_situation"),
            "hidden_objections": prospect_info.get("hidden_objections", []),
        },
        "gatekeeper": {
            "name": gatekeeper.get("name"),
            "role": gatekeeper.get("role"),
            "personality": gatekeeper.get("personality"),
            "typical_responses": gatekeeper.get("typical_responses", []),
        }
        if gatekeeper
        else None,
        "product": template.get("product", {}),
        "proof": template.get("proof", {}),
        "competition": template.get("competition", {}),
        "scenario_flow": template.get("scenario_flow", {}),
        "opening_message": template.get("scenario_flow", {}).get("opening", {}).get("gatekeeper_first_response")
        or template.get("scenario_flow", {}).get("opening", {}).get("prospect_first_response")
        or "Bonjour?",
        "objectives": template.get("scenario_flow", {}).get("objectives", []),
        "success_criteria": template.get("scenario_flow", {}).get("success_criteria", []),
        "conversation_rules": template.get(
            "conversation_rules", {"min_exchanges": 5, "max_exchanges": 15, "auto_end_enabled": True}
        ),
        "solution": template.get("product", {}).get("name"),
        "product_pitch": template.get("product", {}).get("tagline"),
        # Objections visibles (celles que le prospect peut exprimer)
        "objections": [
            {
                "expressed": obj.get("expressed", obj.get("objection")),
                "hidden": obj.get("hidden", ""),
                "type": obj.get("type", "general"),
            }
            for obj in template.get("possible_objections", [])
        ],
    }

    # Nettoyer les valeurs None
    scenario = {k: v for k, v in scenario.items() if v is not None}

    return scenario
