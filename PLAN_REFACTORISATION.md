# Plan de Refactorisation - Système de Scénarios Commercial

Ce document décrit la refactorisation complète du système de scénarios,
centré sur le VENDEUR et non plus sur le PROSPECT.

**Changements majeurs :**
1. Playbook commercial complet (YAML) au lieu de templates JSON
2. Intelligence contextuelle dans l'aide à la vente
3. **Suppression des 3 niveaux de difficulté** (easy/medium/hard)
4. **TrainingAgent** géré par l'orchestrateur (plus de TrainingServiceV2)
5. **Nommage propre** - Plus de "V2" dans les fichiers

---

## 1. VISION GLOBALE

### Ancien Système (à supprimer)
```
Product → Prospect → Objections → Flow
         ↓
    Templates JSON statiques
         ↓
    scenario_loader.py (conversion complexe)
```

### Nouveau Système (à implémenter)
```
VENDEUR → SOCIÉTÉ → PRODUIT → PREUVES → PROSPECT (besoin + objections)
                      ↓
              Playbook Commercial Complet
                      ↓
              IA génère le prospect dynamiquement
```

---

## 2. SIMPLIFICATION UX : SUPPRESSION DES NIVEAUX

### Pourquoi supprimer les niveaux ?

| Ancien système (3 niveaux) | Problème |
|----------------------------|----------|
| Easy = tout visible | Trop d'info, pas contextuel |
| Medium = aide partielle | Arbitraire |
| Hard = aucune aide | Frustrant même pour experts |

| Nouveau système (1 mode) | Avantage |
|--------------------------|----------|
| Accordéon intelligent | L'aide s'adapte à la PHASE de conversation |
| Highlight contextuel | Montre ce qui est pertinent MAINTENANT |
| Auto-ouverture objections | Réagit en temps réel |

### L'intelligence contextuelle remplace les niveaux

```
DÉBUTANT (comportement naturel) :
├── Reste longtemps en phase "opening/discovery"
├── L'accordéon montre sections débutant (pitch, questions)
└── Plus de temps pour assimiler

EXPERT (comportement naturel) :
├── Avance vite vers "negotiation/closing"
├── L'accordéon suit son rythme
└── Peut réduire/fermer les sections qu'il maîtrise

TOUS LES NIVEAUX :
└── Objection détectée → section objections s'ouvre automatiquement
```

### Option pour experts "puristes"

Ajouter un simple toggle dans l'interface :
```
[ ] Masquer l'aide
```
Cela cache l'accordéon entièrement pour ceux qui veulent s'entraîner "à l'aveugle".

---

## 3. TRAINING AGENT (REMPLACEMENT DE TRAININGSERVICEV2)

### Pourquoi un Agent plutôt qu'un Service ?

| TrainingServiceV2 (ancien) | TrainingAgent (nouveau) |
|---------------------------|-------------------------|
| Service isolé, 1400 lignes | Agent modulaire géré par orchestrateur |
| Appelle Claude directement | Intégré dans l'architecture multi-agents |
| Difficile à maintenir | Responsabilités séparées |
| Pas de mémoire partagée | Peut utiliser la mémoire agents |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                               │
│                   (ChampionCloneOrchestrator)                   │
├─────────────────────────────────────────────────────────────────┤
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│   ┌───────────┐     ┌─────────────┐    ┌───────────┐          │
│   │AudioAgent │     │TrainingAgent│    │PatternAgent│          │
│   └───────────┘     └──────┬──────┘    └───────────┘          │
│                            │                                    │
│              ┌─────────────┼─────────────┐                     │
│              ▼             ▼             ▼                     │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│       │ Playbook │  │  Module  │  │  Jauge   │                │
│       │ Service  │  │ Service  │  │ Service  │                │
│       └──────────┘  └──────────┘  └──────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Structure des fichiers

```
backend/
├── agents/
│   ├── base_agent.py              # Classe abstraite (existant)
│   ├── audio_agent/               # (existant)
│   ├── pattern_agent/             # (existant)
│   ├── content_agent/             # (existant - NE PAS TOUCHER - /learn)
│   └── training_agent/            # 🆕 NOUVEAU
│       ├── __init__.py
│       ├── agent.py               # TrainingAgent (hérite BaseAgent)
│       ├── tools.py               # Outils de l'agent
│       └── memory.py              # Mémoire de session
│
├── services/
│   ├── playbook_service.py        # 🆕 Chargement playbooks YAML
│   ├── module_service.py          # 🆕 Chargement modules + évaluation
│   ├── jauge_service.py           # ✅ EXISTANT - Jauge émotionnelle
│   ├── voice_effects.py           # ✅ EXISTANT - Effets voix
│   └── event_service.py           # ✅ EXISTANT - Événements
│
├── playbooks/                     # 🆕 YAML produits
│   └── automate_ai.yaml
│
└── training_modules/              # 🆕 YAML modules
    ├── bebedc.yaml
    ├── spin_selling.yaml
    ├── closing.yaml
    └── objection_handling.yaml
```

### Services existants à GARDER (émotions, voix, etc.)

| Service | Fichier | Rôle | Statut |
|---------|---------|------|--------|
| **JaugeService** | `jauge_service.py` | Jauge 0-100, moods, comportements | ✅ GARDER |
| **BehavioralDetector** | `jauge_service.py` | Détection patterns (reformulation, empathie...) | ✅ GARDER |
| **VoiceEffects** | `voice_effects.py` | Effets voix selon mood | ✅ GARDER |
| **EventService** | `event_service.py` | Events temps réel | ✅ GARDER |

```
SYSTÈME ÉMOTIONNEL (inchangé) :
┌─────────────────────────────────────────────────────────────────┐
│  JaugeService                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Jauge : 0 ──────────────────────────────────────────────► 100  │
│          │         │         │         │         │              │
│       HOSTILE  SKEPTICAL  NEUTRAL  INTERESTED  READY            │
│                                                                 │
│  BehavioralDetector :                                           │
│  ├── good_listening_signal    → +3 points                       │
│  ├── relevant_reformulation   → +5 points                       │
│  ├── objection_well_handled   → +8 points                       │
│  ├── hidden_objection_found   → +10 points                      │
│  ├── interruption             → -5 points                       │
│  ├── ignored_objection        → -8 points                       │
│  └── aggressive_response      → -10 points                      │
│                                                                 │
│  VoiceEffects :                                                 │
│  ├── hostile     → voix sèche, débit rapide                     │
│  ├── skeptical   → voix dubitative                              │
│  ├── neutral     → voix professionnelle                         │
│  ├── interested  → voix engagée                                 │
│  └── ready       → voix enthousiaste                            │
└─────────────────────────────────────────────────────────────────┘
```

### TrainingAgent : Code

```python
# backend/agents/training_agent/agent.py

from agents.base_agent import BaseAgent
from services.playbook_service import PlaybookService
from services.module_service import ModuleService
from services.jauge_service import JaugeService

class TrainingAgent(BaseAgent):
    """
    Agent de formation commerciale.
    Gère les sessions d'entraînement avec playbook + module.
    """

    name = "training"
    description = "Gère les sessions de formation commerciale"
    model = "claude-sonnet-4-20250514"  # Sonnet pour rapidité

    def __init__(self):
        super().__init__()
        self.playbook_service = PlaybookService()
        self.module_service = ModuleService()
        self.jauge_service = JaugeService()

    # ============================================
    # OUTILS DE L'AGENT
    # ============================================

    async def create_session(
        self,
        user_id: int,
        playbook_id: str,
        module_id: str,
    ) -> dict:
        """
        Crée une nouvelle session d'entraînement.
        """
        # Charger playbook et module
        playbook = await self.playbook_service.load(playbook_id)
        module = await self.module_service.load(module_id)

        # Générer le prospect dynamiquement
        prospect = await self._generate_prospect(playbook, module)

        # Initialiser la jauge
        jauge = self.jauge_service.create(start_value=50)

        return {
            "session_id": ...,
            "playbook": playbook,
            "module": module,
            "prospect": prospect,
            "jauge": jauge,
        }

    async def process_message(
        self,
        session_id: str,
        user_message: str,
    ) -> dict:
        """
        Traite un message de l'utilisateur.
        Retourne la réponse du prospect + mise à jour jauge.
        """
        session = await self._get_session(session_id)

        # Évaluer le message selon le module
        module_progress = await self.module_service.evaluate_message(
            module=session["module"],
            message=user_message,
            history=session["messages"],
        )

        # Mettre à jour la jauge
        jauge_update = self.jauge_service.update(
            user_message=user_message,
            prospect_mood=session["prospect"]["personality"],
        )

        # Générer réponse du prospect
        prospect_response = await self._generate_prospect_response(
            session=session,
            user_message=user_message,
            module_instructions=session["module"]["prospect_instructions"],
        )

        return {
            "prospect_response": prospect_response,
            "jauge": jauge_update,
            "module_progress": module_progress,
            "detected_elements": module_progress.get("detected", []),
        }

    async def end_session(self, session_id: str) -> dict:
        """
        Termine la session et génère le rapport.
        """
        session = await self._get_session(session_id)

        # Évaluation finale du module
        evaluation = await self.module_service.evaluate_session(
            module=session["module"],
            messages=session["messages"],
        )

        # Calculer résultat final (matrice module × closing)
        closing_obtained = session["jauge"]["value"] >= 100
        result = self.module_service.calculate_final_result(
            module_score=evaluation["score"],
            module_threshold=session["module"]["evaluation"]["mastery_threshold"],
            closing=closing_obtained,
        )

        # Générer rapport
        report = await self.module_service.generate_report(
            module=session["module"],
            evaluation=evaluation,
            result=result,
            session=session,
        )

        return report

    # ============================================
    # MÉTHODES PRIVÉES
    # ============================================

    async def _generate_prospect(self, playbook: dict, module: dict) -> dict:
        """
        Génère un prospect cohérent avec le playbook et le module.
        Utilise Claude pour créer un prospect avec besoin + objections.
        """
        prompt = f"""
        Génère un prospect pour une session de formation commerciale.

        PRODUIT : {playbook['product']['name']}
        PROBLÈME RÉSOLU : {playbook['product']['problem']['title']}

        MODULE DE FORMATION : {module['name']}
        INSTRUCTIONS : {module.get('prospect_instructions', '')}

        Le prospect doit :
        1. Avoir un BESOIN réel que le produit peut résoudre
        2. Avoir des OBJECTIONS réalistes (au moins 2)
        3. Ne pas tout révéler spontanément (le vendeur doit questionner)

        Retourne un JSON avec : first_name, last_name, role, company,
        sector, company_size, personality, need, likely_objections
        """

        response = await self.call_claude(prompt)
        return self._parse_prospect(response)

    async def _generate_prospect_response(
        self,
        session: dict,
        user_message: str,
        module_instructions: str,
    ) -> str:
        """
        Génère la réponse du prospect.
        """
        prompt = f"""
        Tu es {session['prospect']['first_name']}, {session['prospect']['role']}
        chez {session['prospect']['company']}.

        Personnalité : {session['prospect']['personality']}
        Besoin caché : {session['prospect']['need']['pain']}

        INSTRUCTIONS MODULE : {module_instructions}

        Le commercial vient de dire : "{user_message}"

        Réponds de manière réaliste selon ta personnalité.
        """

        return await self.call_claude(prompt)
```

