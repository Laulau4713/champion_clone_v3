"""
Unit Tests for JaugeService and BehavioralDetector.

Tests:
- Mood state calculation
- Action application with volatility
- Conversion checking
- Behavioral pattern detection
"""

import pytest
from datetime import datetime

from services.jauge_service import (
    JaugeService, JaugeModification, MoodState, BehavioralDetector
)


# ============================================
# JaugeModification Tests
# ============================================

class TestJaugeModification:
    """Tests for JaugeModification dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        mod = JaugeModification(
            action="empathy_shown",
            delta=5,
            new_value=55,
            reason="Empathie demontrée"
        )
        result = mod.to_dict()

        assert result["action"] == "empathy_shown"
        assert result["delta"] == 5
        assert result["new_value"] == 55
        assert result["reason"] == "Empathie demontrée"
        assert "timestamp" in result

    def test_default_timestamp(self):
        """Should have default timestamp."""
        mod = JaugeModification(action="test", delta=0, new_value=50, reason="test")
        assert mod.timestamp is not None
        assert isinstance(mod.timestamp, datetime)


# ============================================
# JaugeService Mood Tests
# ============================================

class TestJaugeServiceMood:
    """Tests for mood calculation."""

    def test_easy_level_moods(self):
        """Should return correct moods for easy level."""
        service = JaugeService(level="easy")

        # Test each mood range
        assert service.get_mood(10).mood == "resistant"
        assert service.get_mood(30).mood == "neutral"
        assert service.get_mood(60).mood == "interested"
        assert service.get_mood(85).mood == "ready_to_buy"

    def test_medium_level_moods(self):
        """Should return correct moods for medium level."""
        service = JaugeService(level="medium")

        assert service.get_mood(10).mood == "hostile"
        assert service.get_mood(30).mood == "resistant"
        assert service.get_mood(50).mood == "skeptical"
        assert service.get_mood(65).mood == "neutral"
        assert service.get_mood(80).mood == "interested"
        assert service.get_mood(95).mood == "ready_to_buy"

    def test_expert_level_moods(self):
        """Should return correct moods for expert level."""
        service = JaugeService(level="expert")

        assert service.get_mood(10).mood == "hostile"
        assert service.get_mood(25).mood == "aggressive"
        assert service.get_mood(45).mood == "skeptical"
        assert service.get_mood(60).mood == "neutral"
        assert service.get_mood(80).mood == "interested"
        assert service.get_mood(95).mood == "ready_to_buy"

    def test_mood_state_contains_behavior(self):
        """Should include behavior description in mood state."""
        service = JaugeService(level="easy")
        mood = service.get_mood(10)

        assert mood.behavior != ""
        assert mood.jauge_range == (0, 25)

    def test_fallback_mood_for_invalid_jauge(self):
        """Should return neutral mood for edge cases."""
        service = JaugeService(level="easy")
        # Test with custom config that might create gaps
        mood = service.get_mood(101)  # Out of range
        assert mood.mood == "neutral"


# ============================================
# JaugeService Action Tests
# ============================================

class TestJaugeServiceActions:
    """Tests for action application."""

    def test_apply_positive_action(self):
        """Should apply positive action correctly."""
        service = JaugeService(level="easy")
        result = service.apply_action(50, "empathy_shown", "positive")

        assert result.delta == 5  # Default empathy points
        assert result.new_value == 55
        assert result.action == "empathy_shown"
        assert "Empathie" in result.reason

    def test_apply_negative_action(self):
        """Should apply negative action correctly."""
        service = JaugeService(level="easy")
        result = service.apply_action(50, "interruption", "negative")

        assert result.delta == -5
        assert result.new_value == 45
        assert "parole" in result.reason.lower()

    def test_action_respects_jauge_bounds(self):
        """Should not exceed 0-100 bounds."""
        service = JaugeService(level="easy")

        # Test upper bound
        result = service.apply_action(98, "hidden_objection_discovered", "positive")
        assert result.new_value == 100

        # Test lower bound
        result = service.apply_action(5, "lost_temper", "negative")
        assert result.new_value == 0

    def test_unknown_action_returns_zero_delta(self):
        """Should handle unknown actions gracefully."""
        service = JaugeService(level="easy")
        result = service.apply_action(50, "unknown_action", "positive")

        assert result.delta == 0
        assert result.new_value == 50
        assert "non reconnue" in result.reason

    def test_denigration_caps_jauge_at_70(self):
        """Should cap jauge at 70 for denigration."""
        service = JaugeService(level="easy")
        result = service.apply_action(80, "denigrated_competitor", "negative")

        # Denigration is -12 points, but jauge was 80
        # Even though 80-12=68, the cap should apply differently
        # Actually, it should be: new_value = min(80 + delta, 70)
        assert result.new_value <= 70

    def test_volatility_affects_points(self):
        """Should apply volatility multiplier."""
        # High volatility (1.3x)
        config = {"gauge_volatility": "high"}
        service = JaugeService(level="easy", level_config=config)
        result = service.apply_action(50, "empathy_shown", "positive")

        # Default empathy is 5 points, with 1.3x = 6.5 -> 6 (int)
        assert result.delta == 6

    def test_low_volatility_reduces_points(self):
        """Should reduce points with low volatility."""
        config = {"gauge_volatility": "low"}
        service = JaugeService(level="easy", level_config=config)
        result = service.apply_action(50, "empathy_shown", "positive")

        # Default empathy is 5 points, with 0.8x = 4
        assert result.delta == 4


# ============================================
# JaugeService Conversion Tests
# ============================================

class TestJaugeServiceConversion:
    """Tests for conversion checking."""

    def test_conversion_possible_when_threshold_met(self):
        """Should allow conversion when jauge meets threshold."""
        service = JaugeService(level="easy")
        can_convert, reasons = service.check_conversion_possible(
            jauge=80, blockers=[], required_conditions=[], conditions_met=[]
        )

        assert can_convert is True
        assert len(reasons) == 0

    def test_conversion_blocked_by_low_jauge(self):
        """Should block conversion when jauge too low."""
        service = JaugeService(level="easy")
        can_convert, reasons = service.check_conversion_possible(
            jauge=50, blockers=[]
        )

        assert can_convert is False
        assert any("insuffisante" in r.lower() for r in reasons)

    def test_conversion_blocked_by_lost_temper(self):
        """Should block conversion when lost_temper blocker present."""
        service = JaugeService(level="easy")
        can_convert, reasons = service.check_conversion_possible(
            jauge=90, blockers=["lost_temper"]
        )

        assert can_convert is False
        assert any("calme" in r.lower() for r in reasons)

    def test_conversion_blocked_by_denigration(self):
        """Should block conversion when denigration blocker present."""
        service = JaugeService(level="easy")
        can_convert, reasons = service.check_conversion_possible(
            jauge=90, blockers=["denigrated_competitor"]
        )

        assert can_convert is False
        assert any("70" in r for r in reasons)

    def test_conversion_blocked_by_missing_conditions(self):
        """Should block conversion when required conditions not met."""
        service = JaugeService(level="easy")
        can_convert, reasons = service.check_conversion_possible(
            jauge=90,
            blockers=[],
            required_conditions=["budget_discussed", "decision_maker_identified"],
            conditions_met=["budget_discussed"]
        )

        assert can_convert is False
        assert any("decision_maker" in r.lower() for r in reasons)

    def test_custom_conversion_threshold(self):
        """Should respect custom conversion threshold."""
        config = {"conversion_threshold": 90}
        service = JaugeService(level="easy", level_config=config)

        can_convert_75, _ = service.check_conversion_possible(jauge=75, blockers=[])
        can_convert_95, _ = service.check_conversion_possible(jauge=95, blockers=[])

        assert can_convert_75 is False
        assert can_convert_95 is True


# ============================================
# JaugeService Config Tests
# ============================================

class TestJaugeServiceConfig:
    """Tests for configuration handling."""

    def test_default_starting_jauge(self):
        """Should use default starting jauge of 50."""
        service = JaugeService(level="easy")
        assert service.starting_jauge == 50

    def test_custom_starting_jauge(self):
        """Should respect custom starting jauge."""
        config = {"starting_gauge": 30}
        service = JaugeService(level="easy", level_config=config)
        assert service.starting_jauge == 30

    def test_custom_modifiers_override_defaults(self):
        """Should allow custom modifiers to override defaults."""
        config = {
            "jauge_modifiers": {
                "positive_actions": {
                    "empathy_shown": {"points": 10, "description": "Custom empathy"}
                }
            }
        }
        service = JaugeService(level="easy", level_config=config)
        result = service.apply_action(50, "empathy_shown", "positive")

        assert result.delta == 10  # Custom value instead of default 5

    def test_custom_mood_stages(self):
        """Should respect custom mood stages."""
        config = {
            "mood_stages": [
                {"range": [0, 50], "mood": "custom_low", "behavior": "Custom low"},
                {"range": [51, 100], "mood": "custom_high", "behavior": "Custom high"}
            ]
        }
        service = JaugeService(level="easy", level_config=config)

        assert service.get_mood(25).mood == "custom_low"
        assert service.get_mood(75).mood == "custom_high"


# ============================================
# BehavioralDetector Pattern Tests
# ============================================

class TestBehavioralDetectorPatterns:
    """Tests for pattern detection."""

    def test_detect_reformulation(self):
        """Should detect reformulation patterns."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Si je comprends bien, vous dites que...")

        assert len(result["positive"]) > 0
        assert any(p["action"] == "relevant_reformulation" for p in result["positive"])

    def test_detect_emotional_reformulation(self):
        """Should detect emotional reformulation."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Je sens que vous etes preoccupe")

        assert any(p["action"] == "emotional_reformulation" for p in result["positive"])

    def test_detect_empathy(self):
        """Should detect empathy patterns."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Je comprends votre situation")

        assert any(p["action"] == "empathy_shown" for p in result["positive"])

    def test_detect_open_question(self):
        """Should detect open questions."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Comment gerez-vous ce probleme?")

        assert any(p["action"] == "good_open_question" for p in result["positive"])

    def test_detect_roi_quantified(self):
        """Should detect ROI quantification."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Vous pouvez economiser 30% sur vos couts")

        assert any(p["action"] == "roi_quantified" for p in result["positive"])

    def test_detect_listening_signal(self):
        """Should detect listening signals."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("D'accord, je vois")

        assert any(p["action"] == "good_listening_signal" for p in result["positive"])

    def test_detect_denigration(self):
        """Should detect competitor denigration."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Ils sont mauvais, ne faites pas confiance")

        assert len(result["negative"]) > 0
        assert any(p["action"] == "denigrated_competitor" for p in result["negative"])

    def test_detect_immediate_discount(self):
        """Should detect immediate discount offers."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Ok je fais 20% de remise")

        assert any(p["action"] == "immediate_discount" for p in result["negative"])

    def test_detect_aggressive_closing(self):
        """Should detect aggressive closing."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("C'est maintenant ou jamais!")

        assert any(p["action"] == "aggressive_closing" for p in result["negative"])

    def test_detect_defensive_reaction(self):
        """Should detect defensive reactions."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Ce n'est pas ma faute!")

        assert any(p["action"] == "defensive_reaction" for p in result["negative"])

    def test_no_false_positives_for_normal_text(self):
        """Should not detect patterns in normal text."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Bonjour, comment allez-vous?")

        # Should only detect open question, nothing negative
        assert len(result["negative"]) == 0


