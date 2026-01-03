"""
Service d'adaptation sectorielle des scénarios.

Phase 5 du plan: Adaptation sectorielle sans API.
Adapte les templates génériques au secteur choisi par l'utilisateur,
sans appel API - tout est basé sur les données du secteur.
"""

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Chemin vers les données de secteurs
SECTORS_DATA_PATH = Path(__file__).parent.parent / "content" / "sectors.json"

# ==========================================
# MAPPING SECTEUR → PRODUIT PAR DÉFAUT
# ==========================================

SECTOR_DEFAULT_PRODUCTS = {
    "immo": {
        "name": "Mandat de vente",
        "type": "service",
        "tagline": "Votre bien, notre expertise",
        "value_proposition": "Accompagnement complet pour vendre au meilleur prix",
        "how_it_works": {
            "summary": "Service d'intermédiation immobilière complet",
            "key_features": [
                "Estimation gratuite et sans engagement",
                "Photos professionnelles et visite virtuelle",
                "Diffusion sur tous les portails",
                "Qualification des acheteurs",
                "Accompagnement jusqu'à la signature",
            ],
            "implementation_time": "Mise en vente sous 48h",
        },
        "pricing": {
            "model": "commission",
            "typical_rate": "3% à 5% du prix de vente",
            "entry_price": "Commission uniquement au succès",
            "conditions": "Pas de frais si pas de vente",
        },
    },
    "b2b_saas": {
        "name": "Solution SaaS",
        "type": "subscription",
        "tagline": "Automatisez pour performer",
        "value_proposition": "Automatisation et gain de productivité",
        "how_it_works": {
            "summary": "Plateforme cloud prête à l'emploi",
            "key_features": [
                "Interface intuitive, prise en main rapide",
                "Intégrations avec vos outils existants",
                "Tableau de bord et analytics",
                "Support client dédié",
                "Mises à jour automatiques",
            ],
            "implementation_time": "Déploiement en 1-2 semaines",
        },
        "pricing": {
            "model": "par_utilisateur",
            "entry_price": "À partir de 29€/utilisateur/mois",
            "popular_plan": "Pro à 79€/utilisateur/mois",
            "engagement": "Mensuel ou annuel (-20%)",
            "free_trial": "14 jours gratuits",
        },
    },
    "assurance": {
        "name": "Contrat d'assurance",
        "type": "subscription",
        "tagline": "Votre tranquillité, notre priorité",
        "value_proposition": "Protection adaptée à votre situation",
        "how_it_works": {
            "summary": "Couverture personnalisée selon vos besoins",
            "key_features": [
                "Garanties modulables",
                "Pas de questionnaire médical (selon produit)",
                "Assistance 24h/24",
                "Gestion des sinistres simplifiée",
                "Application mobile",
            ],
            "implementation_time": "Effet immédiat ou à date choisie",
        },
        "pricing": {
            "model": "prime_mensuelle",
            "entry_price": "Dès 20€/mois",
            "typical_range": "20€ à 200€/mois selon couverture",
            "engagement": "Résiliable après 1 an (Loi Hamon)",
        },
    },
    "auto": {
        "name": "Véhicule",
        "type": "one_time",
        "tagline": "La mobilité qui vous ressemble",
        "value_proposition": "Le véhicule adapté à vos besoins et budget",
        "how_it_works": {
            "summary": "Accompagnement de A à Z dans votre projet auto",
            "key_features": [
                "Large choix de véhicules",
                "Reprise de votre ancien véhicule",
                "Solutions de financement (LOA, LLD, crédit)",
                "Garantie constructeur/label",
                "Service après-vente",
            ],
            "implementation_time": "Livraison sous 1-8 semaines selon stock",
        },
        "pricing": {
            "model": "financement",
            "typical_range": "25 000€ à 60 000€",
            "financing_options": "LOA dès 299€/mois, LLD, Crédit classique",
            "trade_in": "Reprise au prix Argus ou plus",
        },
    },
    "energie": {
        "name": "Travaux de rénovation énergétique",
        "type": "one_time",
        "tagline": "Économisez en valorisant votre bien",
        "value_proposition": "Économies d'énergie et confort amélioré",
        "how_it_works": {
            "summary": "Rénovation clé en main avec gestion des aides",
            "key_features": [
                "Audit énergétique gratuit",
                "Artisans RGE certifiés",
                "Gestion complète des aides (MaPrimeRénov', CEE)",
                "Garantie décennale",
                "Accompagnement administratif",
            ],
            "implementation_time": "Travaux sous 2-8 semaines",
        },
        "pricing": {
            "model": "projet",
            "typical_range": "5 000€ à 50 000€ selon travaux",
            "after_aids": "Reste à charge réduit de 40% à 90%",
            "financing": "Éco-PTZ disponible",
        },
    },
    "generic": {
        "name": "Solution",
        "type": "generic",
        "tagline": "La réponse à votre besoin",
        "value_proposition": "Réponse adaptée à votre problématique métier",
        "how_it_works": {
            "summary": "Solution flexible et évolutive",
            "key_features": [
                "Personnalisation selon vos besoins",
                "Accompagnement dédié",
                "Support réactif",
                "Évolutivité",
            ],
            "implementation_time": "Variable selon le projet",
        },
        "pricing": {"model": "sur_mesure", "note": "Tarification adaptée à votre contexte"},
    },
}