### Intégration avec l'Orchestrateur

```python
# backend/orchestrator/main.py

from agents.training_agent import TrainingAgent

class ChampionCloneOrchestrator:
    def __init__(self):
        self.agents = {
            "audio": AudioAgent(),
            "pattern": PatternAgent(),
            "training": TrainingAgent(),  # NOUVEAU
        }

    async def handle_training_request(self, request: dict) -> dict:
        """Route les requêtes training vers le TrainingAgent."""
        agent = self.agents["training"]

        match request["action"]:
            case "create_session":
                return await agent.create_session(**request["params"])
            case "process_message":
                return await agent.process_message(**request["params"])
            case "end_session":
                return await agent.end_session(**request["params"])
```

### Endpoints API simplifiés

```python
# backend/api/routers/training.py

from orchestrator import orchestrator

@router.post("/training/start")
async def start_session(request: StartSessionRequest):
    """Démarre une session via l'orchestrateur."""
    return await orchestrator.handle_training_request({
        "action": "create_session",
        "params": {
            "user_id": request.user_id,
            "playbook_id": request.playbook_id,
            "module_id": request.module_id,
        }
    })

@router.post("/training/respond")
async def respond(request: RespondRequest):
    """Envoie un message via l'orchestrateur."""
    return await orchestrator.handle_training_request({
        "action": "process_message",
        "params": {
            "session_id": request.session_id,
            "user_message": request.message,
        }
    })

@router.post("/training/end")
async def end_session(request: EndSessionRequest):
    """Termine la session via l'orchestrateur."""
    return await orchestrator.handle_training_request({
        "action": "end_session",
        "params": {
            "session_id": request.session_id,
        }
    })
```

### Migration : TrainingServiceV2 → TrainingAgent

| Ancien (à supprimer) | Nouveau |
|---------------------|---------|
| `services/training_service_v2.py` | `agents/training_agent/agent.py` |
| `TrainingServiceV2` | `TrainingAgent` |
| Appel direct dans routers | Appel via orchestrateur |
| 1400 lignes monolithiques | Agent + Services modulaires |

### Séparation ContentAgent vs TrainingAgent

**IMPORTANT : ContentAgent reste INCHANGÉ pour les cours et quizz.**

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENTS DISTINCTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ContentAgent (INCHANGÉ)         TrainingAgent (NOUVEAU)        │
│  ──────────────────────          ────────────────────────       │
│  📚 Cours                        🎯 Sessions entraînement       │
│  📝 Quizz                        💬 Conversations prospect      │
│  📖 Scripts exemple              📊 Jauge émotionnelle          │
│  🎓 Contenu pédagogique          📋 Évaluation module           │
│                                  📈 Rapport final               │
│                                                                 │
│  Page : /learn                   Page : /training               │
│                                                                 │
│  ⚠️ NE PAS TOUCHER              ✅ À CRÉER                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Agent | Fichier | Statut |
|-------|---------|--------|
| ContentAgent | `agents/content_agent/` | ✅ Garder tel quel |
| TrainingAgent | `agents/training_agent/` | 🆕 À créer |
| TrainingServiceV2 | `services/training_service_v2.py` | ❌ À supprimer |

---

## 4. STRUCTURE DU PLAYBOOK COMMERCIAL

```yaml
playbook:
  # 1. QUI VEND
  seller:
    name: "{{user.name}}"
    role: "Commercial"

  # 2. POUR QUI
  company:
    name: "AutomateAI"
    sector: "IA / Automatisation"
    positioning: "L'IA qui travaille pour vous"

  # 3. QUOI (LE PLUS IMPORTANT - ARGUMENTAIRE COMPLET)
  product:
    name: "AutomateAI Box"
    problem_solved:
      title: "Les tâches admin tuent la productivité"
      impacts: ["20h/semaine perdues", "15-25k€/an par employé"]
      pains_by_persona:
        dirigeant: ["Je paie des gens pour du copier-coller"]
        daf: ["Les erreurs de saisie me coûtent cher"]

    how_it_works:
      summary: "Box locale avec IA multi-agents"
      steps:
        - title: "Audit"
          description: "1 journée pour identifier les tâches"
        - title: "Installation"
          description: "2h, aucune interruption"
        - title: "Formation"
          description: "2 jours avec vos équipes"

    benefits:
      main: "Gagnez 10-15h par semaine par employé"
      by_category:
        temps: ["10-15h gagnées/semaine", "Reporting automatique"]
        argent: ["ROI 300% an 1", "15-25k€ économisés/employé"]
        qualite: ["0 erreur", "24/7"]

    pricing:
      model: "Box + Abonnement"
      offers:
        - name: "Starter"
          price: "490€/mois"
          target: "TPE 1-10 employés"
        - name: "Business"
          price: "990€/mois"
          target: "PME 10-50 employés"
      guarantees: ["30 jours satisfait ou remboursé", "ROI garanti"]

    differentiator: "Seule solution 100% locale, RGPD native"

  # 4. PITCH COMMERCIAL
  pitch:
    hook_30s: |
      "Vous savez combien d'heures vos équipes perdent chaque semaine
      à trier des emails, saisir des données ? En moyenne 15-20h.
      On automatise ça avec des IA locales. Résultat : vos équipes
      se concentrent sur ce qui compte."

    pitch_2min: |
      "Je vais être direct : vos équipes admin perdent probablement
      15-20h par semaine sur des tâches répétitives..."

    discovery_questions:
      situation:
        - "Combien de personnes sur l'administratif ?"
        - "Quelles tâches prennent le plus de temps ?"
      pain:
        - "Qu'est-ce qui vous frustre le plus ?"
        - "Avez-vous calculé le coût de ces tâches ?"
      impact:
        - "Combien coûte une erreur de saisie ?"
        - "Que se passe-t-il si rien ne change ?"
      decision:
        - "Qui d'autre serait impliqué ?"
        - "Qu'est-ce qui vous ferait dire oui ?"

    key_phrases:
      hooks:
        - "Combien d'heures perdez-vous à faire le travail d'un robot ?"
      transitions:
        - "Ce que vous décrivez, c'est exactement ce que notre client X vivait..."
      closings:
        - "On fait un audit gratuit la semaine prochaine ?"

  # 5. OBJECTIONS ET RÉPONSES
  objection_responses:
    - type: "budget"
      label: "Trop cher"
      variants:
        - "On n'a pas le budget"
        - "C'est costaud comme investissement"
      hidden_meaning: "Je ne vois pas le ROI"
      response: |
        "Faisons le calcul ensemble :
        3 personnes admin × 10h gagnées × 25€/h = 3000€/mois économisés
        Abonnement : 490€/mois
        Vous économisez 2500€/mois dès le premier mois."
      proof_to_use: "Dupont & Fils : ROI en 6 semaines"

    - type: "timing"
      label: "Pas le moment"
      variants:
        - "Rappelez-moi dans 6 mois"
        - "On est en plein rush"
      hidden_meaning: "J'ai pas envie de gérer un projet de plus"
      response: |
        "Je comprends. Mais chaque mois qu'on attend,
        c'est 60h de perdues. Et l'installation prend 2h.
        On peut commencer par un audit gratuit d'1h ?"
      proof_to_use: "Chiffrer le coût de l'attente"

    - type: "competition"
      label: "On a déjà quelqu'un"
      variants:
        - "On a déjà un prestataire"
        - "Mon neveu gère l'informatique"
      hidden_meaning: "Pourquoi changer ?"
      response: |
        "Très bien. Et est-ce qu'ils automatisent vos tâches admin ?
        La plupart des prestataires font de la maintenance.
        Nous, on automatise. C'est complémentaire."
      proof_to_use: "Cabinet Martin : prestataire + nous = combo gagnant"

    - type: "trust"
      label: "Je vous connais pas"
      variants:
        - "C'est quoi AutomateAI ?"
        - "Jamais entendu parler"
      hidden_meaning: "Peur de me faire avoir"
      response: |
        "Question légitime. On existe depuis 2022, 47 PME équipées.
        Certifié par l'ANSSI. Hébergement 100% France.
        Et on offre 30 jours d'essai sans engagement."
      proof_to_use: "47 clients, certifications, essai gratuit"

    - type: "decision"
      label: "C'est pas moi qui décide"
      variants:
        - "Faut que j'en parle à mon associé"
        - "Le DG doit valider"
      hidden_meaning: "Je veux pas décider seul"
      response: |
        "Bien sûr. Je peux vous préparer un dossier synthétique
        pour votre associé. Et si vous voulez, je peux participer
        à un call avec vous deux pour répondre à ses questions."
      proof_to_use: "Proposer support pour convaincre le décideur"

    - type: "status_quo"
      label: "Ça fonctionne comme ça"
      variants:
        - "On a toujours fait comme ça"
        - "Pourquoi changer ?"
      hidden_meaning: "Flemme de changer"
      response: |
        "Je comprends. Mais les attaques ont explosé de 400% depuis le COVID.
        Votre ami chef d'entreprise qui s'est fait pirater le mois dernier,
        lui aussi pensait que ça fonctionnait..."
      proof_to_use: "Exemple de client qui a failli avoir un problème"

  # 6. PREUVES (MES ARMES)
  proofs:
    global_stats:
      clients: "47 PME équipées"
      satisfaction: "4.8/5"
      main_result: "12h/semaine gagnées en moyenne"

    testimonials:
      - client_name: "Pierre Dupont"
        client_role: "DG"
        company: "Dupont & Fils"
        sector: "Négoce BTP"
        size: "35 employés"
        problem_before: |
          4 personnes admin, 20h/semaine chacun sur tâches répétitives.
          Erreurs de saisie fréquentes. Retards de facturation.
        results:
          - "60% de réduction du temps admin"
          - "0 erreur de saisie"
          - "ROI atteint en 6 semaines"
        quote: |
          "On a absorbé 30% de croissance sans recruter personne."

    certifications:
      - "Certifié ANSSI"
      - "Hébergement France"
      - "Conforme RGPD"

  # 7. PROSPECT (GÉNÉRÉ PAR IA)
  prospect:
    first_name: "François"
    last_name: "Legrand"
    role: "DAF"
    company: "MétalService"
    sector: "Industrie"
    company_size: "45 employés"
    personality: "analytique"  # Veut des chiffres

    need:
      current_situation: "5 personnes au service admin/compta, saisie manuelle"
      pain: "Erreur de saisie le mois dernier → avoir de 2000€"
      stakes: "Croissance 20% prévue, impossible de recruter"
      trigger: "Le DG lui a demandé un plan pour 'faire plus avec moins'"

    likely_objections:
      - type: "proof"
        expressed: "Vous avez des références dans l'industrie ?"
      - type: "security"
        expressed: "Et nos données de prix, elles vont où ?"
      - type: "roi"
        expressed: "Comment vous calculez le ROI ?"
```

