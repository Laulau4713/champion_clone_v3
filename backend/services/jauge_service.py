"""
Service de jauge émotionnelle - Coeur du système de réalisme V2.

La jauge représente l'état émotionnel du prospect (0-100):
- [0-25] HOSTILE -> Fermeture totale
- [26-50] SCEPTIQUE -> Doute, teste
- [51-75] NEUTRE -> Écoute
- [76-85] INTÉRESSÉ -> S'ouvre
- [86-100] PRÊT -> Signaux d'achat

Ce service gère:
- Les modifications de jauge basées sur les actions du commercial
- La détection des patterns comportementaux
- Le calcul de l'humeur du prospect
- Les conditions de conversion
"""

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JaugeModification:
    """Modification de la jauge."""

    action: str
    delta: int
    new_value: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "delta": self.delta,
            "new_value": self.new_value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MoodState:
    """État d'humeur actuel."""

    mood: str
    behavior: str
    jauge_range: tuple[int, int]


class JaugeService:
    """
    Gère la jauge émotionnelle du prospect.
    """

    # Définition des paliers par niveau
    MOOD_STAGES = {
        "easy": [
            {"range": [0, 25], "mood": "resistant", "behavior": "Répond par monosyllabes, sceptique"},
            {"range": [26, 50], "mood": "neutral", "behavior": "Écoute sans enthousiasme"},
            {"range": [51, 75], "mood": "interested", "behavior": "S'engage, pose des questions"},
            {"range": [76, 100], "mood": "ready_to_buy", "behavior": "Signaux d'achat, prêt à closer"},
        ],
        "medium": [
            {"range": [0, 20], "mood": "hostile", "behavior": "Veut raccrocher, agacé"},
            {"range": [21, 40], "mood": "resistant", "behavior": "Objections fréquentes, bras croisés"},
            {"range": [41, 60], "mood": "skeptical", "behavior": "Doute affiché, teste le commercial"},
            {"range": [61, 75], "mood": "neutral", "behavior": "Commence à écouter"},
            {"range": [76, 90], "mood": "interested", "behavior": "Questions constructives"},
            {"range": [91, 100], "mood": "ready_to_buy", "behavior": "Prêt à négocier"},
        ],
        "expert": [
            {"range": [0, 15], "mood": "hostile", "behavior": "Attaque personnelle, menace de raccrocher"},
            {"range": [16, 35], "mood": "aggressive", "behavior": "Objections en rafale, ton sec"},
            {"range": [36, 55], "mood": "skeptical", "behavior": "Questions pièges, bras croisés"},
            {"range": [56, 70], "mood": "neutral", "behavior": "Commence à écouter, moins fermé"},
            {"range": [71, 85], "mood": "interested", "behavior": "S'ouvre progressivement"},
            {"range": [86, 100], "mood": "ready_to_buy", "behavior": "Prêt à négocier pour finaliser"},
        ],
    }

    # Modificateurs par défaut (peuvent être overridés par le niveau)
    DEFAULT_MODIFIERS = {
        "positive": {
            "good_listening_signal": {"points": 3, "description": "Signal d'écoute approprié"},
            "relevant_reformulation": {"points": 5, "description": "Reformulation pertinente"},
            "emotional_reformulation": {"points": 7, "description": "Reformulation émotionnelle"},
            "good_open_question": {"points": 4, "description": "Question ouverte bien formulée"},
            "appropriate_silence": {"points": 5, "description": "Silence maîtrisé après prix"},
            "empathy_shown": {"points": 5, "description": "Empathie démontrée"},
            "value_demonstrated": {"points": 6, "description": "Valeur clairement démontrée"},
            "objection_well_handled": {"points": 8, "description": "Objection bien traitée"},
            "personalization": {"points": 4, "description": "Réponse personnalisée"},
            "roi_quantified": {"points": 7, "description": "ROI chiffré et pertinent"},
            "respected_competitor": {"points": 5, "description": "Concurrent respecté"},
            "counterpart_obtained": {"points": 5, "description": "Contrepartie obtenue pour concession"},
            "hidden_objection_discovered": {"points": 10, "description": "Objection cachée découverte"},
            "stayed_calm_under_pressure": {"points": 8, "description": "Resté calme sous pression"},
            "assertive_reframe": {"points": 8, "description": "Recadrage assertif réussi"},
            "creative_solution": {"points": 7, "description": "Propose une solution créative"},
            "multi_stakeholder_managed": {"points": 10, "description": "Gère plusieurs interlocuteurs"},
        },
        "negative": {
            "interruption": {"points": -5, "description": "Coupe la parole"},
            "ignored_information": {"points": -7, "description": "Ignore une info donnée"},
            "closed_question_spam": {"points": -3, "description": "Enchaîne les questions fermées"},
            "premature_pitch": {"points": -8, "description": "Pitch avant découverte"},
            "price_without_value": {"points": -10, "description": "Prix sans valeur construite"},
            "immediate_discount": {"points": -10, "description": "Remise immédiate sans contrepartie"},
            "denigrated_competitor": {"points": -12, "description": "Dénigrement concurrent"},
            "aggressive_closing": {"points": -6, "description": "Closing trop agressif"},
            "ignored_objection": {"points": -5, "description": "Ignore une objection"},
            "contradiction": {"points": -8, "description": "Se contredit"},
            "lost_temper": {"points": -15, "description": "Perte de calme"},
            "spoke_first_after_price": {"points": -8, "description": "Parlé en premier après le prix"},
            "budget_question_too_early": {"points": -5, "description": "Budget demandé trop tôt"},
            "defensive_reaction": {"points": -6, "description": "Réaction défensive"},
            "gave_up_too_early": {"points": -8, "description": "Abandonne trop tôt"},
        },
    }

    # Blockers de conversion
    CONVERSION_BLOCKERS = {
        "lost_temper": "Perte de calme -> conversion impossible",
        "denigrated_competitor": "Dénigrement -> jauge plafonnée à 70",
        "major_contradiction": "Contradiction majeure -> confiance brisée",
    }

    def __init__(self, level: str = "easy", level_config: dict = None):
        self.level = level
        self.level_config = level_config or {}
        self.modifiers = self._load_modifiers()
        self.mood_stages = self._load_mood_stages()

        # Paramètres du niveau
        self.starting_jauge = self.level_config.get("starting_gauge", 50)
        self.conversion_threshold = self.level_config.get("conversion_threshold", 75)
        volatility_str = self.level_config.get("gauge_volatility", "medium")
        self.volatility = {"low": 0.8, "medium": 1.0, "high": 1.3}.get(volatility_str, 1.0)

    def _load_modifiers(self) -> dict:
        """Charge les modificateurs, avec override du niveau si présent."""
        modifiers = {
            "positive": dict(self.DEFAULT_MODIFIERS["positive"]),
            "negative": dict(self.DEFAULT_MODIFIERS["negative"]),
        }

        if "jauge_modifiers" in self.level_config:
            level_mods = self.level_config["jauge_modifiers"]
            if "positive_actions" in level_mods:
                modifiers["positive"].update(level_mods["positive_actions"])
            if "negative_actions" in level_mods:
                modifiers["negative"].update(level_mods["negative_actions"])

        return modifiers

    def _load_mood_stages(self) -> list:
        """Charge les paliers d'humeur du niveau."""
        if "mood_stages" in self.level_config:
            return self.level_config["mood_stages"]
        return self.MOOD_STAGES.get(self.level, self.MOOD_STAGES["easy"])

    def get_mood(self, jauge: int) -> MoodState:
        """Retourne l'humeur correspondant à la jauge."""
        for stage in self.mood_stages:
            if stage["range"][0] <= jauge <= stage["range"][1]:
                return MoodState(mood=stage["mood"], behavior=stage["behavior"], jauge_range=tuple(stage["range"]))

        # Fallback
        return MoodState(mood="neutral", behavior="Écoute", jauge_range=(0, 100))

    def apply_action(self, current_jauge: int, action: str, action_type: str = "positive") -> JaugeModification:
        """
        Applique une action et retourne la modification.

        Args:
            current_jauge: Jauge actuelle
            action: Nom de l'action (ex: "good_listening_signal")
            action_type: "positive" ou "negative"

        Returns:
            JaugeModification avec le delta et la nouvelle valeur
        """
        modifier = self.modifiers.get(action_type, {}).get(action)

        if not modifier:
            return JaugeModification(action=action, delta=0, new_value=current_jauge, reason="Action non reconnue")

        # Appliquer la volatilité du niveau
        delta = int(modifier["points"] * self.volatility)

        # Vérifier les blockers
        if action in self.CONVERSION_BLOCKERS:
            if action == "denigrated_competitor":
                # Plafonner la jauge à 70
                new_value = min(current_jauge + delta, 70)
            else:
                new_value = max(0, min(100, current_jauge + delta))
        else:
            new_value = max(0, min(100, current_jauge + delta))

        return JaugeModification(action=action, delta=delta, new_value=new_value, reason=modifier["description"])

    def check_conversion_possible(
        self, jauge: int, blockers: list[str], required_conditions: list[str] = None, conditions_met: list[str] = None
    ) -> tuple[bool, list[str]]:
        """
        Vérifie si la conversion est possible.

        Returns:
            Tuple[bool, List[str]]: (conversion_possible, raisons_si_non)
        """
        reasons = []

        # Vérifier la jauge
        if jauge < self.conversion_threshold:
            reasons.append(f"Jauge insuffisante ({jauge}/{self.conversion_threshold})")

        # Vérifier les blockers
        for blocker in blockers:
            if blocker in self.CONVERSION_BLOCKERS:
                reasons.append(self.CONVERSION_BLOCKERS[blocker])

        # Vérifier les conditions requises
        if required_conditions and conditions_met:
            missing = set(required_conditions) - set(conditions_met)
            for m in missing:
                reasons.append(f"Condition manquante: {m}")

        return len(reasons) == 0, reasons

    def get_prospect_reaction(self, action: str, action_type: str) -> str | None:
        """Retourne la réaction du prospect à une action."""
        modifier = self.modifiers.get(action_type, {}).get(action)
        if modifier:
            return modifier.get("prospect_reaction")
        return None


