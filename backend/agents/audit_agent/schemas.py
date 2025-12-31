"""
Schemas de donnees pour l'AuditAgent.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PerformanceLevel(Enum):
    EXCELLENT = "excellent"      # 85-100
    BON = "bon"                  # 70-84
    MOYEN = "moyen"              # 55-69
    INSUFFISANT = "insuffisant"  # 40-54
    CRITIQUE = "critique"        # 0-39


@dataclass
class SkillAnalysis:
    """Analyse d'une competence specifique."""
    skill_slug: str
    skill_name: str
    score: float                          # 0-100
    level: PerformanceLevel
    strengths: List[str]                  # Points forts observes
    weaknesses: List[str]                 # Points faibles observes
    specific_examples: List[Dict[str, str]]  # {"context": str, "action": str, "impact": str}
    improvement_priority: int             # 1 = haute priorite
    recommended_exercises: List[str]


@dataclass
class SessionAudit:
    """Audit complet d'une session."""
    session_id: int
    user_id: int
    timestamp: datetime

    # Scores globaux
    overall_score: float                  # 0-100
    performance_level: PerformanceLevel

    # Analyse par competence
    skill_scores: Dict[str, Any]

    # Analyse comportementale
    behavioral_analysis: Dict[str, Any]   # Patterns detectes
    emotional_intelligence_score: float   # 0-100
    adaptability_score: float             # 0-100

    # Comparaison champion
    champion_alignment: float             # % alignement avec les patterns champion
    champion_gaps: List[str]              # Techniques manquantes vs champion

    # Moments cles
    turning_points: List[Dict[str, Any]]  # Moments qui ont fait basculer la jauge
    missed_opportunities: List[Dict[str, Any]]  # Opportunites ratees
    excellent_moments: List[Dict[str, Any]]     # Moments excellents

    # Feedback
    summary: str                          # Resume en 2-3 phrases
    top_strength: str
    top_weakness: str
    immediate_action: str                 # Une action concrete a faire maintenant

    # Meta
    audit_confidence: float               # Confiance dans l'analyse (0-1)
    audit_model: str                      # Modele utilise pour l'audit


@dataclass
class UserProgressReport:
    """Rapport de progression utilisateur (multi-sessions)."""
    user_id: int
    period_start: datetime
    period_end: datetime
    sessions_analyzed: int

    # Progression globale
    overall_trend: str                    # "improving", "stable", "declining"
    score_evolution: List[Dict[str, Any]] # [{date, score}]
    avg_score_period: float
    best_session_id: int
    worst_session_id: int

    # Progression par skill
    skill_progression: Dict[str, Dict[str, Any]]  # {skill: {start_score, end_score, trend}}
    skills_mastered: List[str]            # Skills >= 80%
    skills_struggling: List[str]          # Skills < 60%

    # Patterns comportementaux
    consistent_strengths: List[str]       # Forces constantes
    persistent_weaknesses: List[str]      # Faiblesses recurrentes
    improvement_velocity: float           # Vitesse d'amelioration

    # Recommandations
    focus_areas: List[str]                # Top 3 priorites
    recommended_path: List[Dict[str, Any]]  # Parcours suggere
    estimated_mastery_date: Optional[datetime]  # Estimation niveau expert

    # Comparaison
    percentile_rank: float                # Classement vs autres users (0-100)
    comparison_to_average: float          # % au-dessus/dessous moyenne


@dataclass
class ChampionComparison:
    """Comparaison detaillee avec un champion."""
    user_id: int
    champion_id: str

    # Scores de similarite
    overall_similarity: float             # 0-100
    technique_similarity: float           # Techniques utilisees
    tone_similarity: float                # Style de communication
    timing_similarity: float              # Gestion du temps/silences

    # Gaps specifiques
    missing_techniques: List[Dict[str, Any]]  # Techniques du champion non utilisees
    overused_techniques: List[str]        # Techniques trop utilisees

    # Recommandations
    techniques_to_adopt: List[Dict[str, Any]]  # {technique, priority, example}
    habits_to_break: List[str]


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
    score_vs_last_week: float             # +/- %
    new_skills_unlocked: List[str]
    achievements: List[str]               # Badges gagnes

    # Focus semaine prochaine
    weekly_goal: str
    daily_tips: List[str]                 # 7 tips, un par jour

    # Motivation
    motivational_message: str
    streak_days: int