---

## 5. MODULES DE FORMATION (SÉPARÉS DU PLAYBOOK)

### Principe : Séparer QUOI vendre de COMMENT s'entraîner

```
┌─────────────────┐     ┌─────────────────┐
│    PLAYBOOK     │     │     MODULE      │
│  (le produit)   │  +  │ (la compétence) │
├─────────────────┤     ├─────────────────┤
│ AutomateAI      │     │ BEBEDC          │
│ Cybersécurité   │     │ SPIN Selling    │
│ CRM Agence      │     │ Closing         │
└─────────────────┘     └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
            ┌───────────────┐
            │   SESSION     │
            │ Produit+Module│
            │ = Scénario    │
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   RAPPORT     │
            │ Évaluation du │
            │ MODULE (pas   │
            │ du closing)   │
            └───────────────┘
```

### 4.1 Structure d'un module

```yaml
# backend/training_modules/bebedc.yaml
module:
  id: bebedc
  name: "Checklist BEBEDC"
  description: "Qualification complète du prospect avant proposition"
  category: "discovery"  # discovery | objection | closing | negotiation

  # ============================================
  # OBJECTIF PÉDAGOGIQUE
  # ============================================
  objective: |
    Maîtriser la qualification BEBEDC pour ne jamais faire
    de proposition à un prospect non qualifié.

  # ============================================
  # CE QUE L'ÉLÈVE DOIT ACCOMPLIR
  # ============================================
  checklist:
    - id: besoin
      label: "Besoin"
      description: "Identifier le besoin réel (pas juste exprimé)"
      question_hint: "Qu'est-ce qui vous pose problème aujourd'hui ?"
      detection_patterns:
        - "besoin|problème|difficulté|défi|frustration"
        - "qu'est-ce qui.*pose problème"
        - "quel est votre.*principal"
      weight: 15  # Points
      required: true

    - id: enjeu
      label: "Enjeu"
      description: "Comprendre l'impact business si rien ne change"
      question_hint: "Quel impact ça a sur votre activité ?"
      detection_patterns:
        - "impact|conséquence|coût|risque|enjeu"
        - "que se passe.*(si|quand)"
        - "combien.*coûte"
      weight: 20
      required: true

    - id: budget
      label: "Budget"
      description: "Qualifier le budget disponible"
      question_hint: "Avez-vous une enveloppe prévue pour ce type de projet ?"
      detection_patterns:
        - "budget|enveloppe|investissement|combien"
        - "quel.*montant"
        - "fourchette"
      weight: 15
      required: true

    - id: echeance
      label: "Échéance"
      description: "Déterminer le timing du projet"
      question_hint: "C'est pour quand idéalement ?"
      detection_patterns:
        - "quand|délai|timing|échéance|calendrier"
        - "pour quand"
        - "urgence|priorité"
      weight: 15
      required: true

    - id: decideur
      label: "Décideur"
      description: "Identifier qui prend la décision"
      question_hint: "Qui d'autre serait impliqué dans la décision ?"
      detection_patterns:
        - "décid|valid|accord|approbation"
        - "qui.*décide"
        - "seul.*décision|avec.*quelqu'un"
      weight: 20
      required: true

    - id: competiteur
      label: "Compétiteur"
      description: "Connaître la concurrence en place"
      question_hint: "Vous utilisez quoi aujourd'hui ?"
      detection_patterns:
        - "concurrent|alternative|actuellement|aujourd'hui"
        - "vous utilisez"
        - "en place|existant"
      weight: 15
      required: false  # Bonus

  # ============================================
  # INSTRUCTIONS POUR L'IA (PROSPECT)
  # ============================================
  prospect_instructions: |
    Tu joues un prospect qui a un VRAI besoin mais qui ne révèle
    pas tout spontanément. Le vendeur doit te QUESTIONNER pour
    découvrir chaque élément BEBEDC.

    Comportement attendu :
    - Besoin : Tu l'exprimes vaguement au début, le vendeur doit creuser
    - Enjeu : Tu ne le donnes QUE si on te demande l'impact
    - Budget : Tu es évasif sauf si on pose la question directement
    - Échéance : Tu as une deadline mais tu ne la dis pas spontanément
    - Décideur : Tu mentionnes "je dois en parler à..." seulement si pressé
    - Compétiteur : Tu ne parles de l'existant que si on demande

    NE FAIS PAS de closing prématuré. L'objectif est la QUALIFICATION.

  # ============================================
  # ÉVALUATION
  # ============================================
  evaluation:
    type: "checklist"  # checklist | sequence | jauge | hybrid

    mastery_threshold: 5  # Sur 6 pour maîtrise
    passing_threshold: 4  # Sur 6 pour validation

    scoring:
      excellent: { min: 6, label: "Excellent", color: "green" }
      good: { min: 5, label: "Bien", color: "blue" }
      progress: { min: 4, label: "En progression", color: "yellow" }
      insufficient: { min: 0, label: "À retravailler", color: "red" }

    # Le closing N'EST PAS l'objectif de ce module
    closing_required: false
    closing_bonus: 10  # Points bonus si closing quand même

  # ============================================
  # FEEDBACK PERSONNALISÉ
  # ============================================
  feedback:
    missing:
      besoin: "Creusez davantage le besoin avec des questions ouvertes : 'Qu'est-ce qui vous frustre le plus ?'"
      enjeu: "N'oubliez pas de quantifier l'impact : 'Combien ça vous coûte par mois ?'"
      budget: "Qualifiez le budget tôt : 'Avez-vous une enveloppe prévue ?'"
      echeance: "Clarifiez le timing : 'C'est urgent ou vous avez le temps ?'"
      decideur: "Identifiez les décideurs : 'Qui d'autre serait concerné ?'"
      competiteur: "Explorez l'existant : 'Vous utilisez quoi aujourd'hui ?'"

    general:
      all_found: "Bravo ! Qualification BEBEDC complète. Vous pouvez proposer en confiance."
      mostly_found: "Bonne qualification. Attention aux éléments manquants avant de proposer."
      insufficient: "Qualification incomplète. Risque de proposition inadaptée."
```

### 4.2 Autres exemples de modules

```yaml
# backend/training_modules/spin_selling.yaml
module:
  id: spin_selling
  name: "SPIN Selling"
  description: "Méthode de questionnement en 4 phases"
  category: "discovery"

  checklist:
    - id: situation
      label: "S - Situation"
      description: "Questions sur le contexte actuel"
      sequence_order: 1

    - id: problem
      label: "P - Problème"
      description: "Questions sur les difficultés"
      sequence_order: 2

    - id: implication
      label: "I - Implication"
      description: "Questions sur les conséquences"
      sequence_order: 3

    - id: need_payoff
      label: "N - Need-Payoff"
      description: "Questions sur les bénéfices attendus"
      sequence_order: 4

  evaluation:
    type: "sequence"  # L'ORDRE compte
    mastery_threshold: 4  # Les 4 dans l'ordre
    closing_required: false
```

