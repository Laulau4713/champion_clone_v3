"""
AI Tasks - Celery tasks for Claude API calls
=============================================

These tasks handle heavy AI operations asynchronously:
- Pattern analysis
- Training responses
- Session evaluation

Rate limited to prevent API quota exhaustion.
"""

import os

import structlog
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

logger = structlog.get_logger()

# =============================================================================
# CLAUDE API CALL (Base task)
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,
    max_retries=3,
    rate_limit="30/m",
)
def call_claude_api(
    self, messages: list, model: str = "claude-sonnet-4-20250514", max_tokens: int = 1024, system: str = None
):
    """
    Generic Claude API call with retry logic.

    Args:
        messages: List of message dicts [{"role": "user", "content": "..."}]
        model: Claude model to use
        max_tokens: Maximum response tokens
        system: System prompt (optional)

    Returns:
        dict: {"content": str, "usage": dict, "model": str}
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)

        result = {
            "content": response.content[0].text if response.content else "",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "model": response.model,
            "stop_reason": response.stop_reason,
        }

        logger.info(
            "claude_api_success",
            model=model,
            input_tokens=result["usage"]["input_tokens"],
            output_tokens=result["usage"]["output_tokens"],
        )

        return result

    except anthropic.RateLimitError as e:
        logger.warning("claude_rate_limit", error=str(e))
        # Exponential backoff with jitter
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    except anthropic.APIError as e:
        logger.error("claude_api_error", error=str(e))
        raise

    except MaxRetriesExceededError:
        logger.error("claude_max_retries_exceeded")
        raise


# =============================================================================
# PATTERN ANALYSIS
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    rate_limit="10/m",
)
def analyze_patterns_async(self, transcript: str, champion_id: int):
    """
    Analyze sales patterns from transcript asynchronously.

    Args:
        transcript: Full call transcript
        champion_id: Champion ID to associate patterns with

    Returns:
        dict: Extracted patterns (openings, objections, closes, etc.)
    """
    system_prompt = """Tu es un expert en analyse de techniques de vente.
    Analyse le transcript suivant et extrait les patterns de vente.

    Retourne un JSON avec:
    - openings: phrases d'accroche
    - objections: objections client et réponses
    - closes: techniques de closing
    - key_phrases: phrases clés mémorables
    - tone_style: style de communication
    - success_patterns: ce qui fonctionne bien
    """

    messages = [{"role": "user", "content": f"Transcript:\n\n{transcript}"}]

    result = call_claude_api.apply(
        args=[messages],
        kwargs={
            "model": "claude-opus-4-20250514",  # Use Opus for quality
            "max_tokens": 2048,
            "system": system_prompt,
        },
    ).get()

    logger.info("patterns_analyzed", champion_id=champion_id)

    return {
        "champion_id": champion_id,
        "patterns": result["content"],
        "usage": result["usage"],
    }


# =============================================================================
# TRAINING RESPONSE GENERATION
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    rate_limit="60/m",
)
def generate_training_response_async(
    self,
    session_id: int,
    user_message: str,
    conversation_history: list,
    scenario: dict,
    patterns: dict,
):
    """
    Generate prospect response for training session.

    Args:
        session_id: Training session ID
        user_message: User's sales attempt
        conversation_history: Previous messages
        scenario: Current scenario details
        patterns: Champion's patterns to mimic

    Returns:
        dict: {"response": str, "feedback": str, "score": int}
    """
    system_prompt = f"""Tu es un prospect dans un scénario de vente.

    Scénario: {scenario.get("description", "")}
    Profil client: {scenario.get("client_profile", "")}
    Objections possibles: {scenario.get("objections", [])}

    Patterns du champion à tester: {patterns}

    Réponds naturellement comme un prospect. Sois réaliste.
    Si le commercial utilise une bonne technique, montre de l'intérêt.
    Si la technique est mauvaise, résiste ou objecte.

    Après ta réponse, évalue brièvement la performance (1 phrase).
    """

    # Build conversation
    messages = conversation_history + [{"role": "user", "content": user_message}]

    result = call_claude_api.apply(
        args=[messages],
        kwargs={
            "model": "claude-sonnet-4-20250514",  # Sonnet for speed
            "max_tokens": 512,
            "system": system_prompt,
        },
    ).get()

    logger.info("training_response_generated", session_id=session_id)

    return {
        "session_id": session_id,
        "response": result["content"],
        "usage": result["usage"],
    }


# =============================================================================
# SESSION EVALUATION
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    rate_limit="20/m",
)
def evaluate_session_async(self, session_id: int, conversation: list, scenario: dict):
    """
    Evaluate complete training session.

    Args:
        session_id: Training session ID
        conversation: Full conversation history
        scenario: Scenario details

    Returns:
        dict: Detailed evaluation with scores and feedback
    """
    system_prompt = """Tu es un coach commercial expert.
    Évalue cette session d'entraînement et fournis:

    1. Score global (0-100)
    2. Points forts (3 max)
    3. Points d'amélioration (3 max)
    4. Techniques utilisées correctement
    5. Techniques manquées
    6. Conseil principal

    Sois constructif et spécifique.
    """

    conversation_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in conversation])

    messages = [{"role": "user", "content": f"Scénario: {scenario}\n\nConversation:\n{conversation_text}"}]

    result = call_claude_api.apply(
        args=[messages],
        kwargs={
            "model": "claude-opus-4-20250514",  # Opus for quality evaluation
            "max_tokens": 1024,
            "system": system_prompt,
        },
    ).get()

    logger.info("session_evaluated", session_id=session_id)

    return {
        "session_id": session_id,
        "evaluation": result["content"],
        "usage": result["usage"],
    }