# ==========================================
# CHARGEMENT DES DONNÉES DE SECTEURS
# ==========================================

_sectors_cache: dict | None = None


def load_sectors_data() -> dict:
    """
    Charge les données des secteurs depuis le fichier JSON.
    Utilise un cache en mémoire pour éviter les lectures répétées.
    """
    global _sectors_cache

    if _sectors_cache is not None:
        return _sectors_cache

    try:
        with open(SECTORS_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
            _sectors_cache = {s["slug"]: s for s in data.get("sectors", [])}
            logger.info("sectors_data_loaded", count=len(_sectors_cache))
            return _sectors_cache
    except FileNotFoundError:
        logger.warning("sectors_data_file_not_found", path=str(SECTORS_DATA_PATH))
        return {}
    except json.JSONDecodeError as e:
        logger.error("sectors_data_json_error", error=str(e))
        return {}


def get_sector_data(sector_slug: str) -> dict | None:
    """
    Récupère les données enrichies d'un secteur.

    Args:
        sector_slug: Le slug du secteur (ex: "immo", "b2b_saas")

    Returns:
        Les données du secteur ou None si non trouvé
    """
    sectors = load_sectors_data()
    return sectors.get(sector_slug)


# ==========================================
# ADAPTATION PRINCIPALE
# ==========================================


def adapt_scenario_to_sector(base_template: dict, sector_slug: str, difficulty: str = "easy") -> dict:
    """
    Adapte un template de scénario au secteur choisi.
    Aucun appel API - tout est basé sur les données du secteur.

    Cette fonction enrichit le template avec:
    - Un persona aléatoire du secteur
    - Le vocabulaire sectoriel
    - Les objections typiques du secteur
    - Les objections cachées du persona
    - Les triggers de conversion
    - Le prompt contextuel pour l'agent
    - Le produit par défaut du secteur (si non défini)

    Args:
        base_template: Le template de scénario de base
        sector_slug: Le slug du secteur
        difficulty: Niveau de difficulté (easy, medium, expert)

    Returns:
        Le template adapté au secteur
    """
    scenario = deepcopy(base_template)

    # Charger les données du secteur
    sector_data = get_sector_data(sector_slug)
    if not sector_data:
        logger.warning("sector_not_found_for_adaptation", sector=sector_slug)
        return scenario

    # 1. Injecter le produit par défaut si non défini
    if not scenario.get("product"):
        default_product = SECTOR_DEFAULT_PRODUCTS.get(sector_slug, SECTOR_DEFAULT_PRODUCTS["generic"])
        scenario["product"] = deepcopy(default_product)
        logger.debug("default_product_injected", sector=sector_slug, product=default_product["name"])

    # 2. Choisir un persona aléatoire du secteur
    persona = None
    if sector_data.get("prospect_personas"):
        # Filtrer les personas par difficulté si applicable
        personas = sector_data["prospect_personas"]

        # En mode expert, préférer les personas avec personality difficile
        if difficulty == "expert":
            difficult_personalities = ["impatient", "analytical", "skeptical", "reluctant", "procedural"]
            difficult_personas = [p for p in personas if p.get("personality") in difficult_personalities]
            if difficult_personas:
                personas = difficult_personas

        persona = random.choice(personas)

        # Mettre à jour le prospect dans le scénario
        if "prospect" not in scenario:
            scenario["prospect"] = {}

        prospect = scenario["prospect"]

        # Fusionner les infos du persona
        if "decision_maker" not in prospect:
            prospect["decision_maker"] = {}

        dm = prospect["decision_maker"]

        # Générer un nom réaliste si pas défini
        if persona.get("id"):
            first_names = {
                "primo_accedant": ["Marie", "Thomas", "Julie", "Antoine"],
                "investisseur": ["Philippe", "Christine", "Marc", "Isabelle"],
                "vendeur_presse": ["Jean-Pierre", "Nathalie", "Olivier", "Sandrine"],
                "senior_patrimoine": ["Bernard", "Françoise", "Michel", "Monique"],
                "head_of_ops": ["Julien", "Sophie", "Nicolas", "Caroline"],
                "it_manager": ["Frédéric", "Laure", "Sébastien", "Émilie"],
                "ceo_startup": ["Maxime", "Léa", "Alexandre", "Camille"],
                "procurement": ["Christophe", "Sylvie", "Pascal", "Valérie"],
                "jeune_actif": ["Lucas", "Emma", "Hugo", "Chloé"],
                "famille_securite": ["David", "Aurélie", "Stéphane", "Céline"],
                "senior_prevoyant": ["Gérard", "Martine", "Alain", "Danielle"],
                "famille_pratique": ["Vincent", "Amélie", "Guillaume", "Mélanie"],
                "passionne": ["Romain", "Pauline", "Fabien", "Justine"],
                "proprietaire_sensibilise": ["Thierry", "Patricia", "Laurent", "Brigitte"],
                "bailleur_contraint": ["Dominique", "Catherine", "Yves", "Anne-Marie"],
                "decision_maker": ["Pierre", "Claire", "Emmanuel", "Nadia"],
                "evaluator": ["François", "Delphine", "Mathieu", "Hélène"],
                "budget_holder": ["Éric", "Véronique", "Bruno", "Florence"],
            }

            names = first_names.get(persona["id"], ["Client"])
            dm["name"] = random.choice(names)

        dm["role"] = persona.get("description", dm.get("role", "Professionnel"))
        dm["personality"] = persona.get("personality", dm.get("personality", "neutral"))
        dm["communication_style"] = persona.get("communication_style", "")

        # Injecter la psychologie du persona
        if persona.get("psychology"):
            dm["psychology"] = persona["psychology"]
            dm["motivations"] = persona["psychology"].get("motivations", [])
            dm["fears"] = persona["psychology"].get("fears", [])
            dm["decision_style"] = persona["psychology"].get("decision_style", "")
            dm["trust_builders"] = persona["psychology"].get("trust_builders", [])

        # Infos budgétaires si disponibles
        if persona.get("typical_budget"):
            dm["typical_budget"] = persona["typical_budget"]
        if persona.get("age_range"):
            dm["age_range"] = persona["age_range"]

    # 3. Injecter le vocabulaire du secteur
    if sector_data.get("vocabulary"):
        scenario["sector_vocabulary"] = sector_data["vocabulary"]

    # 4. Injecter les objections typiques du secteur
    if sector_data.get("typical_objections"):
        scenario["sector_objections"] = sector_data["typical_objections"]

        # Ajouter aux objections possibles du scénario
        if "possible_objections" not in scenario:
            scenario["possible_objections"] = []

        # Sélectionner 2-3 objections du secteur
        sector_objections = sector_data["typical_objections"]
        num_to_add = min(3, len(sector_objections))
        selected_objections = random.sample(sector_objections, num_to_add)

        for obj in selected_objections:
            scenario["possible_objections"].append(
                {
                    "expressed": obj.get("objection"),
                    "type": obj.get("category", "general"),
                    "frequency": obj.get("frequency", "medium"),
                    "suggested_responses": obj.get("suggested_responses", []),
                }
            )

    # 5. Injecter les objections cachées du persona
    if persona and persona.get("hidden_objections"):
        if "hidden_objections" not in scenario.get("prospect", {}):
            scenario["prospect"]["hidden_objections"] = []

        # En mode expert, injecter plus d'objections cachées
        max_hidden = 1 if difficulty == "easy" else (2 if difficulty == "medium" else 3)
        hidden_objs = persona["hidden_objections"][:max_hidden]

        for obj in hidden_objs:
            scenario["prospect"]["hidden_objections"].append(
                {
                    "expressed": obj.get("expressed"),
                    "hidden": obj.get("hidden"),
                    "discovery_approach": obj.get("discovery_approach", ""),
                    "discovered": False,
                }
            )

    # 6. Injecter les triggers de conversion du persona
    if persona and persona.get("conversion_triggers"):
        scenario["conversion_triggers"] = persona["conversion_triggers"]

        # Ajuster le seuil selon la difficulté
        base_threshold = persona["conversion_triggers"].get("gauge_threshold", 70)
        if difficulty == "medium":
            scenario["conversion_threshold"] = base_threshold + 5
        elif difficulty == "expert":
            scenario["conversion_threshold"] = base_threshold + 10
        else:
            scenario["conversion_threshold"] = base_threshold

        # Ajouter les signaux de closing
        if persona["conversion_triggers"].get("closing_signals"):
            scenario["closing_signals"] = persona["conversion_triggers"]["closing_signals"]

    # 7. Utiliser le prompt contextuel du secteur
    if sector_data.get("agent_context_prompt"):
        scenario["agent_context_prompt"] = sector_data["agent_context_prompt"]

    # 8. Appliquer les adaptations de scénario selon la difficulté
    if sector_data.get("scenario_adaptations"):
        adaptations = sector_data["scenario_adaptations"]

        if difficulty == "expert":
            if adaptations.get("prospect_difficile"):
                scenario["difficulty_context"] = adaptations["prospect_difficile"]
            if adaptations.get("multi_objections"):
                scenario["multi_objections_context"] = adaptations["multi_objections"]
        elif difficulty == "medium":
            if adaptations.get("pression_temporelle"):
                scenario["pressure_context"] = adaptations["pression_temporelle"]

    # 9. Ajouter le contexte marché du secteur
    if sector_data.get("market_context"):
        scenario["market_context"] = sector_data["market_context"]

    # 10. Marquer le secteur dans le scénario
    scenario["sector"] = {"slug": sector_slug, "name": sector_data.get("name"), "icon": sector_data.get("icon")}

    logger.info(
        "scenario_adapted_to_sector",
        sector=sector_slug,
        difficulty=difficulty,
        persona_id=persona.get("id") if persona else None,
        hidden_objections_count=len(scenario.get("prospect", {}).get("hidden_objections", [])),
    )

    return scenario


def get_sector_objections(sector_slug: str, category: str | None = None) -> list[dict]:
    """
    Récupère les objections typiques d'un secteur.

    Args:
        sector_slug: Le slug du secteur
        category: Filtrer par catégorie (price, timing, competition, etc.)

    Returns:
        Liste des objections
    """
    sector_data = get_sector_data(sector_slug)
    if not sector_data:
        return []

    objections = sector_data.get("typical_objections", [])

    if category:
        objections = [o for o in objections if o.get("category") == category]

    return objections


def get_sector_personas(sector_slug: str, personality: str | None = None) -> list[dict]:
    """
    Récupère les personas d'un secteur.

    Args:
        sector_slug: Le slug du secteur
        personality: Filtrer par type de personnalité

    Returns:
        Liste des personas
    """
    sector_data = get_sector_data(sector_slug)
    if not sector_data:
        return []

    personas = sector_data.get("prospect_personas", [])

    if personality:
        personas = [p for p in personas if p.get("personality") == personality]

    return personas


def get_sector_vocabulary(sector_slug: str) -> list[dict]:
    """
    Récupère le vocabulaire d'un secteur.

    Args:
        sector_slug: Le slug du secteur

    Returns:
        Liste des termes avec définitions
    """
    sector_data = get_sector_data(sector_slug)
    if not sector_data:
        return []

    return sector_data.get("vocabulary", [])


def list_available_sectors() -> list[dict]:
    """
    Liste tous les secteurs disponibles.

    Returns:
        Liste des secteurs avec slug, name et icon
    """
    sectors = load_sectors_data()
    return [
        {
            "slug": slug,
            "name": data.get("name"),
            "icon": data.get("icon"),
            "description": data.get("description"),
            "personas_count": len(data.get("prospect_personas", [])),
            "objections_count": len(data.get("typical_objections", [])),
        }
        for slug, data in sectors.items()
    ]