```yaml
# backend/training_modules/closing.yaml
module:
  id: closing
  name: "Techniques de Closing"
  description: "Conclure efficacement une vente"
  category: "closing"

  checklist:
    - id: buying_signals
      label: "Signaux d'achat"
      description: "Détecter les signaux d'achat du prospect"

    - id: trial_close
      label: "Pré-closing"
      description: "Tester l'engagement avec questions fermées"

    - id: handle_last_objection
      label: "Dernière objection"
      description: "Traiter l'ultime objection"

    - id: close
      label: "Closing"
      description: "Obtenir l'engagement"

  evaluation:
    type: "jauge"  # ICI le closing EST l'objectif
    mastery_threshold: 100  # Jauge à 100%
    closing_required: true
```

```yaml
# backend/training_modules/objection_handling.yaml
module:
  id: objection_handling
  name: "Traitement des Objections"
  description: "Répondre efficacement aux objections"
  category: "objection"

  checklist:
    - id: acknowledge
      label: "Accuser réception"
      description: "Montrer qu'on a entendu l'objection"

    - id: clarify
      label: "Clarifier"
      description: "Comprendre l'objection réelle"

    - id: respond
      label: "Répondre"
      description: "Apporter une réponse adaptée"

    - id: confirm
      label: "Confirmer"
      description: "Vérifier que l'objection est levée"

  prospect_instructions: |
    Tu dois soulever AU MOINS 3 objections pendant l'échange.
    Types d'objections à utiliser : budget, timing, confiance.

  evaluation:
    type: "count"  # Nombre d'objections traitées
    mastery_threshold: 3
    closing_required: false
```

### 4.3 Structure du rapport final (par module)

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 RAPPORT DE SESSION                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📦 Produit : AutomateAI Box                                    │
│  🎯 Module  : Checklist BEBEDC                                  │
│  ⏱️  Durée   : 8 min 32 sec                                     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 ÉVALUATION BEBEDC                              Score: 4/6   │
│  ───────────────────────────────────────────────────────────── │
│                                                                 │
│  ✅ Besoin       │ Détecté à 2:15                               │
│                  │ "Vous avez évoqué un problème de temps..."   │
│                  │                                               │
│  ✅ Enjeu        │ Détecté à 3:42                               │
│                  │ "L'impact sur la croissance est clair"       │
│                  │                                               │
│  ❌ Budget       │ NON QUALIFIÉ                                 │
│                  │ 💡 Astuce : "Avez-vous une enveloppe ?"      │
│                  │                                               │
│  ✅ Échéance     │ Détecté à 5:10                               │
│                  │ "Avant fin Q1" - Bon timing identifié        │
│                  │                                               │
│  ✅ Décideur     │ Détecté à 4:28                               │
│                  │ "DG doit valider" - Circuit identifié        │
│                  │                                               │
│  ❌ Compétiteur  │ NON EXPLORÉ                                  │
│                  │ 💡 Astuce : "Vous utilisez quoi auj. ?"      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 RÉSULTAT                                                    │
│  ───────────────────────────────────────────────────────────── │
│                                                                 │
│  Score      : 4/6 (67%)                                         │
│  Seuil      : 5/6 pour maîtrise                                 │
│  Statut     : 🔶 EN PROGRESSION                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ████████████████████░░░░░░░░░░ 67%                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 RECOMMANDATIONS                                             │
│  ───────────────────────────────────────────────────────────── │
│                                                                 │
│  1. Budget : Pensez à qualifier le budget tôt dans l'échange    │
│     → Question suggérée : "Avez-vous prévu un budget ?"         │
│                                                                 │
│  2. Compétiteur : Explorez toujours l'existant                  │
│     → Question suggérée : "Vous utilisez quoi aujourd'hui ?"    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ℹ️  Note : La conversion n'était pas l'objectif de ce module   │
│      Jauge finale : 72% (pour information)                      │
│                                                                 │
│  🔄 Prochaine étape suggérée : Refaire BEBEDC ou passer à       │
│     "Traitement des Objections"                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Différents types d'évaluation par module

| Module | Type évaluation | Critère maîtrise | Closing requis ? |
|--------|-----------------|------------------|------------------|
| BEBEDC | `checklist` | 5/6 éléments | ❌ Non |
| SPIN Selling | `sequence` | 4/4 dans l'ordre | ❌ Non |
| Objections | `count` | 3+ objections traitées | ❌ Non |
| Discovery | `checklist` | 5+ questions pertinentes | ❌ Non |
| Closing | `jauge` | Jauge à 100% | ✅ Oui |
| Négociation | `hybrid` | Accord + marge préservée | ✅ Oui |

### 4.5 Matrice d'évaluation finale (Module × Closing)

**Principe : Le module est l'objectif principal, le closing est un BONUS**

| Module maîtrisé | Closing obtenu | Résultat | Badge |
|-----------------|----------------|----------|-------|
| ✅ Oui | ✅ Oui | 🏆 **JACKPOT - Double réussite** | `jackpot` |
| ✅ Oui | ❌ Non | ✅ **SUCCÈS - Compétence acquise** | `success` |
| ❌ Non | ✅ Oui | ⚠️ **ATTENTION - Closing chanceux** | `warning` |
| ❌ Non | ❌ Non | ❌ **À RETRAVAILLER** | `failure` |

#### Logique backend

```python
# Dans ModuleService.generate_report()

def calculate_final_result(module_score: float, module_threshold: float, closing: bool) -> dict:
    module_mastered = module_score >= module_threshold

    if module_mastered and closing:
        return {
            "status": "jackpot",
            "badge": "🏆",
            "title": "JACKPOT - Double réussite !",
            "message": "Compétence maîtrisée ET closing obtenu. Excellent travail !",
            "competence_acquired": True,
            "closing_obtained": True,
        }

    elif module_mastered and not closing:
        return {
            "status": "success",
            "badge": "✅",
            "title": "Compétence acquise",
            "message": "Bravo ! Vous maîtrisez cette compétence. Le closing viendra naturellement.",
            "competence_acquired": True,
            "closing_obtained": False,
        }

    elif not module_mastered and closing:
        return {
            "status": "warning",
            "badge": "⚠️",
            "title": "Closing chanceux",
            "message": "Vous avez converti, mais attention : votre qualification était incomplète. En situation réelle, ce closing aurait pu échouer.",
            "competence_acquired": False,
            "closing_obtained": True,
            "risks": get_missing_element_risks(module_score),  # Risques liés aux éléments manquants
        }

    else:  # not module_mastered and not closing
        return {
            "status": "failure",
            "badge": "❌",
            "title": "À retravailler",
            "message": "Continuez à pratiquer. Concentrez-vous sur les éléments manquants.",
            "competence_acquired": False,
            "closing_obtained": False,
        }
```

#### Rapport pour "Closing chanceux" (cas critique)

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 RAPPORT DE SESSION                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 Module  : Checklist BEBEDC                                  │
│  📋 Score   : 3/6 (50%)                                         │
│  🔶 Seuil   : 5/6 pour maîtrise                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚠️  CLOSING OBTENU MAIS COMPÉTENCE NON ACQUISE                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Vous avez converti ce prospect, bravo pour la ténacité !       │
│                                                                 │
│  MAIS ATTENTION : votre qualification était incomplète.         │
│  En situation réelle, ce closing aurait pu échouer.             │
│                                                                 │
│  ❌ Éléments non qualifiés et leurs RISQUES :                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Budget     → Mauvaise surprise à la signature           │   │
│  │ Décideur   → Deal bloqué par un décideur inconnu        │   │
│  │ Compétiteur→ Objection tardive, prospect compare        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💡 CONSEIL                                                     │
│  ─────────────────────────────────────────────────────────────  │
│  Un closing sans qualification complète, c'est comme           │
│  construire une maison sans fondations.                         │
│                                                                 │
│  Refaites ce module pour ancrer les réflexes de qualification   │
│  AVANT de passer au module Closing.                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔄 PROCHAINE ÉTAPE SUGGÉRÉE                                    │
│  → Refaire "Checklist BEBEDC" (objectif: 5/6)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Rapport pour "Jackpot" (double réussite)

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 RAPPORT DE SESSION                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 Module  : Checklist BEBEDC                                  │
│  📋 Score   : 6/6 (100%)                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🏆 JACKPOT - DOUBLE RÉUSSITE !                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ✅ Compétence BEBEDC maîtrisée (6/6)                           │
│  ✅ Closing obtenu                                              │
│                                                                 │
│  Vous avez parfaitement qualifié le prospect ET converti.       │
│  C'est exactement ce qu'on attend d'un commercial performant.   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔄 PROCHAINE ÉTAPE SUGGÉRÉE                                    │
│  → Passer au module "Traitement des Objections"                 │
│  → Ou augmenter la difficulté du prospect                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Types de risques par élément manquant (BEBEDC)

```yaml
# Dans bebedc.yaml
risks_if_missing:
  besoin:
    risk: "Proposition hors sujet"
    consequence: "Le prospect ne se reconnaît pas dans votre offre"
  enjeu:
    risk: "Pas d'urgence créée"
    consequence: "Le prospect repousse la décision indéfiniment"
  budget:
    risk: "Mauvaise surprise à la signature"
    consequence: "Négociation de dernière minute, deal perdu"
  echeance:
    risk: "Pas de date de décision"
    consequence: "Le deal traîne, finit en 'ghost'"
  decideur:
    risk: "Interlocuteur sans pouvoir"
    consequence: "Tout est à refaire avec le vrai décideur"
  competiteur:
    risk: "Objection tardive"
    consequence: "Le prospect compare et choisit l'autre"
```

