"""Tests pour InterruptionService."""
import pytest
from services.interruption_service import InterruptionService, InterruptionDecision


class TestInterruptionService:
    """Tests du service d'interruption."""

    # ===================================================================
    # TESTS NIVEAU EASY (pas d'interruption)
    # ===================================================================

    def test_easy_level_never_interrupts(self):
        """Niveau facile ne doit jamais interrompre."""
        service = InterruptionService(level="easy")

        # Meme avec beaucoup de temps de parole
        result = service.should_interrupt(speaking_duration=60.0)
        assert result.should_interrupt is False

        # Meme avec beaucoup d'hesitation
        result = service.should_interrupt(speaking_duration=10.0, hesitation_count=10)
        assert result.should_interrupt is False

    def test_easy_level_config(self):
        """Verifier la config niveau facile."""
        service = InterruptionService(level="easy")
        assert service.config["interruption_probability"] == 0.0
        assert service.config["enabled"] is False

    def test_easy_level_with_factual_error(self):
        """Niveau facile n'interrompt pas meme sur erreur factuelle."""
        service = InterruptionService(level="easy")

        context = {"factual_error": True}
        result = service.should_interrupt(speaking_duration=5.0, context=context)
        assert result.should_interrupt is False

    # ===================================================================
    # TESTS NIVEAU MEDIUM
    # ===================================================================

    def test_medium_level_config(self):
        """Verifier la config niveau moyen."""
        service = InterruptionService(level="medium")
        assert service.config["interruption_probability"] == 0.1
        assert service.config["patience_seconds"] == 20
        assert service.config["enabled"] is True

    def test_medium_interrupts_when_speaking_too_long(self):
        """Niveau moyen interrompt si parle trop longtemps."""
        service = InterruptionService(level="medium")

        # Depasse patience_seconds (20)
        result = service.should_interrupt(speaking_duration=25.0)
        assert result.should_interrupt is True
        assert result.reason == "speaking_too_long"
        assert result.phrase is not None

    def test_medium_no_interrupt_short_speech(self):
        """Niveau moyen n'interrompt pas systematiquement si parole courte."""
        service = InterruptionService(level="medium")

        # Test multiple fois pour tenir compte de la probabilite
        no_interrupt_count = 0
        for _ in range(10):
            result = service.should_interrupt(speaking_duration=5.0, hesitation_count=0)
            if not result.should_interrupt:
                no_interrupt_count += 1

        # Devrait ne pas interrompre la majorite du temps
        assert no_interrupt_count >= 5

    # ===================================================================
    # TESTS NIVEAU EXPERT
    # ===================================================================

    def test_expert_level_config(self):
        """Verifier la config niveau expert."""
        service = InterruptionService(level="expert")
        assert service.config["interruption_probability"] == 0.4
        assert service.config["patience_seconds"] == 8
        assert service.config["hesitation_threshold"] == 3
        assert service.config["enabled"] is True

    def test_expert_interrupts_quickly(self):
        """Niveau expert interrompt rapidement."""
        service = InterruptionService(level="expert")

        # Depasse patience_seconds (8)
        result = service.should_interrupt(speaking_duration=10.0)
        assert result.should_interrupt is True
        assert result.reason == "speaking_too_long"

    def test_expert_interrupts_on_hesitation(self):
        """Niveau expert interrompt sur trop d'hesitation."""
        service = InterruptionService(level="expert")

        # Simuler plusieurs appels pour atteindre la probabilite
        interrupted = False
        for _ in range(20):
            result = service.should_interrupt(
                speaking_duration=5.0,
                hesitation_count=5
            )
            if result.should_interrupt and result.reason == "too_much_hesitation":
                interrupted = True
                break

        # Devrait avoir interrompu au moins une fois sur 20 essais
        assert interrupted is True

    def test_expert_interrupts_on_low_confidence(self):
        """Niveau expert interrompt si confiance faible."""
        service = InterruptionService(level="expert")

        emotions = {"confidence": 0.2}

        interrupted = False
        for _ in range(20):
            result = service.should_interrupt(
                speaking_duration=5.0,
                emotions=emotions
            )
            if result.should_interrupt and result.reason == "low_confidence":
                interrupted = True
                break

        assert interrupted is True

    def test_expert_interrupts_on_factual_error(self):
        """Niveau expert interrompt toujours sur erreur factuelle."""
        service = InterruptionService(level="expert")

        context = {"factual_error": True}

        result = service.should_interrupt(speaking_duration=3.0, context=context)
        assert result.should_interrupt is True
        assert result.reason == "factual_error"
        assert result.interruption_type == "disagreement"

    # ===================================================================
    # TESTS PHRASES D'INTERRUPTION
    # ===================================================================

    def test_get_random_phrase_impatient(self):
        """Recuperer une phrase impatiente."""
        service = InterruptionService(level="expert")
        phrase = service.get_random_phrase("impatient")

        assert phrase is not None
        assert len(phrase) > 0
        assert phrase in service.INTERRUPTION_PHRASES["impatient"]

    def test_get_random_phrase_disagreement(self):
        """Recuperer une phrase de desaccord."""
        service = InterruptionService(level="expert")
        phrase = service.get_random_phrase("disagreement")

        assert phrase in service.INTERRUPTION_PHRASES["disagreement"]

    def test_get_random_phrase_skeptical(self):
        """Recuperer une phrase sceptique."""
        service = InterruptionService(level="expert")
        phrase = service.get_random_phrase("skeptical")

        assert phrase in service.INTERRUPTION_PHRASES["skeptical"]

    def test_get_random_phrase_default(self):
        """Phrase par defaut si type inconnu."""
        service = InterruptionService(level="expert")
        phrase = service.get_random_phrase("unknown_type")

        # Devrait retourner une phrase impatient par defaut
        assert phrase in service.INTERRUPTION_PHRASES["impatient"]

    # ===================================================================
    # TESTS EDGE CASES
    # ===================================================================

    def test_invalid_level_defaults_to_easy(self):
        """Niveau invalide utilise config easy."""
        service = InterruptionService(level="invalid")
        assert service.config["enabled"] is False

    def test_interruption_decision_structure(self):
        """Verifier la structure de InterruptionDecision."""
        service = InterruptionService(level="expert")
        result = service.should_interrupt(speaking_duration=15.0)

        assert hasattr(result, 'should_interrupt')
        assert hasattr(result, 'phrase')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'interruption_type')

    def test_interruption_with_none_emotions(self):
        """Interruption avec emotions None."""
        service = InterruptionService(level="expert")
        # Ne doit pas lever d'exception
        result = service.should_interrupt(speaking_duration=5.0, emotions=None)
        assert isinstance(result, InterruptionDecision)

    def test_interruption_with_none_context(self):
        """Interruption avec context None."""
        service = InterruptionService(level="expert")
        # Ne doit pas lever d'exception
        result = service.should_interrupt(speaking_duration=5.0, context=None)
        assert isinstance(result, InterruptionDecision)

    def test_medium_factual_error_interrupts(self):
        """Niveau medium interrompt sur erreur factuelle."""
        service = InterruptionService(level="medium")
        context = {"factual_error": True}

        result = service.should_interrupt(speaking_duration=3.0, context=context)
        assert result.should_interrupt is True
        assert result.reason == "factual_error"
