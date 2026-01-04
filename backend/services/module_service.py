"""
Service de gestion des modules de formation.

Gère le chargement des modules YAML (BEBEDC, SPIN, etc.)
et l'évaluation des sessions selon les critères du module.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml


def normalize_text(text: str) -> str:
    """Normalise le texte en supprimant les accents pour une meilleure detection."""
    # Decomposer les caracteres accentues
    normalized = unicodedata.normalize("NFD", text)
    # Supprimer les marques diacritiques (accents)
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return without_accents.lower()


@dataclass
class ChecklistItem:
    """Element de checklist d'un module."""

    id: str
    label: str
    description: str
    question_hint: str
    detection_patterns: list[str]
    weight: int
    required: bool = True
    detected: bool = False
    detection_quality: str = "none"  # none | basic | good | excellent


@dataclass
class ModuleEvaluation:
    """Resultat d'evaluation d'une session selon un module."""

    module_id: str
    module_name: str
    elements_detected: list[dict]
    elements_missing: list[dict]
    score: int
    max_score: int
    mastery_achieved: bool
    level: str  # excellent | good | partial | insufficient
    level_description: str
    risks: list[dict]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "elements_detected": self.elements_detected,
            "elements_missing": self.elements_missing,
            "score": self.score,
            "max_score": self.max_score,
            "mastery_achieved": self.mastery_achieved,
            "level": self.level,
            "level_description": self.level_description,
            "risks": self.risks,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FinalResult:
    """Resultat final combinant module et closing."""

    module_success: bool
    closing_success: bool
    result_key: str
    label: str
    emoji: str
    message: str

    def to_dict(self) -> dict:
        return {
            "module_success": self.module_success,
            "closing_success": self.closing_success,
            "result_key": self.result_key,
            "label": self.label,
            "emoji": self.emoji,
            "message": self.message,
        }


