"""
Service de gestion des playbooks commerciaux.

Un playbook contient toutes les informations nécessaires pour vendre un produit :
- Entreprise et positionnement
- Produit (problème, solution, bénéfices, pricing)
- Pitch commercial (hooks, questions discovery, phrases clés)
- Réponses aux objections avec preuves

Ce service remplace l'ancien scenario_loader.py et fournit une structure
plus riche et orientée VENDEUR plutôt que PROSPECT.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Company:
    """Informations sur l'entreprise vendeuse."""

    name: str
    baseline: str = ""
    sector: str = ""
    positioning: str = ""
    founded: str = ""
    size: str = ""
    location: str = ""


@dataclass
class Problem:
    """Problème que le produit résout."""

    title: str
    description: str = ""
    impacts: list[str] = field(default_factory=list)
    pains_by_persona: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class HowItWorks:
    """Comment le produit fonctionne."""

    summary: str
    steps: list[dict[str, str]] = field(default_factory=list)
    technology: str = ""
    differentiator: str = ""


@dataclass
class Benefits:
    """Bénéfices du produit."""

    main: str
    categories: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Pricing:
    """Tarification du produit."""

    model: str
    box: dict[str, Any] = field(default_factory=dict)
    offers: list[dict[str, Any]] = field(default_factory=list)
    engagement: str = ""
    guarantees: list[str] = field(default_factory=list)


@dataclass
class Product:
    """Produit vendu."""

    name: str
    type: str = ""
    problem: Problem | None = None
    how_it_works: HowItWorks | None = None
    benefits: Benefits | None = None
    pricing: Pricing | None = None


@dataclass
class Pitch:
    """Éléments de pitch commercial."""

    hook_30s: str = ""
    pitch_2min: str = ""
    discovery_questions: dict[str, list[str]] = field(default_factory=dict)
    key_phrases: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ObjectionResponse:
    """Réponse à une objection."""

    type: str
    label: str
    variants: list[str] = field(default_factory=list)
    hidden_meaning: str = ""
    response: str = ""
    proof: str = ""


@dataclass
class Proof:
    """Preuves et témoignages."""

    global_stats: dict[str, str] = field(default_factory=dict)
    testimonials: list[dict[str, Any]] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)


