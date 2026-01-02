"""
Schemas de donnees pour l'AuditAgent.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class PerformanceLevel(Enum):
    EXCELLENT = "excellent"  # 85-100
    BON = "bon"  # 70-84
    MOYEN = "moyen"  # 55-69
    INSUFFISANT = "insuffisant"  # 40-54
    CRITIQUE = "critique"  # 0-39


@dataclass
class SkillAnalysis:
    """Analyse d'une competence specifique."""

    skill_slug: str
    skill_name: str
    score: float  # 0-100
    level: PerformanceLevel
    strengths: list[str]  # Points forts observes
    weaknesses: list[str]  # Points faibles observes
    specific_examples: list[dict[str, str]]  # {"context": str, "action": str, "impact": str}
    improvement_priority: int  # 1 = haute priorite
    recommended_exercises: list[str]


@dataclass
class SessionAudit:
    """Audit complet d'une session."""

    session_id: int
    user_id: int
    timestamp: datetime

    # Scores globaux
    overall_score: float  # 0-100
    performance_level: PerformanceLevel

    # Analyse par competence
    skill_scores: dict[str, Any]

    # Analyse comportementale
    behavioral_analysis: dict[str, Any]  # Patterns detectes
    emotional_intelligence_score: float  # 0-100
    adaptability_score: float  # 0-100

    # Comparaison champion
    champion_alignment: float  # % alignement avec les patterns champion
    champion_gaps: list[str]  # Techniques manquantes vs champion

    # Moments cles
    turning_points: list[dict[str, Any]]  # Moments qui ont fait basculer la jauge
    missed_opportunities: list[dict[str, Any]]  # Opportunites ratees
    excellent_moments: list[dict[str, Any]]  # Moments excellents

    # Feedback
    summary: str  # Resume en 2-3 phrases
    top_strength: str
    top_weakness: str
    immediate_action: str  # Une action concrete a faire maintenant

    # Meta
    audit_confidence: float  # Confiance dans l'analyse (0-1)
    audit_model: str  # Modele utilise pour l'audit


@dataclass
class UserProgressReport:
    """Rapport de progression utilisateur (multi-sessions)."""

    user_id: int
    period_start: datetime
    period_end: datetime
    sessions_analyzed: int

    # Progression globale
    overall_trend: str  # "improving", "stable", "declining"
    score_evolution: list[dict[str, Any]]  # [{date, score}]
    avg_score_period: float
    best_session_id: int
    worst_session_id: int

    # Progression par skill
    skill_progression: dict[str, dict[str, Any]]  # {skill: {start_score, end_score, trend}}
    skills_mastered: list[str]  # Skills >= 80%
    skills_struggling: list[str]  # Skills < 60%

    # Patterns comportementaux
    consistent_strengths: list[str]  # Forces constantes
    persistent_weaknesses: list[str]  # Faiblesses recurrentes
    improvement_velocity: float  # Vitesse d'amelioration

    # Recommandations
    focus_areas: list[str]  # Top 3 priorites
    recommended_path: list[dict[str, Any]]  # Parcours suggere
    estimated_mastery_date: datetime | None  # Estimation niveau expert

    # Comparaison
    percentile_rank: float  # Classement vs autres users (0-100)
    comparison_to_average: float  # % au-dessus/dessous moyenne


@dataclass
class ChampionComparison:
    """Comparaison detaillee avec un champion."""

    user_id: int
    champion_id: str

    # Scores de similarite
    overall_similarity: float  # 0-100
    technique_similarity: float  # Techniques utilisees
    tone_similarity: float  # Style de communication
    timing_similarity: float  # Gestion du temps/silences

    # Gaps specifiques
    missing_techniques: list[dict[str, Any]]  # Techniques du champion non utilisees
    overused_techniques: list[str]  # Techniques trop utilisees

    # Recommandations
    techniques_to_adopt: list[dict[str, Any]]  # {technique, priority, example}
    habits_to_break: list[str]


@dataclass
class WeeklyDigest:
    """Digest hebdomadaire pour l'utilisateur."""

    user_id: int
    week_number: int
    year: int

    # Stats de la semaine
    sessions_completed: int
    total_training_minutes: int
    avg_score: float
    best_moment: str

    # Progression
    score_vs_last_week: float  # +/- %
    new_skills_unlocked: list[str]
    achievements: list[str]  # Badges gagnes

    # Focus semaine prochaine
    weekly_goal: str
    daily_tips: list[str]  # 7 tips, un par jour

    # Motivation
    motivational_message: str
    streak_days: int