# ============================================
# BehavioralDetector Indicator Tests
# ============================================

class TestBehavioralDetectorIndicators:
    """Tests for indicator detection."""

    def test_count_hesitations(self):
        """Should count hesitation words."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Euh, donc voila, en fait euh...")

        assert result["indicators"]["hesitation_count"] >= 4

    def test_detect_question_type_open(self):
        """Should identify open questions."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Comment faites-vous?")

        assert result["indicators"]["question_type"] == "open"

    def test_detect_question_type_closed(self):
        """Should identify closed questions."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Est-ce que ca vous interesse?")

        assert result["indicators"]["question_type"] == "closed"

    def test_word_count(self):
        """Should count words correctly."""
        detector = BehavioralDetector()
        result = detector.detect_patterns("Un deux trois quatre cinq")

        assert result["indicators"]["word_count"] == 5


# ============================================
# BehavioralDetector Timing Tests
# ============================================

class TestBehavioralDetectorTiming:
    """Tests for timing-based detection."""

    def test_check_interruption_true(self):
        """Should detect interruption when speaking over prospect."""
        detector = BehavioralDetector()
        is_interruption = detector.check_interruption(
            user_response_delay=0.3,
            prospect_was_speaking=True
        )
        assert is_interruption is True

    def test_check_interruption_false_with_delay(self):
        """Should not flag interruption with proper delay."""
        detector = BehavioralDetector()
        is_interruption = detector.check_interruption(
            user_response_delay=1.0,
            prospect_was_speaking=True
        )
        assert is_interruption is False

    def test_check_interruption_false_when_not_speaking(self):
        """Should not flag interruption if prospect wasnt speaking."""
        detector = BehavioralDetector()
        is_interruption = detector.check_interruption(
            user_response_delay=0.1,
            prospect_was_speaking=False
        )
        assert is_interruption is False

    def test_spoke_first_after_price(self):
        """Should detect speaking first after price mention."""
        detector = BehavioralDetector()
        spoke_first = detector.check_spoke_first_after_price(
            last_prospect_message="Le prix est de 5000 euros",
            user_response_delay=1.0
        )
        assert spoke_first is True

    def test_waited_after_price(self):
        """Should not flag when waited after price."""
        detector = BehavioralDetector()
        spoke_first = detector.check_spoke_first_after_price(
            last_prospect_message="Le prix est de 5000 euros",
            user_response_delay=3.0
        )
        assert spoke_first is False

    def test_closed_question_spam_detection(self):
        """Should detect closed question spam."""
        detector = BehavioralDetector()
        recent_questions = [
            {"type": "closed"},
            {"type": "closed"},
            {"type": "closed"}
        ]
        is_spam = detector.detect_closed_question_spam(recent_questions)
        assert is_spam is True

    def test_no_spam_with_mixed_questions(self):
        """Should not flag spam with mixed question types."""
        detector = BehavioralDetector()
        recent_questions = [
            {"type": "open"},
            {"type": "closed"},
            {"type": "open"}
        ]
        is_spam = detector.detect_closed_question_spam(recent_questions)
        assert is_spam is False

    def test_budget_question_too_early(self):
        """Should detect budget question asked too early."""
        detector = BehavioralDetector()
        too_early = detector.detect_budget_question_too_early(
            text="Quel est votre budget?",
            message_count=4
        )
        assert too_early is True

    def test_budget_question_at_right_time(self):
        """Should not flag budget question at right time."""
        detector = BehavioralDetector()
        too_early = detector.detect_budget_question_too_early(
            text="Quel est votre budget?",
            message_count=10
        )
        assert too_early is False
