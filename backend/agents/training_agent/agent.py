"""
Training Agent - Agent de formation commerciale avec playbooks et modules.

Gère les sessions d'entraînement avec :
- Playbook commercial (produit, pitch, objections)
- Module de formation (BEBEDC, SPIN, etc.)
- Évaluation en temps réel selon le module
"""

import os
import random
import uuid

import structlog

from agents.base_agent import BaseAgent, ToolResult
from services.jauge_service import BehavioralDetector, JaugeService
from services.module_service import ModuleService
from services.playbook_service import Playbook, PlaybookService

logger = structlog.get_logger()

# LLM clients
try:
    from groq import AsyncGroq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class TrainingAgent(BaseAgent):
    """
    Agent de formation commerciale.

    Gère les sessions d'entraînement avec playbook + module.
    Remplace l'ancien système basé sur scenario/patterns/difficulty.
    """

    name = "training"
    description = "Gère les sessions de formation commerciale"

    SYSTEM_PROMPT = """Tu es le Training Agent de Champion Clone.

Ton rôle est de gérer les sessions d'entraînement où les utilisateurs pratiquent leurs techniques de vente.

CAPACITÉS:
1. create_session: Créer une nouvelle session avec playbook + module
2. process_message: Traiter un message utilisateur et générer la réponse prospect
3. end_session: Terminer une session et générer le rapport final
4. get_session_status: Obtenir l'état actuel d'une session

WORKFLOW:
1. Charger le playbook (produit, pitch, objections)
2. Charger le module (BEBEDC, SPIN, etc.)
3. Générer le prospect dynamiquement selon playbook + module
4. Pour chaque message utilisateur:
   - Évaluer selon les critères du module
   - Mettre à jour la jauge émotionnelle
   - Générer la réponse du prospect
5. À la fin, générer un rapport selon le module

RÈGLES:
- Le prospect ne révèle pas tout spontanément
- L'évaluation suit les critères du module choisi
- La jauge émotionnelle évolue selon la qualité des échanges
"""

    def __init__(self):
        super().__init__(name="Training Agent", model=os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514"))

        # Services
        self.playbook_service = PlaybookService()
        self.module_service = ModuleService()
        self.jauge_service = JaugeService()
        self.behavioral_detector = BehavioralDetector()

        # LLM client
        self._init_llm_client()

        # Sessions actives (en mémoire pour l'instant)
        self._sessions: dict[str, dict] = {}

    def _init_llm_client(self):
        """Initialise le client LLM (Groq gratuit ou Anthropic)."""
        self.use_groq = GROQ_AVAILABLE and os.getenv("GROQ_API_KEY")
        self.use_anthropic = ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY")

        if self.use_groq:
            self.llm_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            self.llm_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info("training_agent_init", provider="groq", model=self.llm_model)
        elif self.use_anthropic:
            self.llm_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.llm_model = os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514")
            logger.info("training_agent_init", provider="anthropic", model=self.llm_model)
        else:
            self.llm_client = None
            self.llm_model = None
            logger.warning("training_agent_init", msg="No LLM provider. Set GROQ_API_KEY or ANTHROPIC_API_KEY")

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "create_session",
                "description": "Create a new training session with playbook and module",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "playbook_id": {"type": "string", "description": "Playbook ID (e.g., 'automate_ai')"},
                        "module_id": {"type": "string", "description": "Module ID (e.g., 'bebedc', 'spin_selling')"},
                        "user_id": {"type": "string", "description": "User ID"},
                    },
                    "required": ["playbook_id", "module_id"],
                },
            },
            {
                "name": "process_message",
                "description": "Process user message and get prospect response",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Session ID"},
                        "message": {"type": "string", "description": "User's message"},
                    },
                    "required": ["session_id", "message"],
                },
            },
            {
                "name": "end_session",
                "description": "End session and generate final report",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Session ID"},
                        "closing_achieved": {"type": "boolean", "description": "Whether closing was achieved"},
                    },
                    "required": ["session_id"],
                },
            },
            {
                "name": "get_session_status",
                "description": "Get current session status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Session ID"},
                    },
                    "required": ["session_id"],
                },
            },
        ]

    async def execute_tool(self, name: str, input_data: dict) -> ToolResult:
        """Execute a tool and return the result."""
        try:
            if name == "create_session":
                result = await self.create_session(
                    playbook_id=input_data["playbook_id"],
                    module_id=input_data["module_id"],
                    user_id=input_data.get("user_id", "anonymous"),
                )
            elif name == "process_message":
                result = await self.process_message(
                    session_id=input_data["session_id"],
                    message=input_data["message"],
                )
            elif name == "end_session":
                result = await self.end_session(
                    session_id=input_data["session_id"],
                    closing_achieved=input_data.get("closing_achieved", False),
                )
            elif name == "get_session_status":
                result = await self.get_session_status(input_data["session_id"])
            else:
                return ToolResult(tool_name=name, success=False, output=None, error=f"Unknown tool: {name}")

            return ToolResult(
                tool_name=name,
                success=result.get("success", True),
                output=result,
                error=result.get("error"),
            )

        except Exception as e:
            logger.error("tool_execution_error", tool=name, error=str(e))
            return ToolResult(tool_name=name, success=False, output=None, error=str(e))

    # ============================================
    # SESSION MANAGEMENT
    # ============================================

    async def create_session(
        self,
        playbook_id: str,
        module_id: str,
        user_id: str = "anonymous",
    ) -> dict:
        """
        Crée une nouvelle session d'entraînement.

        Args:
            playbook_id: ID du playbook (produit à vendre)
            module_id: ID du module (méthode de vente)
            user_id: ID de l'utilisateur

        Returns:
            Dict avec session_id, first_message, playbook_data
        """
        # Charger playbook et module
        try:
            playbook = await self.playbook_service.load(playbook_id)
            module = await self.module_service.load_module(module_id)
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}

        # Créer l'ID de session
        session_id = str(uuid.uuid4())[:8]

        # Générer le prospect
        prospect = await self._generate_prospect(playbook, module)

        # Construire le system prompt pour le prospect
        system_prompt = self._build_prospect_system_prompt(playbook, module, prospect)

        # Générer le premier message du prospect
        first_message = await self._generate_prospect_response(
            system_prompt=system_prompt,
            conversation=[],
            user_message="START",
        )

        # Initialiser la jauge
        initial_jauge = self.jauge_service.starting_jauge
        initial_mood = self.jauge_service.get_mood(initial_jauge)
        jauge_state = {
            "value": initial_jauge,
            "mood": initial_mood.mood,
            "behavior": initial_mood.behavior,
        }

        # Créer la session
        session = {
            "id": session_id,
            "user_id": user_id,
            "playbook_id": playbook_id,
            "module_id": module_id,
            "playbook": playbook,
            "module": module,
            "prospect": prospect,
            "system_prompt": system_prompt,
            "conversation": [{"role": "prospect", "content": first_message}],
            "jauge": jauge_state,
            "module_progress": {"detected": [], "scores": {}},
            "status": "active",
        }

        self._sessions[session_id] = session

        logger.info(
            "session_created",
            session_id=session_id,
            playbook=playbook_id,
            module=module_id,
        )

        return {
            "success": True,
            "session_id": session_id,
            "first_message": first_message,
            "prospect": prospect,
            "playbook_data": self._get_playbook_for_frontend(playbook),
            "module_data": {
                "id": module["id"],
                "name": module["name"],
                "checklist": module.get("checklist", []),
            },
            "jauge": jauge_state,
        }

    async def process_message(
        self,
        session_id: str,
        message: str,
    ) -> dict:
        """
        Traite un message de l'utilisateur.

        Args:
            session_id: ID de la session
            message: Message de l'utilisateur

        Returns:
            Dict avec prospect_response, evaluation, jauge
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if session["status"] != "active":
            return {"success": False, "error": "Session is not active"}

        # Ajouter le message utilisateur
        session["conversation"].append({"role": "user", "content": message})

        # Évaluer selon le module
        module_eval = await self.module_service.evaluate_message(
            module=session["module"],
            message=message,
            history=session["conversation"],
            current_progress=session["module_progress"],
        )
        session["module_progress"] = module_eval["progress"]

        # Détecter les patterns pour la jauge
        patterns = self.behavioral_detector.detect_patterns(message)

        # Appliquer les actions détectées
        current_jauge = session["jauge"]["value"]
        modifications = []

        for pos in patterns["positive"]:
            mod = self.jauge_service.apply_action(current_jauge, pos["action"], "positive")
            current_jauge = mod.new_value
            modifications.append(mod.to_dict())

        for neg in patterns["negative"]:
            mod = self.jauge_service.apply_action(current_jauge, neg["action"], "negative")
            current_jauge = mod.new_value
            modifications.append(mod.to_dict())

        # Mettre à jour l'état de la jauge
        mood_state = self.jauge_service.get_mood(current_jauge)
        session["jauge"] = {
            "value": current_jauge,
            "mood": mood_state.mood,
            "behavior": mood_state.behavior,
        }
        behaviors = {
            "patterns": patterns,
            "modifications": modifications,
        }

        # Vérifier si la session doit se terminer
        is_complete = self._check_session_complete(session)

        if is_complete:
            session["status"] = "completed"
            return {
                "success": True,
                "session_complete": True,
                "evaluation": module_eval,
                "jauge": session["jauge"],
                "behaviors": behaviors,
            }

        # Générer la réponse du prospect
        prospect_response = await self._generate_prospect_response(
            system_prompt=session["system_prompt"],
            conversation=session["conversation"],
            user_message=message,
            jauge_mood=session["jauge"]["mood"],
        )

        # Ajouter la réponse du prospect
        session["conversation"].append({"role": "prospect", "content": prospect_response})

        return {
            "success": True,
            "prospect_response": prospect_response,
            "evaluation": module_eval,
            "jauge": session["jauge"],
            "behaviors": behaviors,
            "session_complete": False,
        }

    async def end_session(
        self,
        session_id: str,
        closing_achieved: bool = False,
    ) -> dict:
        """
        Termine une session et génère le rapport final.

        Args:
            session_id: ID de la session
            closing_achieved: Si le closing a été obtenu

        Returns:
            Dict avec le rapport complet
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Évaluer la session complète
        evaluation = await self.module_service.evaluate_session(
            module=session["module"],
            messages=session["conversation"],
        )

        # Calculer le résultat final (module × closing)
        final_result = self.module_service.calculate_final_result(
            module_score=evaluation.score,
            module_threshold=session["module"].get("evaluation", {}).get("mastery_threshold", 70),
            closing=closing_achieved,
            module=session["module"],
        )

        # Générer le rapport
        report = await self.module_service.generate_report(
            module=session["module"],
            evaluation=evaluation,
            session={
                "id": session_id,
                "duration": None,  # TODO: calculer
                "message_count": len([m for m in session["conversation"] if m["role"] == "user"]),
                "jauge": session["jauge"],
            },
            result=final_result,
        )

        # Marquer comme terminée
        session["status"] = "completed"

        logger.info(
            "session_ended",
            session_id=session_id,
            score=evaluation.score,
            closing=closing_achieved,
            result=final_result.result_key,
        )

        return {
            "success": True,
            "session_id": session_id,
            "evaluation": evaluation.to_dict(),
            "final_result": final_result.to_dict(),
            "report": report,
        }

    async def get_session_status(self, session_id: str) -> dict:
        """Retourne l'état actuel d'une session."""
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        return {
            "success": True,
            "session_id": session_id,
            "status": session["status"],
            "playbook_id": session["playbook_id"],
            "module_id": session["module_id"],
            "message_count": len(session["conversation"]),
            "jauge": session["jauge"],
            "module_progress": {
                "detected_count": len(session["module_progress"]["detected"]),
                "total_elements": len(session["module"].get("checklist", [])),
            },
        }

    # ============================================
    # PROSPECT GENERATION
    # ============================================

    async def _generate_prospect(self, playbook: Playbook, module: dict) -> dict:
        """
        Génère dynamiquement un prospect basé sur le playbook et le module.

        Args:
            playbook: Le playbook commercial
            module: Le module de formation

        Returns:
            Dict avec les infos du prospect
        """
        # Choisir un persona parmi ceux définis dans le playbook
        pains = playbook.product.problem.pains_by_persona if playbook.product.problem else {}
        personas = list(pains.keys()) if pains else ["dirigeant"]
        persona = random.choice(personas)

        # Générer un nom réaliste
        first_names = ["Jean-Pierre", "Marie", "Philippe", "Sophie", "Laurent", "Isabelle", "François", "Catherine"]
        last_names = ["Martin", "Dubois", "Bernard", "Leroy", "Moreau", "Petit", "Roux", "Vincent"]
        name = f"{random.choice(first_names)} {random.choice(last_names)}"

        # Générer le contexte du prospect
        prospect = {
            "name": name,
            "persona": persona,
            "company_type": self._generate_company_type(playbook),
            "pain_points": pains.get(persona, []),
            "hidden_objections": self._select_hidden_objections(playbook),
            "decision_context": self._generate_decision_context(),
        }

        logger.info("prospect_generated", name=name, persona=persona)

        return prospect

    def _generate_company_type(self, playbook: Playbook) -> str:
        """Génère un type d'entreprise cohérent avec le playbook."""
        # Basé sur le secteur du playbook
        sector = playbook.company.sector if playbook.company else ""
        if "IA" in sector or "Tech" in sector:
            companies = ["PME tech", "Startup SaaS", "ESN", "Cabinet de conseil"]
        else:
            companies = ["PME industrielle", "ETI", "Groupe familial", "Franchise"]

        return random.choice(companies)

    def _select_hidden_objections(self, playbook: Playbook) -> list[dict]:
        """Sélectionne 2-3 objections cachées depuis le playbook."""
        objections = playbook.objections[:5] if playbook.objections else []
        selected = random.sample(objections, min(2, len(objections)))

        return [
            {
                "type": obj.type,
                "label": obj.label,
                "hidden_meaning": obj.hidden_meaning,
            }
            for obj in selected
        ]

    def _generate_decision_context(self) -> dict:
        """Génère le contexte de décision du prospect."""
        budgets = ["non défini", "10-20k€", "20-50k€", "50k€+"]
        timings = ["urgent (1 mois)", "moyen terme (3 mois)", "pas pressé (6 mois+)"]
        decision_makers = [
            "Je décide seul",
            "Mon manager doit valider",
            "Comité de direction",
            "Direction générale",
        ]

        return {
            "budget": random.choice(budgets),
            "timing": random.choice(timings),
            "decision_maker": random.choice(decision_makers),
            "competitors_looking": random.choice([True, False]),
        }

    def _build_prospect_system_prompt(
        self,
        playbook: Playbook,
        module: dict,
        prospect: dict,
    ) -> str:
        """Construit le system prompt pour le prospect."""
        # Instructions du module
        module_instructions = module.get("prospect_instructions", "")

        # Contexte du playbook
        product_context = f"""
PRODUIT PRÉSENTÉ: {playbook.product.name}
ENTREPRISE: {playbook.company.name}
PROBLÈME RÉSOLU: {playbook.product.problem.title if playbook.product.problem else ""}
"""

        # Contexte du prospect
        prospect_context = f"""
TON PROFIL:
- Tu es {prospect["persona"]} d'une {prospect["company_type"]}
- Tes problèmes: {", ".join(prospect["pain_points"][:2])}
- Budget: {prospect["decision_context"]["budget"]}
- Timing: {prospect["decision_context"]["timing"]}
- Pouvoir de décision: {prospect["decision_context"]["decision_maker"]}
- Tu regardes d'autres solutions: {"Oui" if prospect["decision_context"]["competitors_looking"] else "Non"}
"""

        # Objections cachées
        objections_context = ""
        if prospect.get("hidden_objections"):
            objections_list = "\n".join(
                [f"- {obj['label']}: {obj['hidden_meaning']}" for obj in prospect["hidden_objections"]]
            )
            objections_context = f"""
OBJECTIONS CACHÉES (ne les révèle que si bien questionné):
{objections_list}
"""

        return f"""Tu es un prospect réaliste dans une session de formation commerciale.

{product_context}

{prospect_context}

{objections_context}

INSTRUCTIONS DU MODULE:
{module_instructions}

RÈGLES GÉNÉRALES:
1. Tu joues le rôle du PROSPECT, pas du vendeur
2. Sois réaliste - pose des questions, hésite, objecte
3. Ne révèle PAS tout spontanément
4. Réponds aux questions posées, pas plus
5. Réponds de manière concise (1-3 phrases max)
6. Si le commercial est maladroit, montre ton scepticisme
7. Si le commercial est bon, ouvre-toi progressivement

Commence par "Bonjour" quand on te dit "START"."""

    async def _generate_prospect_response(
        self,
        system_prompt: str,
        conversation: list[dict],
        user_message: str,
        jauge_mood: str = "neutral",
    ) -> str:
        """
        Génère la réponse du prospect via LLM.

        Args:
            system_prompt: Le system prompt du prospect
            conversation: L'historique de conversation
            user_message: Le dernier message utilisateur
            jauge_mood: L'humeur actuelle de la jauge

        Returns:
            La réponse du prospect
        """
        if not self.llm_client:
            return "Je suis là, qu'est-ce que vous proposez ?"

        # Construire les messages
        messages = []
        for msg in conversation:
            role = "assistant" if msg["role"] == "prospect" else "user"
            messages.append({"role": role, "content": msg["content"]})

        if user_message != "START":
            messages.append({"role": "user", "content": user_message})

        # Ajouter l'indication d'humeur
        mood_instruction = ""
        if jauge_mood == "hostile":
            mood_instruction = "\n[Tu es agacé et impatient. Réponds sèchement.]"
        elif jauge_mood == "skeptical":
            mood_instruction = "\n[Tu es dubitatif. Pose des questions challengeantes.]"
        elif jauge_mood == "interested":
            mood_instruction = "\n[Tu es intéressé. Montre de la curiosité.]"
        elif jauge_mood == "ready":
            mood_instruction = "\n[Tu es convaincu. Tu veux avancer.]"

        system_with_mood = system_prompt + mood_instruction

        try:
            if self.use_groq:
                # Groq (format OpenAI)
                groq_messages = [{"role": "system", "content": system_with_mood}]
                groq_messages.extend(messages)
                if user_message == "START":
                    groq_messages.append({"role": "user", "content": "START"})

                response = await self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=groq_messages,
                    max_tokens=256,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            else:
                # Anthropic
                if user_message == "START":
                    messages.append({"role": "user", "content": "START"})

                response = await self.llm_client.messages.create(
                    model=self.llm_model,
                    max_tokens=256,
                    system=system_with_mood,
                    messages=messages,
                    temperature=0.7,
                )
                return response.content[0].text.strip()

        except Exception as e:
            logger.error("prospect_response_error", error=str(e))
            return "Pardon, je n'ai pas bien compris. Pouvez-vous reformuler ?"

    # ============================================
    # UTILITIES
    # ============================================

    def _check_session_complete(self, session: dict) -> bool:
        """Vérifie si la session doit se terminer."""
        conversation = session["conversation"]
        user_messages = [m for m in conversation if m["role"] == "user"]

        # Limite de messages
        if len(user_messages) >= 12:
            return True

        # Détection de fin de conversation
        if conversation:
            last = conversation[-1].get("content", "").lower()
            endings = [
                "d'accord, on signe",
                "envoyez-moi le contrat",
                "je prends",
                "marché conclu",
                "pas intéressé",
                "non merci, au revoir",
                "je ne suis pas convaincu",
                "je vais réfléchir",  # Peut indiquer une fin
            ]
            if any(end in last for end in endings):
                return True

        return False

    def _get_playbook_for_frontend(self, playbook: Playbook) -> dict:
        """Prépare les données du playbook pour le frontend."""
        return {
            "id": playbook.id,
            "product": {
                "name": playbook.product.name,
                "company": playbook.company.name,
            },
            "pitch": {
                "hook_30s": playbook.pitch.hook_30s,
                "discovery_questions": playbook.pitch.discovery_questions,
                "key_phrases": playbook.pitch.key_phrases,
            },
            "objections": [
                {
                    "type": obj.type,
                    "label": obj.label,
                    "response": obj.response,
                    "proof": obj.proof,
                }
                for obj in playbook.objections
            ],
            "proofs": {
                "global_stats": playbook.proofs.global_stats if playbook.proofs else {},
                "testimonials": playbook.proofs.testimonials if playbook.proofs else [],
            },
            "benefits": playbook.product.benefits.categories if playbook.product.benefits else {},
        }

    # ============================================
    # LEGACY CONVENIENCE METHODS (pour compatibilité API)
    # ============================================

    async def start_session(self, scenario: dict, patterns: dict) -> dict:
        """
        Méthode legacy pour compatibilité.
        Utilise le nouveau système avec playbook/module par défaut.
        """
        return await self.create_session(
            playbook_id=scenario.get("playbook_id", "automate_ai"),
            module_id=scenario.get("module_id", "bebedc"),
        )

    async def get_prospect_response(
        self,
        user_message: str,
        conversation_history: list,
        system_prompt: str,
    ) -> str:
        """Méthode legacy pour compatibilité."""
        return await self._generate_prospect_response(
            system_prompt=system_prompt,
            conversation=conversation_history,
            user_message=user_message,
        )