---

## 6. FICHIERS À MODIFIER

### 6.1 Backend

#### A. Nouveau service : `services/playbook_service.py`
```python
"""
Service de gestion des playbooks commerciaux.
Remplace scenario_loader.py
"""

class PlaybookService:
    """
    Gère le chargement et la génération des playbooks.
    """

    async def load_playbook(self, product_slug: str) -> dict:
        """Charge un playbook depuis un fichier YAML/JSON."""
        pass

    async def generate_prospect(
        self,
        playbook: dict,
        skill: str,
        level: str,
        sector: str | None = None
    ) -> dict:
        """
        Génère un prospect cohérent avec le produit.
        Utilise Claude pour créer un prospect avec :
        - Un BESOIN réel que le produit résout
        - Des OBJECTIONS réalistes
        """
        pass

    async def get_objection_response(
        self,
        playbook: dict,
        objection_type: str
    ) -> dict:
        """Retourne la réponse à une objection."""
        pass
```

#### B. Modifier : `services/training_service_v2.py`
```python
# AVANT (ligne 258-283)
# Générer le scénario - Priorité aux templates (Phase 4)
scenario = None
template = load_scenario_template(skill_slug=skill.slug, difficulty=level)
if template:
    scenario = convert_template_to_scenario(template)
else:
    # Fallback sur ContentAgent
    ...

# APRÈS
# Charger le playbook et générer le prospect (SANS level)
playbook_service = PlaybookService()
playbook = await playbook_service.load_playbook(product_slug)
prospect = await playbook_service.generate_prospect(
    playbook=playbook,
    skill=skill.slug,
    sector=sector_slug
    # NOTE: Plus de paramètre 'level'
)
scenario = {
    "playbook": playbook,
    "prospect": prospect,
    ...
}
```

#### C. Modifier : `create_session()` - Supprimer le paramètre level
```python
# AVANT
async def create_session(
    self,
    user_id: int,
    skill_id: int,
    level: str,  # ← À SUPPRIMER
    ...
)

# APRÈS
async def create_session(
    self,
    user_id: int,
    skill_id: int,
    # Plus de level
    ...
)
```

#### D. Modifier : Endpoints API (`api/routers/training.py`)
```python
# AVANT
class StartSessionRequest(BaseModel):
    skill_id: int
    level: str  # ← À SUPPRIMER
    ...

# APRÈS
class StartSessionRequest(BaseModel):
    skill_id: int
    # Plus de level
    ...
```

#### F. Nouveau service : `services/module_service.py`
```python
"""
Service de gestion des modules de formation.
Gère le chargement et l'évaluation des modules.
"""

class ModuleService:
    """
    Gère les modules de formation (BEBEDC, SPIN, etc.)
    """

    async def load_module(self, module_id: str) -> dict:
        """Charge un module depuis un fichier YAML."""
        pass

    async def evaluate_session(
        self,
        module: dict,
        messages: list[dict],
        session_data: dict
    ) -> dict:
        """
        Évalue une session selon les critères du module.
        Retourne le score et les éléments détectés/manquants.
        """
        pass

    async def generate_report(
        self,
        module: dict,
        evaluation: dict,
        session: dict
    ) -> dict:
        """Génère le rapport final de session."""
        pass
```

#### G. Supprimer (à terme)
- `services/scenario_loader.py` - Remplacé par PlaybookService
- `services/scenario_adapter.py` - Plus nécessaire
- `scenario_templates/*.json` - Remplacé par playbooks YAML

### 6.2 Frontend

#### A. Nouveaux fichiers créés (à conserver)
```
frontend/
├── types/playbook.ts                      # Types TypeScript (FAIT)
├── hooks/useConversationPhase.ts          # Intelligence contextuelle (FAIT)
└── components/training/
    └── SalesHelperAccordion.tsx           # Composant accordéon (FAIT)
```

#### B. Modifier : `app/training/page.tsx` - Supprimer sélection niveau

```tsx
// AVANT - Sélection du niveau
const [selectedLevel, setSelectedLevel] = useState<"easy" | "medium" | "hard">("easy");

// Cards de sélection niveau...
<div className="grid grid-cols-3 gap-4">
  <LevelCard level="easy" ... />
  <LevelCard level="medium" ... />
  <LevelCard level="hard" ... />
</div>

// APRÈS - Plus de sélection niveau
// Supprimer tout le code lié aux niveaux
// Le bouton "Démarrer" lance directement la session
```

#### C. Modifier : `app/training/session/[id]/page.tsx`

**Supprimer les imports et références au level :**
```typescript
// AVANT
const { level } = useParams(); // ou searchParams

// APRÈS
// Plus besoin de level
```

**Supprimer les conditionnels basés sur level :**
```tsx
// AVANT
{(level === "easy" || level === "medium") && session?.scenario && (
  // Panneau d'aide
)}

// APRÈS - Toujours afficher (avec option toggle)
{session?.scenario && playbook && !hideHelper && (
  // Accordéon intelligent
)}
```

**Ajouter toggle "Masquer l'aide" :**
```tsx
const [hideHelper, setHideHelper] = useState(false);

// Dans le header ou toolbar
<button onClick={() => setHideHelper(!hideHelper)}>
  {hideHelper ? "Afficher l'aide" : "Masquer l'aide"}
</button>
```

**Nouveau code pour l'accordéon (simplifié) :**
```tsx
{/* Accordéon intelligent - TOUJOURS disponible */}
{session?.scenario && playbook && !hideHelper && (
  <div className="hidden lg:block fixed left-4 top-24 w-96 h-[calc(100vh-120px)] rounded-xl bg-white/5 border border-white/10 overflow-hidden">
    <SalesHelperAccordion
      playbook={playbook as Partial<SalesPlaybook>}
      context={conversationContext}
      className="h-full"
    />
  </div>
)}
```

**Simplifier la marge du chat :**
```tsx
{/* AVANT - Conditionnel sur level */}
<div className={cn(
  "flex-1 mx-auto px-4 flex flex-col",
  (level === "easy" || level === "medium") ? "lg:ml-80 lg:mr-72 max-w-3xl" : "max-w-4xl"
)}>

{/* APRÈS - Conditionnel sur hideHelper */}
<div className={cn(
  "flex-1 mx-auto px-4 flex flex-col",
  !hideHelper ? "lg:ml-[26rem] lg:mr-72 max-w-3xl" : "max-w-4xl"
)}>
```

#### D. Modifier : `lib/api.ts` - Supprimer level de createSession

```typescript
// AVANT
export async function createSession(skillId: number, level: string, ...): Promise<Session> {
  return fetchWithAuth("/training/start", {
    method: "POST",
    body: JSON.stringify({ skill_id: skillId, level, ... }),
  });
}

// APRÈS
export async function createSession(skillId: number, ...): Promise<Session> {
  return fetchWithAuth("/training/start", {
    method: "POST",
    body: JSON.stringify({ skill_id: skillId, ... }),
  });
}
```

#### E. Modifier : `components/training/SalesHelperAccordion.tsx`

```typescript
// AVANT
interface SalesHelperAccordionProps {
  playbook: Partial<SalesPlaybook>;
  context: ConversationContext;
  level: string;  // ← À SUPPRIMER
  className?: string;
}

// APRÈS
interface SalesHelperAccordionProps {
  playbook: Partial<SalesPlaybook>;
  context: ConversationContext;
  className?: string;
  // Plus de level - l'accordéon est le même pour tous
}
```

#### F. Supprimer (cleanup)
- `components/training/LevelSelector.tsx` (si existant)
- Tout composant spécifique à la sélection de niveau

---

## 7. FLOW DE L'INTELLIGENCE CONTEXTUELLE

