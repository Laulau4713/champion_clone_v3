"""
Training Agent Tools - Utilitaires pour l'agent de formation.

Ce fichier est conservé pour compatibilité. La logique principale
a été déplacée dans agent.py qui utilise directement les services
PlaybookService, ModuleService et JaugeService.
"""

import structlog

logger = structlog.get_logger()


class TrainingTools:
    """
    Collection d'outils utilitaires pour le training.

    Note: La plupart des fonctionnalités ont été migrées vers:
    - PlaybookService (playbook_service.py)
    - ModuleService (module_service.py)
    - JaugeService (jauge_service.py)
    - TrainingAgent (agent.py)
    """

    # Conservé pour compatibilité avec l'ancien code
    PROSPECT_SYSTEM_PROMPT = """Tu es un prospect dans un scénario de formation commerciale.

CONTEXTE DU SCÉNARIO:
{scenario}

PATTERNS DU CHAMPION (pour créer des défis appropriés):
{patterns}

---

RÈGLES:
1. Tu joues le rôle du PROSPECT, pas du vendeur
2. Sois réaliste - pose des questions, hésite, objecte
3. Adapte ton niveau de difficulté ({difficulty})
4. Utilise les objections que le champion sait gérer
5. Réponds de manière concise (1-3 phrases max)
6. Ne sois pas trop facile - challenge l'utilisateur

DIFFICULTÉ:
- easy: Prospect plutôt ouvert, quelques hésitations
- medium: Prospect sceptique, objections standards
- hard: Prospect difficile, multiples objections

Commence quand on te dit "START"."""

    def __init__(self):
        logger.info("training_tools_init", msg="TrainingTools initialized (legacy)")

    async def generate_tips(self, scenario: dict, patterns: dict) -> list[str]:
        """
        Génère des conseils contextuels (conservé pour compatibilité).

        Cette fonction est maintenant gérée par le playbook qui contient
        directement les phrases clés et questions de découverte.
        """
        tips = []

        if patterns.get("openings"):
            tips.append(f"Technique d'ouverture: {patterns['openings'][0][:60]}...")

        if patterns.get("key_phrases"):
            tips.append(f'Phrase clé: "{patterns["key_phrases"][0][:50]}..."')

        objectives = scenario.get("objectives", [])
        if objectives:
            tips.append(f"Objectif: {objectives[0]}")

        return tips[:4]

    def check_session_complete(self, conversation: list, scenario: dict) -> bool:
        """
        Vérifie si la session doit se terminer (conservé pour compatibilité).

        La logique principale est dans TrainingAgent._check_session_complete()
        """
        user_messages = [m for m in conversation if m.get("role") == "user"]

        if len(user_messages) >= 10:
            return True

        if conversation:
            last = conversation[-1].get("content", "").lower()
            endings = [
                "d'accord",
                "on signe",
                "je prends",
                "marché conclu",
                "envoyez-moi",
                "je vous rappelle",
                "pas intéressé",
                "non merci",
                "au revoir",
            ]
            if any(end in last for end in endings):
                return True

        return False
