"""
InterruptionService - Gère les interruptions du prospect selon le niveau de difficulté.

Responsable de:
- Décider quand le prospect interrompt l'utilisateur
- Générer des phrases d'interruption appropriées
- Adapter le comportement selon le niveau (easy, medium, expert)
"""

import random
from dataclasses import dataclass
from typing import Optional
import structlog

logger = structlog.get_logger()


@dataclass
class InterruptionDecision:
    """Résultat de la décision d'interruption."""
    should_interrupt: bool
    phrase: Optional[str] = None
    reason: Optional[str] = None
    interruption_type: Optional[str] = None  # impatient, skeptical, disagreement


class InterruptionService:
    """
    Service de gestion des interruptions du prospect.

    Le comportement varie selon le niveau:
    - easy: Jamais d'interruption
    - medium: Interruptions occasionnelles après longue parole
    - expert: Interruptions fréquentes, réactives aux hésitations
    """

    # Configuration par niveau
    LEVEL_CONFIGS = {
        "easy": {
            "enabled": False,
            "interruption_probability": 0.0,
            "patience_seconds": 999,
            "hesitation_threshold": 999,
        },
        "medium": {
            "enabled": True,
            "interruption_probability": 0.1,
            "patience_seconds": 20,
            "hesitation_threshold": 7,
        },
        "expert": {
            "enabled": True,
            "interruption_probability": 0.4,
            "patience_seconds": 8,
            "hesitation_threshold": 3,
        }
    }

    # Phrases d'interruption par type
    INTERRUPTION_PHRASES = {
        "impatient": [
            "Attendez, je vous arrête...",
            "Oui mais concrètement ?",
            "Venons-en au fait.",
            "Je n'ai pas beaucoup de temps.",
            "Pouvez-vous être plus concis ?",
            "D'accord, mais en résumé ?",
        ],
        "skeptical": [
            "Hmm, vous êtes sûr de ce que vous avancez ?",
            "Ça me semble un peu trop beau...",
            "Comment pouvez-vous prouver ça ?",
            "D'autres m'ont dit la même chose...",
            "J'ai du mal à vous croire.",
        ],
        "disagreement": [
            "Non, je ne suis pas d'accord.",
            "Ce n'est pas ce que j'ai compris.",
            "Attendez, c'est incorrect.",
            "Non, ça ne fonctionne pas comme ça.",
            "Je vous arrête, c'est faux.",
        ]
    }

    def __init__(self, level: str = "easy"):
        """
        Initialise le service d'interruption.

        Args:
            level: Niveau de difficulté (easy, medium, expert)
        """
        self.level = level
        self.config = self.LEVEL_CONFIGS.get(level, self.LEVEL_CONFIGS["easy"])
        logger.debug("interruption_service_initialized", level=level, enabled=self.config["enabled"])

    def should_interrupt(
        self,
        speaking_duration: float,
        hesitation_count: int = 0,
        emotions: Optional[dict] = None,
        context: Optional[dict] = None
    ) -> InterruptionDecision:
        """
        Décide si le prospect doit interrompre.

        Args:
            speaking_duration: Durée de parole en secondes
            hesitation_count: Nombre d'hésitations détectées
            emotions: Émotions détectées (confidence, hesitation, etc.)
            context: Contexte additionnel (factual_error, etc.)

        Returns:
            InterruptionDecision avec should_interrupt, phrase, reason
        """
        # Niveau easy ne coupe jamais
        if not self.config["enabled"]:
            return InterruptionDecision(should_interrupt=False)

        emotions = emotions or {}
        context = context or {}

        # 1. Erreur factuelle → toujours interrompre
        if context.get("factual_error"):
            return InterruptionDecision(
                should_interrupt=True,
                phrase=self.get_random_phrase("disagreement"),
                reason="factual_error",
                interruption_type="disagreement"
            )

        # 2. Parle trop longtemps → interrompre
        if speaking_duration > self.config["patience_seconds"]:
            return InterruptionDecision(
                should_interrupt=True,
                phrase=self.get_random_phrase("impatient"),
                reason="speaking_too_long",
                interruption_type="impatient"
            )

        # 3. Trop d'hésitations (avec probabilité)
        if hesitation_count >= self.config["hesitation_threshold"]:
            if random.random() < self.config["interruption_probability"] * 1.5:
                return InterruptionDecision(
                    should_interrupt=True,
                    phrase=self.get_random_phrase("impatient"),
                    reason="too_much_hesitation",
                    interruption_type="impatient"
                )

        # 4. Confiance faible détectée
        confidence = emotions.get("confidence", 1.0)
        if confidence < 0.3:
            if random.random() < self.config["interruption_probability"] * 2:
                return InterruptionDecision(
                    should_interrupt=True,
                    phrase=self.get_random_phrase("skeptical"),
                    reason="low_confidence",
                    interruption_type="skeptical"
                )

        # 5. Interruption aléatoire selon probabilité de base
        if random.random() < self.config["interruption_probability"]:
            return InterruptionDecision(
                should_interrupt=True,
                phrase=self.get_random_phrase("impatient"),
                reason="random",
                interruption_type="impatient"
            )

        return InterruptionDecision(should_interrupt=False)

    def get_random_phrase(self, interruption_type: str) -> str:
        """
        Récupère une phrase d'interruption aléatoire.

        Args:
            interruption_type: Type d'interruption (impatient, skeptical, disagreement)

        Returns:
            Phrase d'interruption
        """
        phrases = self.INTERRUPTION_PHRASES.get(
            interruption_type,
            self.INTERRUPTION_PHRASES["impatient"]
        )
        return random.choice(phrases)