class ModuleService:
    """
    Gère les modules de formation (BEBEDC, SPIN, etc.)
    """

    # Cache des modules charges
    _cache: dict[str, dict] = {}

    # Chemin par defaut des modules
    MODULES_PATH = Path(__file__).parent.parent / "training_modules"

    def __init__(self, modules_path: Path | None = None):
        if modules_path:
            self.modules_path = modules_path
        else:
            self.modules_path = self.MODULES_PATH

    async def load_module(self, module_id: str) -> dict:
        """
        Charge un module depuis un fichier YAML.

        Args:
            module_id: Identifiant du module (ex: "bebedc", "spin_selling")

        Returns:
            Dictionnaire du module charge

        Raises:
            FileNotFoundError: Si le module n'existe pas
            ValueError: Si le module est mal forme
        """
        # Verifier le cache
        if module_id in self._cache:
            return self._cache[module_id]

        # Construire le chemin
        module_file = self.modules_path / f"{module_id}.yaml"

        if not module_file.exists():
            raise FileNotFoundError(f"Module '{module_id}' not found at {module_file}")

        # Charger le YAML
        with open(module_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Valider la structure
        if "module" not in data:
            raise ValueError(f"Module '{module_id}' missing 'module' key")

        module = data["module"]

        required_fields = ["id", "name", "checklist", "evaluation"]
        for f_name in required_fields:
            if f_name not in module:
                raise ValueError(f"Module '{module_id}' missing required field '{f_name}'")

        # Mettre en cache
        self._cache[module_id] = module

        return module

    def load_module_sync(self, module_id: str) -> dict:
        """Version synchrone de load_module."""
        if module_id in self._cache:
            return self._cache[module_id]

        module_file = self.modules_path / f"{module_id}.yaml"

        if not module_file.exists():
            raise FileNotFoundError(f"Module '{module_id}' not found at {module_file}")

        with open(module_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if "module" not in data:
            raise ValueError(f"Module '{module_id}' missing 'module' key")

        module = data["module"]
        self._cache[module_id] = module
        return module

    async def list_modules(self) -> list[dict]:
        """Liste tous les modules disponibles."""
        modules = []

        if not self.modules_path.exists():
            return modules

        for file in self.modules_path.glob("*.yaml"):
            try:
                module = await self.load_module(file.stem)
                modules.append(
                    {
                        "id": module["id"],
                        "name": module["name"],
                        "description": module.get("description", ""),
                        "category": module.get("category", "general"),
                    }
                )
            except (FileNotFoundError, ValueError):
                continue

        return modules

    def detect_element(self, text: str, patterns: list[str]) -> tuple[bool, str]:
        """
        Detecte si un element est present dans le texte.

        Args:
            text: Texte a analyser
            patterns: Liste de patterns regex a rechercher

        Returns:
            Tuple[bool, str]: (element detecte, qualite de la detection)
        """
        # Normaliser le texte (supprime les accents pour meilleure detection)
        text_normalized = normalize_text(text)

        for pattern in patterns:
            # Normaliser aussi le pattern pour matcher sans accents
            pattern_normalized = normalize_text(pattern)
            if re.search(pattern_normalized, text_normalized, re.IGNORECASE):
                # Evaluer la qualite
                if "?" in text:
                    # C'est une question -> bonne qualite
                    return True, "good"
                else:
                    # Affirmation ou reponse -> qualite basique
                    return True, "basic"

        return False, "none"

    async def evaluate_message(
        self,
        module: dict,
        message: str,
        history: list[dict],
        current_progress: dict | None = None,
    ) -> dict:
        """
        Evalue un message selon les criteres du module.

        Args:
            module: Le module charge
            message: Message de l'utilisateur
            history: Historique de la conversation
            current_progress: Progres actuel (elements deja detectes)

        Returns:
            Dictionnaire avec les elements detectes et le score partiel
        """
        if current_progress is None:
            current_progress = {"detected": [], "scores": {}}

        detected_in_message = []
        checklist = module.get("checklist", [])
        scoring = module.get("evaluation", {}).get("scoring", {})

        per_element_base = scoring.get("per_element_base", 10)
        quality_bonus = scoring.get("quality_bonus", 5)

        for item in checklist:
            item_id = item["id"]

            # Si deja detecte, passer
            if item_id in current_progress["detected"]:
                continue

            # Detecter
            detected, quality = self.detect_element(message, item.get("detection_patterns", []))

            if detected:
                current_progress["detected"].append(item_id)
                detected_in_message.append(
                    {
                        "id": item_id,
                        "label": item["label"],
                        "quality": quality,
                    }
                )

                # Calculer le score
                score = per_element_base
                if quality == "good":
                    score += quality_bonus
                elif quality == "excellent":
                    score += quality_bonus * 2

                current_progress["scores"][item_id] = score

        return {
            "detected": detected_in_message,
            "total_detected": len(current_progress["detected"]),
            "total_elements": len(checklist),
            "current_score": sum(current_progress["scores"].values()),
            "progress": current_progress,
        }

    async def evaluate_session(
        self,
        module: dict,
        messages: list[dict],
        session_data: dict | None = None,
    ) -> ModuleEvaluation:
        """
        Evalue une session complete selon les criteres du module.

        Args:
            module: Le module charge
            messages: Liste des messages de la session
            session_data: Donnees supplementaires de session

        Returns:
            ModuleEvaluation avec le score et les elements detectes/manquants
        """
        checklist = module.get("checklist", [])
        evaluation_config = module.get("evaluation", {})
        scoring = evaluation_config.get("scoring", {})
        levels = evaluation_config.get("levels", {})
        risks_config = module.get("risks_if_missing", {})

        per_element_base = scoring.get("per_element_base", 10)
        quality_bonus = scoring.get("quality_bonus", 5)
        mastery_threshold = evaluation_config.get("mastery_threshold", 70)

        # Analyser tous les messages utilisateur
        user_messages = [m for m in messages if m.get("role") == "user"]
        combined_text = " ".join([m.get("content", "") for m in user_messages])

        elements_detected = []
        elements_missing = []
        total_score = 0
        max_score = 0

        for item in checklist:
            item_id = item["id"]
            weight = item.get("weight", per_element_base)
            max_score += weight

            # Detecter l'element
            detected, quality = self.detect_element(combined_text, item.get("detection_patterns", []))

            if detected:
                score = weight
                if quality == "good":
                    score = min(weight + quality_bonus, weight * 1.5)
                elif quality == "excellent":
                    score = min(weight + quality_bonus * 2, weight * 2)

                total_score += score
                elements_detected.append(
                    {
                        "id": item_id,
                        "label": item["label"],
                        "description": item["description"],
                        "quality": quality,
                        "score": int(score),
                    }
                )
            else:
                elements_missing.append(
                    {
                        "id": item_id,
                        "label": item["label"],
                        "description": item["description"],
                        "required": item.get("required", True),
                        "question_hint": item.get("question_hint", ""),
                    }
                )

        # Calculer le score normalise sur 100 (plafonner a 100)
        normalized_score = min(100, int((total_score / max_score) * 100)) if max_score > 0 else 0
        mastery_achieved = normalized_score >= mastery_threshold

        # Determiner le niveau (trier par min_score decroissant pour matcher le meilleur)
        level = "insufficient"
        level_description = ""
        sorted_levels = sorted(levels.items(), key=lambda x: x[1].get("min_score", 0), reverse=True)
        for level_name, level_config in sorted_levels:
            min_score = level_config.get("min_score", 0)
            elements_required = level_config.get("elements_required", 0)

            if normalized_score >= min_score and len(elements_detected) >= elements_required:
                level = level_name
                level_description = level_config.get("description", "")
                break

        # Construire les risques
        risks = []
        for missing in elements_missing:
            if missing["required"] and missing["id"] in risks_config:
                risk_info = risks_config[missing["id"]]
                risks.append(
                    {
                        "element": missing["id"],
                        "label": missing["label"],
                        "risk": risk_info.get("risk", ""),
                        "consequence": risk_info.get("consequence", ""),
                        "coaching_tip": risk_info.get("coaching_tip", ""),
                    }
                )

        return ModuleEvaluation(
            module_id=module["id"],
            module_name=module["name"],
            elements_detected=elements_detected,
            elements_missing=elements_missing,
            score=normalized_score,
            max_score=100,
            mastery_achieved=mastery_achieved,
            level=level,
            level_description=level_description,
            risks=risks,
        )

    def calculate_final_result(
        self,
        module_score: int,
        module_threshold: int,
        closing: bool,
        module: dict | None = None,
    ) -> FinalResult:
        """
        Calcule le resultat final selon la matrice module x closing.

        Args:
            module_score: Score du module (0-100)
            module_threshold: Seuil de maitrise
            closing: True si le closing a ete obtenu
            module: Module pour recuperer les messages personnalises

        Returns:
            FinalResult avec le resultat combine
        """
        module_success = module_score >= module_threshold

        # Matrice de resultats
        result_matrix = module.get("result_matrix", {}) if module else {}

        if module_success and closing:
            key = "module_success_closing_success"
            default = {
                "label": "VICTOIRE COMPLETE",
                "emoji": "trophy",
                "message": "Bravo ! Qualification et closing reussis.",
            }
        elif module_success and not closing:
            key = "module_success_closing_fail"
            default = {
                "label": "QUALIFICATION OK",
                "emoji": "target",
                "message": "Bonne qualification mais closing a travailler.",
            }
        elif not module_success and closing:
            key = "module_fail_closing_success"
            default = {
                "label": "CHANCE - RISQUE",
                "emoji": "warning",
                "message": "Closing obtenu mais qualification incomplete. Risque eleve.",
            }
        else:
            key = "module_fail_closing_fail"
            default = {
                "label": "ECHEC",
                "emoji": "cross",
                "message": "Ni qualification ni closing. A retravailler.",
            }

        result_config = result_matrix.get(key, default)

        return FinalResult(
            module_success=module_success,
            closing_success=closing,
            result_key=key,
            label=result_config.get("label", default["label"]),
            emoji=result_config.get("emoji", default["emoji"]),
            message=result_config.get("message", default["message"]),
        )

    async def generate_report(
        self,
        module: dict,
        evaluation: ModuleEvaluation,
        session: dict,
        result: FinalResult | None = None,
    ) -> dict:
        """
        Genere le rapport final de session.

        Args:
            module: Le module utilise
            evaluation: L'evaluation de la session
            session: Donnees de la session
            result: Resultat final (module x closing)

        Returns:
            Rapport complet de la session
        """
        feedback_templates = module.get("feedback_templates", {})

        # Construire le feedback pour les elements detectes
        detected_feedback = []
        for elem in evaluation.elements_detected:
            if elem["quality"] in ["good", "excellent"]:
                template = feedback_templates.get("element_detected", {}).get(
                    "with_quality", "Excellent travail sur {element}."
                )
            else:
                template = feedback_templates.get("element_detected", {}).get("positive", "Bien identifie : {element}.")
            detected_feedback.append(
                {
                    "element": elem["label"],
                    "feedback": template.format(element=elem["label"]),
                    "quality": elem["quality"],
                }
            )

        # Construire le feedback pour les elements manquants
        missing_feedback = []
        for elem in evaluation.elements_missing:
            if elem["required"]:
                template = feedback_templates.get("element_missing", {}).get(
                    "direct", "ATTENTION : {element} non qualifie."
                )
            else:
                template = feedback_templates.get("element_missing", {}).get("gentle", "Pensez a explorer {element}.")

            risk_info = next((r for r in evaluation.risks if r["element"] == elem["id"]), None)

            missing_feedback.append(
                {
                    "element": elem["label"],
                    "feedback": template.format(element=elem["label"], risk=risk_info["risk"] if risk_info else ""),
                    "hint": elem.get("question_hint", ""),
                    "risk": risk_info,
                }
            )

        # Recommendations
        recommendations = []
        for risk in evaluation.risks[:3]:  # Top 3 risques
            if risk.get("coaching_tip"):
                recommendations.append(
                    {
                        "priority": "high" if risk["element"] in ["besoin", "enjeu", "decideur"] else "medium",
                        "element": risk["element"],
                        "tip": risk["coaching_tip"],
                    }
                )

        report = {
            "module": {
                "id": module["id"],
                "name": module["name"],
                "category": module.get("category", "general"),
            },
            "summary": {
                "score": evaluation.score,
                "max_score": evaluation.max_score,
                "level": evaluation.level,
                "level_description": evaluation.level_description,
                "mastery_achieved": evaluation.mastery_achieved,
                "elements_detected_count": len(evaluation.elements_detected),
                "elements_total_count": len(evaluation.elements_detected) + len(evaluation.elements_missing),
            },
            "detected": detected_feedback,
            "missing": missing_feedback,
            "risks": evaluation.risks,
            "recommendations": recommendations,
            "session": {
                "id": session.get("id"),
                "duration": session.get("duration"),
                "message_count": session.get("message_count"),
                "jauge_final": session.get("jauge", {}).get("value"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        if result:
            report["final_result"] = result.to_dict()

        return report

    def clear_cache(self) -> None:
        """Vide le cache des modules."""
        self._cache.clear()

    async def get_prospect_instructions(self, module_id: str) -> str:
        """
        Recupere les instructions pour le prospect d'un module.

        Args:
            module_id: Identifiant du module

        Returns:
            Instructions pour le prospect
        """
        module = await self.load_module(module_id)
        return module.get("prospect_instructions", "")
