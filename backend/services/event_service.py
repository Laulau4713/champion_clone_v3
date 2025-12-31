"""
Service d'événements situationnels et retournements V2.

Ce service gère:
- Les événements situationnels (interruptions, pression temporelle, etc.)
- Les retournements de situation (last minute bomb, price attack, etc.)
- Les indices comportementaux du prospect
"""

import random
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class SituationalEvent:
    """Événement situationnel."""
    type: str
    prospect_says: str
    test: str
    good_response_bonus: int
    bad_response_penalty: int
    is_test: bool = False
    adds_interlocutor: Optional[dict] = None


@dataclass
class Reversal:
    """Retournement de situation."""
    type: str
    prospect_says: str
    impact: str
    jauge_drop: int
    reveals: Optional[str] = None
    is_fake: bool = False
    test: Optional[str] = None


class EventService:
    """
    Gère les événements situationnels et retournements.
    """

    SITUATIONAL_EVENTS = {
        "easy": [],  # Pas d'événements en facile
        "medium": [
            {
                "type": "phone_interruption",
                "trigger": "random",
                "probability": 0.2,
                "prospect_says": "Excusez-moi, j'ai un autre appel... (revient) Bon, où on en était?",
                "test": "Le commercial résume brièvement et reprend le fil",
                "good_response_bonus": 5,
                "bad_response_penalty": -3
            },
            {
                "type": "time_pressure",
                "trigger": "random",
                "probability": 0.15,
                "prospect_says": "Je dois y aller dans 5 minutes. On peut accélérer?",
                "test": "Le commercial priorise et va à l'essentiel",
                "good_response_bonus": 6,
                "bad_response_penalty": -4
            },
            {
                "type": "distraction",
                "trigger": "random",
                "probability": 0.1,
                "prospect_says": "Pardon, j'ai dû gérer un truc. Vous pouvez répéter le dernier point?",
                "test": "Le commercial répète sans s'énerver",
                "good_response_bonus": 3,
                "bad_response_penalty": -2
            }
        ],
        "expert": [
            {
                "type": "aggressive_interruption",
                "trigger": "random",
                "probability": 0.3,
                "prospect_says": "Stop stop stop. Vous me faites perdre mon temps là.",
                "test": "Le commercial reste calme et recadre positivement",
                "good_response_bonus": 8,
                "bad_response_penalty": -12
            },
            {
                "type": "competitor_mention",
                "trigger": "during_value_proposition",
                "probability": 0.25,
                "prospect_says": "[Concurrent] m'a proposé la même chose 30% moins cher.",
                "test": "Le commercial ne dénigre pas et recentre sur la valeur",
                "good_response_bonus": 8,
                "bad_response_penalty": -10
            },
            {
                "type": "power_play",
                "trigger": "random",
                "probability": 0.2,
                "prospect_says": "Écoutez, j'ai 50 commerciaux comme vous qui m'appellent chaque semaine.",
                "test": "Le commercial reste assertif sans être arrogant",
                "good_response_bonus": 7,
                "bad_response_penalty": -8
            },
            {
                "type": "phone_on_speaker",
                "trigger": "start_of_call",
                "probability": 0.15,
                "prospect_says": "Je vous mets sur haut-parleur, mon collègue Marc écoute.",
                "test": "Le commercial s'adapte aux deux interlocuteurs",
                "good_response_bonus": 5,
                "bad_response_penalty": -5,
                "adds_interlocutor": {"name": "Marc", "personality": "skeptical_technical"}
            },
            {
                "type": "sudden_time_pressure",
                "trigger": "when_gauge_high",
                "probability": 0.2,
                "prospect_says": "Mon prochain rendez-vous arrive dans 2 minutes. Conclusion?",
                "test": "Le commercial fait un closing éclair efficace",
                "good_response_bonus": 10,
                "bad_response_penalty": -8
            },
            {
                "type": "fake_objection_test",
                "trigger": "after_good_argument",
                "probability": 0.2,
                "prospect_says": "Mouais, je ne suis pas convaincu. (teste le commercial)",
                "test": "Le commercial tient sa position sans s'effondrer",
                "good_response_bonus": 8,
                "bad_response_penalty": -10,
                "is_test": True
            },
            {
                "type": "emotional_bait",
                "trigger": "random",
                "probability": 0.15,
                "prospect_says": "Vous êtes tous les mêmes, vous promettez la lune!",
                "test": "Le commercial ne mord pas à l'hameçon émotionnel",
                "good_response_bonus": 8,
                "bad_response_penalty": -12
            }
        ]
    }

    REVERSALS = {
        "easy": [],  # Pas de retournements en facile
        "medium": [
            {
                "type": "last_minute_doubt",
                "trigger_gauge": 75,
                "probability": 0.2,
                "prospect_says": "Attendez, en fait je me demande si c'est vraiment le bon moment...",
                "gauge_drop": 10,
                "test": "Le commercial rassure sans presser"
            }
        ],
        "expert": [
            {
                "type": "last_minute_bomb",
                "trigger_gauge": 80,
                "probability": 0.3,
                "prospect_says": "Avant de finaliser, il y a quelque chose que je ne vous ai pas dit...",
                "gauge_drop": 25,
                "reveals": "major_hidden_objection"
            },
            {
                "type": "price_attack_at_close",
                "trigger_gauge": 85,
                "probability": 0.35,
                "prospect_says": "OK je suis prêt à signer. Mais à -25%.",
                "gauge_drop": 0,
                "test": "Le commercial ne cède pas sans contrepartie"
            },
            {
                "type": "ghost_decision_maker",
                "trigger_gauge": 75,
                "probability": 0.25,
                "prospect_says": "En fait, ce n'est pas moi qui signe. C'est mon DG, et il est difficile...",
                "gauge_drop": 15,
                "impact": "Must re-qualify and prepare champion"
            },
            {
                "type": "fake_competitor_offer",
                "trigger_gauge": 70,
                "probability": 0.2,
                "prospect_says": "J'ai [concurrent] qui vient de m'envoyer une offre 40% en dessous.",
                "gauge_drop": 0,
                "is_fake": True,
                "test": "Le commercial reste calme et creuse sans paniquer"
            }
        ]
    }

    # Indices comportementaux par état
    BEHAVIORAL_CUES = {
        "hostile": ["(soupir)", "(regarde l'heure)", "(ton agacé)", "(tape du pied)"],
        "aggressive": ["(ton sec)", "(bras croisés)", "(moue)"],
        "skeptical": ["(bras croisés)", "(sourcils froncés)", "(ton sceptique)", "(silence)"],
        "resistant": ["(hésitant)", "(évasif)", "(distant)"],
        "neutral": ["(écoute)", "(attentif)", "(pensif)"],
        "interested": ["(prend des notes)", "(hochement de tête)", "(ton plus posé)", "(se penche en avant)"],
        "ready_to_buy": ["(sourire)", "(enthousiaste)", "(ton engagé)", "(impatient de commencer)"]
    }

    # Indices basés sur le delta de jauge
    DELTA_CUES = {
        "positive": ["(ton plus ouvert)", "(intéressé)", "(se détend)", "(sourire)"],
        "negative": ["(se recule)", "(moue dubitative)", "(ton plus froid)", "(regarde ailleurs)"]
    }


    def __init__(self, level: str = "easy", level_config: dict = None):
        self.level = level
        self.level_config = level_config or {}
        self._load_events()
        self.triggered_events: List[str] = []
        self.reversal_triggered = False

    def _load_events(self):
        """Charge les événements depuis la config ou utilise les défauts."""
        # Événements situationnels
        if self.level_config.get("situational_events", {}).get("enabled"):
            events_config = self.level_config.get("situational_events", {}).get("events", [])
            self.events = events_config if events_config else self.SITUATIONAL_EVENTS.get(self.level, [])
        else:
            self.events = self.SITUATIONAL_EVENTS.get(self.level, [])

        # Retournements
        if self.level_config.get("reversals", {}).get("enabled"):
            reversals_config = self.level_config.get("reversals", {}).get("types", [])
            self.reversals = reversals_config if reversals_config else self.REVERSALS.get(self.level, [])
        else:
            self.reversals = self.REVERSALS.get(self.level, [])

    def should_trigger_event(
        self,
        message_count: int,
        jauge: int,
        context: str = "random"
    ) -> Optional[SituationalEvent]:
        """
        Décide si un événement doit se déclencher.

        Args:
            message_count: Nombre de messages échangés
            jauge: Jauge actuelle
            context: Contexte ("random", "after_good_argument", etc.)

        Returns:
            SituationalEvent si déclenché, None sinon
        """
        if not self.events:
            return None

        # Pas d'événement dans les 3 premiers échanges
        if message_count < 6:
            return None

        # Filtrer les événements applicables
        applicable = []
        for event in self.events:
            if event["type"] in self.triggered_events:
                continue  # Déjà déclenché

            trigger = event.get("trigger", "random")
            if trigger == "random" or trigger == context:
                if trigger == "when_jauge_high" and jauge < 60:
                    continue
                applicable.append(event)

        if not applicable:
            return None

        # Choisir un événement selon les probabilités
        for event in applicable:
            if random.random() < event.get("probability", 0.1):
                self.triggered_events.append(event["type"])
                return SituationalEvent(
                    type=event["type"],
                    prospect_says=event["prospect_says"],
                    test=event.get("test", ""),
                    good_response_bonus=event.get("good_response_bonus", 5),
                    bad_response_penalty=event.get("bad_response_penalty", -5),
                    is_test=event.get("is_test", False),
                    adds_interlocutor=event.get("adds_interlocutor")
                )

        return None

    def should_trigger_reversal(
        self,
        jauge: int,
        closing_attempted: bool = False
    ) -> Optional[Reversal]:
        """
        Décide si un retournement doit se déclencher.
        """
        if self.reversal_triggered:
            return None

        if not self.reversals:
            return None

        for reversal in self.reversals:
            trigger_jauge = reversal.get("trigger_gauge", 75)

            if jauge >= trigger_jauge:
                # Certains retournements nécessitent une tentative de closing
                reversal_type = reversal.get("type", "")
                if "close" in reversal_type.lower() and not closing_attempted:
                    continue

                if random.random() < reversal.get("probability", 0.2):
                    self.reversal_triggered = True
                    return Reversal(
                        type=reversal["type"],
                        prospect_says=reversal["prospect_says"],
                        impact=reversal.get("impact", ""),
                        jauge_drop=reversal.get("gauge_drop", 0),
                        reveals=reversal.get("reveals"),
                        is_fake=reversal.get("is_fake", False),
                        test=reversal.get("test")
                    )

        return None

    def get_behavioral_cue(self, mood: str, jauge_delta: int = 0) -> Optional[str]:
        """
        Retourne un indice comportemental basé sur l'état actuel.

        Args:
            mood: Humeur actuelle du prospect
            jauge_delta: Changement de jauge au dernier message

        Returns:
            Indice comme "(soupir)" ou "(prend des notes)"
        """
        cues = []

        # Basé sur l'humeur
        mood_cues = self.BEHAVIORAL_CUES.get(mood, [])
        if mood_cues:
            cues.extend(mood_cues)

        # Basé sur le delta
        if jauge_delta >= 5:
            cues.extend(self.DELTA_CUES["positive"])
        elif jauge_delta <= -5:
            cues.extend(self.DELTA_CUES["negative"])

        if cues:
            return random.choice(cues)
        return None

    def evaluate_event_response(
        self,
        event: SituationalEvent,
        user_response: str,
        patterns_detected: dict
    ) -> dict:
        """
        Évalue la réponse du commercial à un événement.

        Returns:
            {
                "handled_well": bool,
                "jauge_impact": int,
                "feedback": str
            }
        """
        # Logique simplifiée - en production, utiliser Claude pour évaluer
        handled_well = False
        jauge_impact = event.bad_response_penalty

        # Critères basiques selon le type d'événement
        if event.type == "aggressive_interruption":
            # Vérifie si le commercial reste calme (pas de patterns négatifs)
            if not patterns_detected.get("negative"):
                if patterns_detected.get("positive"):
                    handled_well = True
                    jauge_impact = event.good_response_bonus

        elif event.type == "competitor_mention":
            # Vérifie que le commercial ne dénigre pas
            negative_actions = [p["action"] for p in patterns_detected.get("negative", [])]
            if "denigrated_competitor" not in negative_actions:
                positive_actions = [p["action"] for p in patterns_detected.get("positive", [])]
                if any(a in positive_actions for a in ["value_demonstrated", "roi_quantified"]):
                    handled_well = True
                    jauge_impact = event.good_response_bonus

        elif event.type == "time_pressure" or event.type == "sudden_time_pressure":
            # Vérifie que le commercial priorise
            word_count = patterns_detected.get("indicators", {}).get("word_count", 0)
            if word_count < 50:  # Réponse concise
                handled_well = True
                jauge_impact = event.good_response_bonus

        elif event.type == "fake_objection_test":
            # Vérifie que le commercial tient sa position
            positive_actions = [p["action"] for p in patterns_detected.get("positive", [])]
            if any(a in positive_actions for a in ["stayed_calm_under_pressure", "assertive_reframe"]):
                handled_well = True
                jauge_impact = event.good_response_bonus

        else:
            # Pour les autres événements, on regarde le ratio positif/négatif
            pos_count = len(patterns_detected.get("positive", []))
            neg_count = len(patterns_detected.get("negative", []))
            if pos_count > neg_count:
                handled_well = True
                jauge_impact = event.good_response_bonus

        return {
            "handled_well": handled_well,
            "jauge_impact": jauge_impact,
            "feedback": f"{'Bien géré!' if handled_well else 'Attention: ' + event.test}"
        }

    def get_hidden_objection(
        self,
        level_config: dict,
        persona_objections: List[dict] = None
    ) -> Optional[dict]:
        """
        Sélectionne une objection cachée selon la config du niveau.

        Returns:
            Objection cachée ou None
        """
        hidden_config = level_config.get("hidden_objections", {})

        if not hidden_config.get("enabled"):
            return None

        probability = hidden_config.get("probability", 0.3)
        if random.random() > probability:
            return None

        # Prendre depuis la config du niveau ou les objections du persona
        types = hidden_config.get("types", [])

        if persona_objections:
            types = types + persona_objections

        if not types:
            return None

        selected = random.choice(types)
        return {
            "expressed": selected.get("expressed"),
            "hidden": selected.get("hidden"),
            "discovery_questions": selected.get("discovery_questions", []),
            "discovered": False
        }