@dataclass
class Playbook:
    """
    Playbook commercial complet.

    Contient tout ce dont un commercial a besoin pour vendre un produit :
    - L'entreprise et son positionnement
    - Le produit (problème, solution, bénéfices, pricing)
    - Le pitch (hook, questions, phrases clés)
    - Les réponses aux objections
    - Les preuves (témoignages, stats, certifications)
    """

    id: str
    version: str
    product_slug: str
    company: Company
    product: Product
    pitch: Pitch
    objections: list[ObjectionResponse] = field(default_factory=list)
    proofs: Proof | None = None
    skills_compatible: list[str] = field(default_factory=list)

    def get_objection_response(self, objection_type: str) -> ObjectionResponse | None:
        """Retourne la réponse à une objection par type."""
        for obj in self.objections:
            if obj.type == objection_type:
                return obj
        return None

    def get_objection_by_variant(self, variant_text: str) -> ObjectionResponse | None:
        """Trouve une objection qui match un variant textuel."""
        variant_lower = variant_text.lower()
        for obj in self.objections:
            for variant in obj.variants:
                if variant.lower() in variant_lower or variant_lower in variant.lower():
                    return obj
        return None

    def get_discovery_questions(self, category: str | None = None) -> list[str]:
        """Retourne les questions de découverte."""
        if category:
            return self.pitch.discovery_questions.get(category, [])
        # Toutes les questions
        all_questions = []
        for questions in self.pitch.discovery_questions.values():
            all_questions.extend(questions)
        return all_questions

    def get_key_phrases(self, category: str | None = None) -> list[str]:
        """Retourne les phrases clés."""
        if category:
            return self.pitch.key_phrases.get(category, [])
        all_phrases = []
        for phrases in self.pitch.key_phrases.values():
            all_phrases.extend(phrases)
        return all_phrases

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour sérialisation."""
        return {
            "id": self.id,
            "version": self.version,
            "product_slug": self.product_slug,
            "company": {
                "name": self.company.name,
                "baseline": self.company.baseline,
                "sector": self.company.sector,
                "positioning": self.company.positioning,
            },
            "product": {
                "name": self.product.name,
                "type": self.product.type,
                "problem": {
                    "title": self.product.problem.title if self.product.problem else "",
                    "description": self.product.problem.description if self.product.problem else "",
                    "impacts": self.product.problem.impacts if self.product.problem else [],
                },
                "benefits": {
                    "main": self.product.benefits.main if self.product.benefits else "",
                    "categories": self.product.benefits.categories if self.product.benefits else {},
                },
                "pricing": {
                    "model": self.product.pricing.model if self.product.pricing else "",
                    "offers": self.product.pricing.offers if self.product.pricing else [],
                    "guarantees": self.product.pricing.guarantees if self.product.pricing else [],
                },
            },
            "pitch": {
                "hook_30s": self.pitch.hook_30s,
                "pitch_2min": self.pitch.pitch_2min,
                "discovery_questions": self.pitch.discovery_questions,
                "key_phrases": self.pitch.key_phrases,
            },
            "objections": [
                {
                    "type": obj.type,
                    "label": obj.label,
                    "variants": obj.variants,
                    "hidden_meaning": obj.hidden_meaning,
                    "response": obj.response,
                    "proof": obj.proof,
                }
                for obj in self.objections
            ],
            "proofs": {
                "global_stats": self.proofs.global_stats if self.proofs else {},
                "testimonials": self.proofs.testimonials if self.proofs else [],
                "certifications": self.proofs.certifications if self.proofs else [],
            },
        }


class PlaybookService:
    """
    Service de gestion des playbooks commerciaux.

    Gère le chargement, le parsing et l'accès aux playbooks YAML.
    """

    def __init__(self, playbooks_dir: str | None = None):
        """
        Initialise le service.

        Args:
            playbooks_dir: Chemin vers le dossier des playbooks.
                          Par défaut: backend/playbooks/
        """
        if playbooks_dir:
            self.playbooks_dir = Path(playbooks_dir)
        else:
            # Chemin par défaut relatif au fichier courant
            self.playbooks_dir = Path(__file__).parent.parent / "playbooks"

        self._cache: dict[str, Playbook] = {}

    def _parse_company(self, data: dict) -> Company:
        """Parse les données de l'entreprise."""
        return Company(
            name=data.get("name", ""),
            baseline=data.get("baseline", ""),
            sector=data.get("sector", ""),
            positioning=data.get("positioning", ""),
            founded=data.get("founded", ""),
            size=data.get("size", ""),
            location=data.get("location", ""),
        )

    def _parse_problem(self, data: dict) -> Problem:
        """Parse les données du problème."""
        return Problem(
            title=data.get("title", ""),
            description=data.get("description", ""),
            impacts=data.get("impacts", []),
            pains_by_persona=data.get("pains_by_persona", {}),
        )

    def _parse_how_it_works(self, data: dict) -> HowItWorks:
        """Parse le fonctionnement du produit."""
        return HowItWorks(
            summary=data.get("summary", ""),
            steps=data.get("steps", []),
            technology=data.get("technology", ""),
            differentiator=data.get("differentiator", ""),
        )

    def _parse_benefits(self, data: dict) -> Benefits:
        """Parse les bénéfices."""
        return Benefits(
            main=data.get("main", ""),
            categories=data.get("categories", {}),
        )

    def _parse_pricing(self, data: dict) -> Pricing:
        """Parse la tarification."""
        return Pricing(
            model=data.get("model", ""),
            box=data.get("box", {}),
            offers=data.get("offers", []),
            engagement=data.get("engagement", ""),
            guarantees=data.get("guarantees", []),
        )

    def _parse_product(self, data: dict) -> Product:
        """Parse les données du produit."""
        problem = None
        if "problem" in data:
            problem = self._parse_problem(data["problem"])

        how_it_works = None
        if "how_it_works" in data:
            how_it_works = self._parse_how_it_works(data["how_it_works"])

        benefits = None
        if "benefits" in data:
            benefits = self._parse_benefits(data["benefits"])

        pricing = None
        if "pricing" in data:
            pricing = self._parse_pricing(data["pricing"])

        return Product(
            name=data.get("name", ""),
            type=data.get("type", ""),
            problem=problem,
            how_it_works=how_it_works,
            benefits=benefits,
            pricing=pricing,
        )

    def _parse_pitch(self, data: dict) -> Pitch:
        """Parse les éléments de pitch."""
        return Pitch(
            hook_30s=data.get("hook_30s", ""),
            pitch_2min=data.get("pitch_2min", ""),
            discovery_questions=data.get("discovery_questions", {}),
            key_phrases=data.get("key_phrases", {}),
        )

    def _parse_objection(self, data: dict) -> ObjectionResponse:
        """Parse une réponse à objection."""
        return ObjectionResponse(
            type=data.get("type", ""),
            label=data.get("label", ""),
            variants=data.get("variants", []),
            hidden_meaning=data.get("hidden_meaning", ""),
            response=data.get("response", ""),
            proof=data.get("proof", ""),
        )

    def _parse_proofs(self, data: dict) -> Proof:
        """Parse les preuves."""
        return Proof(
            global_stats=data.get("global_stats", {}),
            testimonials=data.get("testimonials", []),
            certifications=data.get("certifications", []),
        )

    def _parse_playbook(self, data: dict) -> Playbook:
        """Parse un playbook complet depuis les données YAML."""
        meta = data.get("meta", {})

        return Playbook(
            id=meta.get("id", ""),
            version=meta.get("version", "1.0"),
            product_slug=meta.get("product_slug", ""),
            skills_compatible=meta.get("skills_compatible", []),
            company=self._parse_company(data.get("company", {})),
            product=self._parse_product(data.get("product", {})),
            pitch=self._parse_pitch(data.get("pitch", {})),
            objections=[self._parse_objection(obj) for obj in data.get("objections", [])],
            proofs=self._parse_proofs(data.get("proofs", {})) if "proofs" in data else None,
        )

    async def load(self, playbook_id: str, use_cache: bool = True) -> Playbook:
        """
        Charge un playbook depuis un fichier YAML.

        Args:
            playbook_id: Identifiant du playbook (nom du fichier sans extension)
            use_cache: Utiliser le cache si disponible

        Returns:
            Playbook: Le playbook chargé

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le parsing échoue
        """
        # Vérifier le cache
        if use_cache and playbook_id in self._cache:
            return self._cache[playbook_id]

        # Construire le chemin
        file_path = self.playbooks_dir / f"{playbook_id}.yaml"

        if not file_path.exists():
            # Essayer avec .yml
            file_path = self.playbooks_dir / f"{playbook_id}.yml"

        if not file_path.exists():
            raise FileNotFoundError(f"Playbook not found: {playbook_id}")

        # Charger le YAML
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid playbook: {playbook_id}")

        # Parser
        playbook = self._parse_playbook(data)

        # Mettre en cache
        self._cache[playbook_id] = playbook

        return playbook

    def load_sync(self, playbook_id: str, use_cache: bool = True) -> Playbook:
        """Version synchrone de load() pour les contextes non-async."""
        if use_cache and playbook_id in self._cache:
            return self._cache[playbook_id]

        file_path = self.playbooks_dir / f"{playbook_id}.yaml"

        if not file_path.exists():
            file_path = self.playbooks_dir / f"{playbook_id}.yml"

        if not file_path.exists():
            raise FileNotFoundError(f"Playbook not found: {playbook_id}")

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid playbook: {playbook_id}")

        playbook = self._parse_playbook(data)
        self._cache[playbook_id] = playbook

        return playbook

    async def list_playbooks(self) -> list[dict[str, str]]:
        """
        Liste tous les playbooks disponibles.

        Returns:
            Liste de dictionnaires avec id, name, product_name
        """
        playbooks = []

        if not self.playbooks_dir.exists():
            return playbooks

        for file_path in self.playbooks_dir.glob("*.yaml"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    meta = data.get("meta", {})
                    product = data.get("product", {})
                    company = data.get("company", {})

                    playbooks.append(
                        {
                            "id": meta.get("id", file_path.stem),
                            "name": product.get("name", file_path.stem),
                            "company": company.get("name", ""),
                            "sector": company.get("sector", ""),
                        }
                    )
            except Exception:
                # Ignorer les fichiers invalides
                continue

        # Aussi chercher les .yml
        for file_path in self.playbooks_dir.glob("*.yml"):
            if file_path.with_suffix(".yaml").exists():
                continue  # Déjà traité
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    meta = data.get("meta", {})
                    product = data.get("product", {})
                    company = data.get("company", {})

                    playbooks.append(
                        {
                            "id": meta.get("id", file_path.stem),
                            "name": product.get("name", file_path.stem),
                            "company": company.get("name", ""),
                            "sector": company.get("sector", ""),
                        }
                    )
            except Exception:
                continue

        return playbooks

    def clear_cache(self) -> None:
        """Vide le cache des playbooks."""
        self._cache.clear()

    def get_cached(self, playbook_id: str) -> Playbook | None:
        """Retourne un playbook du cache s'il existe."""
        return self._cache.get(playbook_id)