```
┌─────────────────────────────────────────────────────────────┐
│  HOOK: useConversationPhase                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT:                                                     │
│  ├── messages[]        (historique conversation)            │
│  ├── currentJauge      (0-100)                              │
│  ├── conversionPossible                                     │
│  └── prospectMood      (hostile, neutral, interested...)    │
│                                                             │
│  ANALYSE:                                                   │
│  ├── Compte les échanges                                    │
│  ├── Détecte les patterns d'objection (regex)               │
│  ├── Détecte les signaux d'achat                            │
│  └── Détermine la phase                                     │
│                                                             │
│  OUTPUT: ConversationContext                                │
│  ├── phase: "opening" | "discovery" | "presentation" |      │
│  │          "objection" | "negotiation" | "closing"         │
│  ├── exchangeCount: number                                  │
│  ├── detectedObjectionType: "budget" | "timing" | ...       │
│  └── conversionPossible: boolean                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  COMPOSANT: SalesHelperAccordion                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Reçoit: playbook + conversationContext + level             │
│                                                             │
│  SECTIONS (accordéon):                                      │
│  ├── 👤 Prospect      → Toujours pertinent                  │
│  ├── 💬 Mon Pitch     → Highlight si opening/closing        │
│  ├── ❓ Questions     → Highlight si discovery              │
│  ├── 📦 Ma Solution   → Highlight si presentation           │
│  ├── 🏆 Mes Preuves   → Highlight si negotiation            │
│  └── 🛡️ Objections   → AUTO-OUVRE si objection détectée    │
│                                                             │
│  COMPORTEMENT:                                              │
│  ├── Sections pertinentes = border visible                  │
│  ├── Section highlighted = badge "Utile maintenant"         │
│  ├── Objection détectée = alerte rouge + section ouverte    │
│  └── Scroll interne pour contenu long                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. MAPPING PHASE → SECTIONS

| Phase | Sections Pertinentes | Section Highlight |
|-------|---------------------|-------------------|
| `opening` | prospect, pitch | **pitch** |
| `discovery` | prospect, questions, solution | **questions** |
| `presentation` | solution, proofs, pitch | **solution** |
| `objection` | objections, proofs | **objections** |
| `negotiation` | proofs, solution, objections | **proofs** |
| `closing` | proofs, pitch | **pitch** |

---

## 9. ORDRE D'EXÉCUTION

### Phase 1 : Préparer les playbooks (Backend)
1. [ ] Créer `services/playbook_service.py`
2. [ ] Créer le dossier `playbooks/` avec des fichiers YAML
3. [ ] Créer un playbook exemple complet (AutomateAI)
4. [ ] Tester le chargement

### Phase 2 : Créer les modules de formation (Backend)
1. [ ] Créer `services/module_service.py`
2. [ ] Créer le dossier `training_modules/` avec des fichiers YAML
3. [ ] Créer module BEBEDC complet (`bebedc.yaml`)
4. [ ] Créer module SPIN Selling (`spin_selling.yaml`)
5. [ ] Créer module Closing (`closing.yaml`)
6. [ ] Créer module Objections (`objection_handling.yaml`)
7. [ ] Implémenter `evaluate_session()` avec détection des patterns
8. [ ] Implémenter `generate_report()` pour rapport final

### Phase 3 : Créer TrainingAgent (Backend)
1. [ ] Créer dossier `agents/training_agent/`
2. [ ] Créer `agent.py` - TrainingAgent héritant de BaseAgent
3. [ ] Créer `tools.py` - Outils de l'agent
4. [ ] Créer `memory.py` - Gestion mémoire session
5. [ ] Implémenter `create_session()` avec playbook + module
6. [ ] Implémenter `process_message()` avec évaluation module
7. [ ] Implémenter `end_session()` avec rapport final
8. [ ] Implémenter `_generate_prospect()` via Claude
9. [ ] Implémenter `_generate_prospect_response()` via Claude

### Phase 4 : Intégrer TrainingAgent dans l'orchestrateur
1. [ ] Modifier `orchestrator/main.py` - Ajouter TrainingAgent
2. [ ] Créer `handle_training_request()` dans l'orchestrateur
3. [ ] Supprimer `training_service_v2.py` (plus nécessaire)
4. [ ] Mettre à jour les imports

### Phase 5 : Mettre à jour les endpoints API
1. [ ] Modifier `api/routers/training.py` - Utiliser orchestrateur
2. [ ] Remplacer `level` par `playbook_id` + `module_id`
3. [ ] Modifier `schemas.py` - Mettre à jour les modèles
4. [ ] Tester les endpoints via orchestrateur

### Phase 6 : Génération dynamique du prospect
1. [ ] Tester `_generate_prospect()` dans TrainingAgent
2. [ ] Passer les `prospect_instructions` du module à Claude
3. [ ] S'assurer que le prospect a un BESOIN + des OBJECTIONS
4. [ ] Tester une session complète

### Phase 7 : Supprimer les niveaux (Frontend)
1. [ ] Modifier `app/training/page.tsx` :
   - [ ] Supprimer sélection niveau (easy/medium/hard)
   - [ ] Ajouter sélection produit (playbook)
   - [ ] Ajouter sélection module (BEBEDC, SPIN, etc.)
2. [ ] Modifier `lib/api.ts` - Remplacer `level` par `playbook_id` + `module_id`
3. [ ] Modifier `lib/queries.ts` - Mettre à jour les queries
4. [ ] Tester le démarrage de session avec produit + module

### Phase 8 : Intégrer l'accordéon intelligent (Frontend)
1. [x] Types TypeScript (`types/playbook.ts`)
2. [x] Hook intelligence (`hooks/useConversationPhase.ts`)
3. [x] Composant accordéon (`components/training/SalesHelperAccordion.tsx`)
4. [ ] Modifier `SalesHelperAccordion` - Supprimer prop `level`
5. [ ] Modifier `app/training/session/[id]/page.tsx` :
   - [ ] Supprimer références au `level`
   - [ ] Ajouter toggle "Masquer l'aide"
   - [ ] Intégrer l'accordéon
   - [ ] Ajuster les marges
6. [ ] Tester l'affichage et l'intelligence contextuelle

### Phase 9 : Nouveau rapport de session (Frontend)
1. [ ] Créer composant `SessionReport.tsx` avec structure module
2. [ ] Afficher checklist du module (éléments détectés/manquants)
3. [ ] Afficher score selon type d'évaluation du module
4. [ ] Afficher recommandations personnalisées (matrice module × closing)
5. [ ] Afficher "Prochaine étape suggérée"
6. [ ] Gérer les 4 cas : Jackpot, Succès, Warning, Échec

### Phase 10 : Cleanup
1. [ ] Supprimer `training_service_v2.py`
2. [ ] Supprimer `scenario_loader.py`
3. [ ] Supprimer `scenario_adapter.py`
4. [ ] Supprimer les anciens templates JSON
5. [ ] Supprimer composants liés aux niveaux (si existants)
6. [ ] Renommer tous les fichiers "v2" → noms propres
7. [ ] Mettre à jour la documentation
8. [ ] Run lint + build pour vérifier

---

## 10. EXEMPLE DE PLAYBOOK YAML

Fichier : `backend/playbooks/automate_ai.yaml`

```yaml
# Playbook Commercial - AutomateAI
# Version: 1.0
# Dernière mise à jour: 2024-01

meta:
  id: automate_ai
  version: "1.0"
  product_slug: automate_ai
  skills_compatible:
    - cold_calling
    - objection_handling
    - closing
    - discovery

company:
  name: AutomateAI
  baseline: "L'IA qui travaille pour vous"
  sector: "IA / Automatisation"
  founded: "2022"
  size: "18 employés"
  location: "Paris"
  positioning: |
    Libérer les équipes des tâches administratives répétitives
    pour qu'elles se concentrent sur ce qui compte vraiment.

product:
  name: AutomateAI Box
  type: "SaaS + Hardware"

  problem:
    title: "Les tâches administratives tuent la productivité"
    description: |
      Dans une entreprise moyenne, chaque employé perd 2 à 4 heures par jour
      sur des tâches répétitives et sans valeur ajoutée.
    impacts:
      - "20h/semaine perdues par employé administratif"
      - "Coût caché : 15-25k€/an par employé en temps perdu"
      - "Erreurs humaines : 3-5% sur les tâches répétitives"
    pains_by_persona:
      dirigeant:
        - "Je paie des gens qualifiés pour faire du copier-coller"
        - "On rate des opportunités car on est noyés dans l'admin"
      daf:
        - "Les erreurs de saisie me coûtent cher"
        - "Le reporting prend 2 jours chaque mois"
      manager:
        - "Mon équipe est démotivée par les tâches répétitives"
        - "Les bons partent, je garde ceux qui acceptent la routine"

  how_it_works:
    summary: |
      On installe une petite box dans vos locaux avec des IA spécialisées
      qui apprennent vos process et automatisent vos tâches répétitives.
    steps:
      - title: "Audit (1 journée)"
        description: "On identifie les tâches répétitives et chronophages"
      - title: "Installation (2 heures)"
        description: "Mini-serveur dans vos locaux, aucune donnée ne sort"
      - title: "Configuration (1-2 semaines)"
        description: "On programme les agents IA selon VOS process"
      - title: "Formation (2 jours)"
        description: "Formation pratique avec vos vrais cas d'usage"
    technology: |
      Multi-agents spécialisés : chaque IA fait UNE tâche et la fait bien.
      Agent Tri, Agent Réponse, Agent Extraction, Agent Saisie...
    differentiator: |
      TOUT tourne en LOCAL. Vos données ne sortent JAMAIS.
      100% conforme RGPD par design.

  benefits:
    main: "Gagnez 10-15h par semaine et par employé administratif"
    categories:
      temps:
        - "10-15h gagnées par semaine par employé"
        - "Reporting automatique en temps réel"
        - "Plus de recherche de documents"
      argent:
        - "ROI moyen de 300% la première année"
        - "Économie de 15-25k€/an par employé"
        - "Pas besoin de recruter pour absorber la croissance"
      qualite:
        - "0 erreur sur les tâches répétitives"
        - "Traitement 24h/24, 7j/7"
        - "Traçabilité complète des actions"
      humain:
        - "Équipes recentrées sur les tâches à valeur ajoutée"
        - "Motivation et engagement en hausse"
        - "Réduction du turnover"

  pricing:
    model: "Box (achat) + Abonnement mensuel"
    box:
      price: "2 500€ HT"
      includes: ["Mini-serveur", "Installation", "Garantie 3 ans"]
    offers:
      - name: Starter
        price: "490€/mois"
        includes: ["5 agents IA", "Support email"]
        target: "TPE, 1-10 employés"
      - name: Business
        price: "990€/mois"
        includes: ["15 agents IA", "Support prioritaire", "Optimisation trimestrielle"]
        target: "PME, 10-50 employés"
    engagement: "12 mois (mensuel +20%)"
    guarantees:
      - "30 jours satisfait ou remboursé"
      - "Audit gratuit sans engagement"
      - "ROI garanti ou prolongation gratuite"