class BehavioralDetector:
    """
    Détecte les patterns comportementaux dans le texte.
    """

    # Patterns de détection
    PATTERNS = {
        "reformulation": {
            "regex": r"(si je comprends|en d'autres termes|vous dites que|ce que j'entends|j'ai bien compris)",
            "type": "positive",
            "action": "relevant_reformulation",
        },
        "emotional_reformulation": {
            "regex": r"(je sens que|j'ai l'impression que|ça a l'air de|vous semblez)",
            "type": "positive",
            "action": "emotional_reformulation",
        },
        "open_question": {
            "regex": r"^\s*(qu'est-ce|comment|pourquoi|quand|qui|où|quel|quelle)",
            "type": "positive",
            "action": "good_open_question",
        },
        "empathy": {
            "regex": r"(je comprends|je vois|c'est normal|à votre place|je peux imaginer)",
            "type": "positive",
            "action": "empathy_shown",
        },
        "value_quantified": {
            "regex": r"(\d+\s*%|\d+\s*€|\d+\s*euros?|économiser|gagner|retour sur investissement|ROI)",
            "type": "positive",
            "action": "roi_quantified",
        },
        "listening_signal": {
            "regex": r"\b(je vois|d'accord|hmm|intéressant|je comprends|très bien|effectivement)\b",
            "type": "positive",
            "action": "good_listening_signal",
        },
        "denigration": {
            "regex": r"(ils sont (mauvais|nuls)|ne faites pas confiance|problèmes avec|concurrent.*mauvais)",
            "type": "negative",
            "action": "denigrated_competitor",
        },
        "immediate_discount": {
            "regex": r"(ok je fais|d'accord je baisse|je vous offre|je peux faire.*%\s*(de remise|moins))",
            "type": "negative",
            "action": "immediate_discount",
        },
        "pressure": {
            "regex": r"(c'est maintenant ou jamais|dernière chance|vous devez|il faut signer)",
            "type": "negative",
            "action": "aggressive_closing",
        },
        "defensive": {
            "regex": r"(ce n'est pas ma faute|calmez-vous|vous avez tort|mais non)",
            "type": "negative",
            "action": "defensive_reaction",
        },
    }

    # Indicateurs d'hésitation à compter
    HESITATION_WORDS = ["euh", "hum", "enfin", "donc", "voilà", "en fait", "bon", "bah"]

    def detect_patterns(self, text: str) -> dict:
        """
        Détecte tous les patterns dans le texte.

        Returns:
            {
                "positive": [{"pattern": str, "action": str}],
                "negative": [{"pattern": str, "action": str}],
                "indicators": {"hesitation_count": int, ...}
            }
        """
        text_lower = text.lower()

        result = {
            "positive": [],
            "negative": [],
            "indicators": {"hesitation_count": 0, "question_type": None, "word_count": len(text.split())},
        }

        # Compter les hésitations
        for word in self.HESITATION_WORDS:
            result["indicators"]["hesitation_count"] += text_lower.count(word)

        # Détecter les patterns
        for pattern_name, config in self.PATTERNS.items():
            if re.search(config["regex"], text_lower, re.IGNORECASE):
                if config["type"] == "positive":
                    result["positive"].append({"pattern": pattern_name, "action": config["action"]})
                elif config["type"] == "negative":
                    result["negative"].append({"pattern": pattern_name, "action": config["action"]})

        # Détecter le type de question
        if "?" in text:
            if re.search(r"^\s*(qu'est-ce|comment|pourquoi|quand|qui|où|quel)", text_lower):
                result["indicators"]["question_type"] = "open"
            else:
                result["indicators"]["question_type"] = "closed"

        return result

    def check_interruption(self, user_response_delay: float, prospect_was_speaking: bool) -> bool:
        """Vérifie si le commercial a coupé la parole."""
        return prospect_was_speaking and user_response_delay < 0.5

    def check_spoke_first_after_price(self, last_prospect_message: str, user_response_delay: float) -> bool:
        """Vérifie si le commercial a parlé en premier après annonce du prix."""
        price_mentioned = bool(
            re.search(r"(\d+\s*€|\d+\s*euros?|le prix|le tarif|ça coûte|ça fait)", last_prospect_message.lower())
        )
        return price_mentioned and user_response_delay < 2.0

    def detect_closed_question_spam(self, recent_questions: list[dict]) -> bool:
        """Détecte si le commercial enchaîne trop de questions fermées."""
        if len(recent_questions) < 3:
            return False

        last_three = recent_questions[-3:]
        closed_count = sum(1 for q in last_three if q.get("type") == "closed")
        return closed_count >= 3

    def detect_budget_question_too_early(self, text: str, message_count: int) -> bool:
        """Détecte si le budget est demandé trop tôt."""
        budget_patterns = r"(quel.*budget|votre budget|combien.*prévu|c'est combien)"
        if re.search(budget_patterns, text.lower()):
            # Trop tôt si moins de 4 échanges
            return message_count < 8
        return False