pitch:
  hook_30s: |
    Vous savez combien d'heures vos équipes perdent chaque semaine
    à trier des emails, saisir des données ou faire des reporting ?
    En moyenne, c'est 15 à 20 heures par personne.
    Chez AutomateAI, on installe une box avec des IA locales
    qui automatisent ces tâches répétitives.
    Résultat : vos équipes se concentrent sur ce qui compte,
    et vous économisez l'équivalent d'un mi-temps par employé.

  pitch_2min: |
    Je vais être direct : vos équipes administratives perdent
    probablement 15 à 20 heures par semaine sur des tâches répétitives.

    Trier des emails, répondre aux mêmes questions, saisir des données,
    chercher des documents, faire des reporting...
    Des tâches qu'un robot pourrait faire.

    Le problème c'est que jusqu'ici, les solutions d'automatisation
    c'était soit trop complexe, soit ça envoyait vos données dans le cloud,
    soit ça coûtait une fortune.

    Nous, on a créé AutomateAI Box.

    C'est un mini-serveur qu'on installe chez vous avec des IA spécialisées.
    Chaque IA fait UNE tâche et la fait parfaitement.
    On les programme selon VOS process.
    Vos données restent chez VOUS, 100% RGPD.

    Nos clients gagnent en moyenne 12 heures par semaine par employé.
    À 30€ de l'heure chargé, ça fait 1 500€ d'économie par mois
    pour un abonnement à 490€.

    On fait un audit gratuit pour mesurer votre potentiel ?

  discovery_questions:
    situation:
      - "Combien de personnes avez-vous sur des fonctions administratives ?"
      - "Quelles sont les tâches qui prennent le plus de temps ?"
      - "Comment gérez-vous le tri des emails aujourd'hui ?"
    pain:
      - "Qu'est-ce qui vous frustre le plus dans la gestion administrative ?"
      - "Avez-vous déjà calculé le coût de ces tâches répétitives ?"
      - "Que pourrait faire votre équipe si elle avait 10h de plus par semaine ?"
    impact:
      - "Combien vous coûte une erreur de saisie en moyenne ?"
      - "Que se passe-t-il quand un email client tombe dans les limbes ?"
    decision:
      - "Qui d'autre serait concerné par ce type de décision ?"
      - "Qu'est-ce qui vous ferait dire 'oui, on y va' ?"

  key_phrases:
    hooks:
      - "Combien d'heures perdez-vous chaque semaine à faire le travail d'un robot ?"
      - "Et si vos équipes pouvaient enfin se concentrer sur ce qui compte ?"
    transitions:
      - "Ce que vous décrivez, c'est exactement ce que notre client X vivait..."
      - "Justement, c'est pour ça qu'on a conçu..."
    proofs:
      - "Notre client Dupont & Fils a réduit son temps admin de 60%"
      - "En moyenne, nos clients voient le ROI en 3 mois"
    closings:
      - "On fait un audit gratuit la semaine prochaine ?"
      - "Qu'est-ce qui vous empêcherait de tester pendant 30 jours ?"

objections:
  - type: budget
    label: "Trop cher"
    variants:
      - "On n'a pas le budget"
      - "2500€ + 490€/mois c'est costaud"
      - "On peut pas se permettre ça maintenant"
    hidden_meaning: "Je ne vois pas le ROI"
    response: |
      Je comprends, c'est un investissement.

      Faisons le calcul ensemble :
      Vous avez 3 personnes sur l'administratif.
      Si chacune gagne 10h par semaine, ça fait 30h.
      À 25€ de l'heure chargé, ça fait 3 000€ par mois.

      L'abonnement est à 490€.
      Vous économisez 2 500€ par mois dès le premier mois.
      La box est rentabilisée en 1 mois.

      Et si le ROI n'est pas là après 30 jours, on vous rembourse.
    proof: "Dupont & Fils : ROI atteint en 6 semaines"

  - type: timing
    label: "Pas le moment"
    variants:
      - "Rappelez-moi dans 6 mois"
      - "On est en plein rush"
      - "C'est pas le moment"
    hidden_meaning: "J'ai pas la bande passante pour un nouveau projet"
    response: |
      Je comprends, vous avez beaucoup à gérer.

      Justement, combien de temps vos équipes perdent chaque semaine
      sur ces tâches répétitives ?

      Chaque mois qu'on attend, c'est 60h de perdues.
      Et l'installation prend 2h. La formation 2 jours.
      Ce n'est pas un projet de 6 mois.

      On peut commencer par un audit gratuit d'1h ?
    proof: "Coût de l'attente : 60h/mois perdues"

  - type: trust
    label: "Je vous connais pas"
    variants:
      - "AutomateAI... jamais entendu parler"
      - "C'est quoi votre boîte ?"
      - "Vous êtes fiables ?"
    hidden_meaning: "Peur de me faire avoir"
    response: |
      Question légitime.

      On existe depuis 2022, on équipe 47 PME.
      Certifié par l'ANSSI.
      Hébergement 100% France.

      Et surtout : 30 jours d'essai sans engagement.
      Si ça ne marche pas, on rembourse.
    proof: "47 clients, ANSSI, essai gratuit"

  - type: status_quo
    label: "Ça fonctionne comme ça"
    variants:
      - "On a toujours fait comme ça"
      - "Ça marche bien pour nous"
      - "Pourquoi changer ?"
    hidden_meaning: "Flemme de changer les habitudes"
    response: |
      Je comprends, le changement c'est jamais simple.

      Mais est-ce que ça fonctionne vraiment bien ?
      Ou est-ce qu'on s'est juste habitué aux problèmes ?

      Vos équipes, elles aiment passer 20h par semaine
      à faire du copier-coller ? Ou elles aimeraient
      faire quelque chose de plus intéressant ?

      On ne change pas tout. On automatise juste
      les tâches que personne n'aime faire.
    proof: "Cabinet Martin : 'On aurait dû faire ça avant'"

proofs:
  stats:
    clients: "47 PME équipées"
    satisfaction: "4.8/5 sur 120 avis"
    main_result: "12h/semaine gagnées en moyenne"
    roi_average: "ROI en 3 mois"

  testimonials:
    - client_name: "Pierre Dupont"
      client_role: "Directeur Général"
      company: "Dupont & Fils"
      sector: "Négoce BTP"
      size: "35 employés"
      problem_before: |
        4 personnes à l'administratif.
        20h/semaine chacun sur tâches répétitives.
        Erreurs de saisie fréquentes.
        Retards de facturation.
      solution: |
        AutomateAI Box Business.
        5 agents configurés : Tri email, Saisie commandes,
        Extraction factures, Reporting, Relances.
      results:
        - "60% de réduction du temps admin"
        - "0 erreur de saisie (vs 3-5% avant)"
        - "ROI atteint en 6 semaines"
        - "+30% de croissance absorbée sans recruter"
      quote: |
        Mes équipes admin passaient leur temps à faire du copier-coller.
        Maintenant elles gèrent la relation client.
        On a absorbé 30% de croissance sans recruter personne.

    - client_name: "Sophie Martin"
      client_role: "Gérante"
      company: "Cabinet Martin Expertise"
      sector: "Expert-comptable"
      size: "12 employés"
      problem_before: |
        Tri manuel de 200 emails/jour.
        Saisie des factures fournisseurs manuelle.
        Avaient testé 3 solutions avant (échecs).
      results:
        - "4h/jour gagnées sur le tri email"
        - "Saisie factures : 2min vs 15min"
        - "Adoption : 95% dès la 2ème semaine"
      quote: |
        On avait tout essayé. AutomateAI c'est la première solution
        que l'équipe utilise vraiment. Parce que c'est simple.

  certifications:
    - "Certifié ANSSI"
    - "Label France Cybersecurity"
    - "Hébergement France (OVH)"
    - "Conforme RGPD"

  references:
    - "Dupont & Fils"
    - "Cabinet Martin"
    - "MécaPrécision"
    - "Groupe Hôtelier Lumière"
```

---

## 11. CHECKLIST FINALE

### Backend - Playbooks
- [ ] Lire et valider ce document
- [ ] Créer le dossier `backend/playbooks/`
- [ ] Créer `automate_ai.yaml` avec le contenu ci-dessus
- [ ] Créer `PlaybookService`

### Backend - Modules de formation
- [ ] Créer le dossier `backend/training_modules/`
- [ ] Créer `bebedc.yaml` (module complet)
- [ ] Créer `spin_selling.yaml`
- [ ] Créer `closing.yaml`
- [ ] Créer `objection_handling.yaml`
- [ ] Créer `ModuleService` avec :
  - [ ] `load_module()` - charger un module YAML
  - [ ] `evaluate_session()` - évaluer selon le module
  - [ ] `calculate_final_result()` - matrice module × closing
  - [ ] `generate_report()` - générer rapport final

### Backend - TrainingAgent
- [ ] Créer dossier `agents/training_agent/`
- [ ] Créer `agent.py` - TrainingAgent héritant de BaseAgent
- [ ] Créer `tools.py` - Outils de l'agent
- [ ] Créer `memory.py` - Gestion mémoire session
- [ ] Implémenter :
  - [ ] `create_session()` avec playbook + module
  - [ ] `process_message()` avec évaluation module
  - [ ] `end_session()` avec rapport final
  - [ ] `_generate_prospect()` via Claude
  - [ ] `_generate_prospect_response()` via Claude

### Backend - Orchestrateur
- [ ] Modifier `orchestrator/main.py` - Ajouter TrainingAgent
- [ ] Créer `handle_training_request()` dans l'orchestrateur

### Backend - API
- [ ] Modifier `api/routers/training.py` - Utiliser orchestrateur
- [ ] Remplacer `level` par `playbook_id` + `module_id`
- [ ] Modifier `schemas.py` - mettre à jour les modèles
- [ ] Tester API via orchestrateur

### Frontend - Sélection session
- [ ] Modifier `app/training/page.tsx` :
  - [ ] Supprimer sélection niveau (easy/medium/hard)
  - [ ] Ajouter sélection produit (playbook)
  - [ ] Ajouter sélection module (BEBEDC, SPIN, etc.)
- [ ] Modifier `lib/api.ts` - level → module_id
- [ ] Modifier `lib/queries.ts` - mettre à jour

### Frontend - Session et accordéon
- [ ] Modifier `SalesHelperAccordion` - supprimer prop `level`
- [ ] Modifier `app/training/session/[id]/page.tsx` :
  - [ ] Supprimer références au level
  - [ ] Ajouter toggle "Masquer l'aide"
  - [ ] Intégrer l'accordéon intelligent
- [ ] Tester l'affichage et l'intelligence contextuelle

### Frontend - Nouveau rapport
- [ ] Créer `components/training/SessionReport.tsx`
- [ ] Afficher checklist module (éléments détectés/manquants)
- [ ] Afficher score selon type d'évaluation
- [ ] Afficher recommandations personnalisées
- [ ] Afficher statut maîtrise (pas juste closing)

### Cleanup
- [ ] Supprimer `training_service_v2.py`
- [ ] Supprimer `scenario_loader.py`
- [ ] Supprimer `scenario_adapter.py`
- [ ] Supprimer les anciens templates JSON
- [ ] Renommer fichiers "v2" → noms propres (si restants)
- [ ] Run `npm run lint` et `npm run build`
- [ ] Tester end-to-end

---

## 12. INFRASTRUCTURE & SCALABILITÉ (100+ users)

### Stratégie : APIs pour dev, Local pour prod

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENVIRONNEMENTS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DEV / TEST                        PROD (100+ users)            │
│  ──────────                        ─────────────────            │
│  Claude API ──────────────────────► Qwen 14B (local)            │
│  ElevenLabs ──────────────────────► Chatterbox (local)          │
│  Whisper OpenAI ──────────────────► Whisper (local)             │
│                                                                 │
│  Coût : ~$10-50/mois               Coût : ~$150-300/mois        │
│  (pay per use, faible volume)      (fixe, illimité)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Services abstraits (switch dev ↔ prod)

```python
# backend/services/llm_service.py

class LLMService:
    """Abstraction LLM - switch via config."""

    def __init__(self):
        provider = settings.LLM_PROVIDER  # "claude" ou "local"

        if provider == "claude":
            self.client = ClaudeClient(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = LocalLLMClient(
                base_url=settings.LOCAL_LLM_URL,  # Vast.ai endpoint
                model="qwen2.5-14b-instruct"
            )

    async def generate(self, prompt: str, system: str = None) -> str:
        return await self.client.generate(prompt, system=system)
```

```python
# backend/services/voice_service.py

class VoiceService:
    """Abstraction Voice - switch via config."""

    def __init__(self):
        provider = settings.VOICE_PROVIDER  # "elevenlabs" ou "local"

        if provider == "elevenlabs":
            self.tts = ElevenLabsTTS(api_key=settings.ELEVENLABS_API_KEY)
            self.stt = WhisperOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.tts = ChatterboxTTS(base_url=settings.LOCAL_TTS_URL)
            self.stt = WhisperLocal(base_url=settings.LOCAL_STT_URL)

    async def text_to_speech(self, text: str, voice: str) -> bytes:
        return await self.tts.synthesize(text, voice=voice)

    async def speech_to_text(self, audio: bytes) -> str:
        return await self.stt.transcribe(audio)
```

### Chatterbox Turbo - Optimisation latence

Pour réduire la latence TTS, utiliser **Chatterbox Turbo** au lieu du modèle standard :

```
Chatterbox Standard vs Turbo :

Standard (chatterbox)
├── Paramètres : ~1B
├── Backbone : LLaMA
├── Inference : 10 étapes CFM
├── Latence : 1-2 secondes
└── VRAM : ~8GB

Turbo (chatterbox-turbo)
├── Paramètres : 350M
├── Backbone : GPT-2 (plus rapide)
├── Inference : 1 seule étape (distillé)
├── Latence : 500ms - 1s (réel)
├── VRAM : ~4GB
└── Time-to-first-sound : sub-150ms (théorique)
```

**Configuration Turbo :**

```python
# backend/services/tts/chatterbox.py

class ChatterboxTTS:
    def __init__(self, base_url: str, use_turbo: bool = True):
        self.model = "chatterbox-turbo" if use_turbo else "chatterbox"
        # Version ONNX pour encore plus de vitesse
        self.use_onnx = True  # chatterbox-turbo-ONNX

    async def synthesize(self, text: str, voice: str) -> bytes:
        # Streaming natif pour latence minimale
        async for chunk in self._stream_generate(text, voice):
            yield chunk
```

**Streaming pour latence perçue :**

```
Sans streaming :
[Génération complète 2s] → [Playback]

Avec streaming Turbo :
[Chunk 1] → [Playback début]
[Chunk 2] → [Continue playback]
...

→ Time-to-first-sound : ~200-500ms au lieu de 2s
```

**Docker Turbo :**

```yaml
# docker-compose.vastai.yml - TTS optimisé
tts:
  image: ghcr.io/resemble-ai/chatterbox-turbo:latest
  environment:
    - MODEL=turbo
    - USE_ONNX=true
    - STREAMING=true
  ports:
    - "8001:8001"
```

### Configuration .env

```bash
# backend/.env

# ============================================
# DEV : APIs (défaut)
# ============================================
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...

VOICE_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=...
OPENAI_API_KEY=sk-...

# ============================================
# PROD : Local (décommenter pour prod)
# ============================================
# LLM_PROVIDER=local
# LOCAL_LLM_URL=http://vast-ai-instance:8000/v1

# VOICE_PROVIDER=local
# LOCAL_TTS_URL=http://vast-ai-instance:8001
# LOCAL_STT_URL=http://vast-ai-instance:8002
```

### Déploiement Vast.ai

```yaml
# docker-compose.vastai.yml

services:
  llm:
    image: vllm/vllm-openai:latest
    command: >
      --model Qwen/Qwen2.5-14B-Instruct
      --tensor-parallel-size 1
      --max-model-len 8192
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  tts:
    image: chatterbox-tts:latest  # À builder
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  stt:
    image: whisper-api:latest
    environment:
      - MODEL=large-v3
    ports:
      - "8002:8002"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

### Comparatif coûts

| Scénario | Provider | Coût estimé |
|----------|----------|-------------|
| **Dev solo** | Claude + ElevenLabs + Whisper OAI | ~$20-50/mois |
| **Beta 10 users** | Claude + ElevenLabs + Whisper OAI | ~$50-150/mois |
| **Prod 100 users** | Vast.ai (RTX 4090) | ~$200-300/mois fixe |
| **Prod 100 users** | Serveur dédié (Hetzner) | ~$250-400/mois fixe |

### Seuil de rentabilité

```
APIs vs Local - Point de bascule :

Claude : ~$0.01/message
ElevenLabs : ~$0.30/1000 chars (~$0.10/message)
Whisper OAI : ~$0.006/min

Total par message : ~$0.12

Vast.ai RTX 4090 : ~$0.50/h = $360/mois

Seuil : 360 / 0.12 = ~3000 messages/mois

→ Si > 3000 messages/mois → Local rentable
→ 100 users × 30 messages = 3000 → Exactement le seuil!

Conclusion : Dès 100 users actifs, local = rentable
```

### Hardware requis (Vast.ai)

```
Pour Qwen 14B + Chatterbox + Whisper :
├── GPU : RTX 4090 (24GB VRAM) ou A100 40GB
├── RAM : 32GB minimum
├── Storage : 100GB SSD
└── Coût Vast.ai : ~$0.40-0.80/h
```

### Capacité serveur unique

```
1x RTX 4090 :
├── LLM : ~20-30 tokens/sec
├── TTS : ~1.5x realtime (1 sec audio = 0.7 sec génération)
├── STT : ~10x realtime
│
├── Sessions simultanées : 50-100
├── Latence réponse : 2-5 sec (acceptable)
└── ⚠️ Si >100 simultanés : ajouter 2ème GPU
```

### Migration Dev → Prod

```
Phase 1 (maintenant) : Dev avec APIs
├── Développer avec Claude/ElevenLabs
├── Tester fonctionnalités
└── Coût minimal

Phase 2 (beta) : Test avec quelques users
├── Toujours APIs
├── Mesurer usage réel
└── Valider product-market fit

Phase 3 (prod) : Switch vers local
├── Déployer sur Vast.ai
├── Changer .env : LLM_PROVIDER=local
├── Tester performances
└── Basculer le trafic
```

---

## RÉSUMÉ ARCHITECTURE FINALE

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
├─────────────────────────────────────────────────────────────────┤
│  training/page.tsx      → Sélection playbook + module           │
│  training/session/      → Accordéon intelligent + toggle        │
│  SessionReport.tsx      → Rapport avec matrice module×closing   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                               │
├─────────────────────────────────────────────────────────────────┤
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│   ┌───────────┐     ┌─────────────┐    ┌───────────┐          │
│   │AudioAgent │     │TrainingAgent│    │PatternAgent│          │
│   └───────────┘     └──────┬──────┘    └───────────┘          │
│                            │                                    │
│              ┌─────────────┼─────────────┐                     │
│              ▼             ▼             ▼                     │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│       │ Playbook │  │  Module  │  │  Jauge   │                │
│       │ Service  │  │ Service  │  │ Service  │                │
│       └────┬─────┘  └────┬─────┘  └──────────┘                │
│            │             │                                      │
│            ▼             ▼                                      │
│       ┌──────────┐  ┌──────────┐                               │
│       │ YAML     │  │ YAML     │                               │
│       │playbooks/│  │modules/  │                               │
│       └──────────┘  └──────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```
