"""
Voice Effects Service - Phase 7

Handles:
- Parsing voice annotations like (soupir), (agacée), (rire)
- Mapping emotions to TTS parameters (ElevenLabs stability/similarity)
- Audio assembly (sound effects + TTS)
- Voice configuration for realistic prospect behavior
"""

import io
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class VoiceAnnotation:
    """Parsed voice annotation from text."""

    type: str  # "sound", "emotion", "action"
    value: str  # "sigh", "annoyed", "takes_notes"
    original: str  # "(soupir)"
    position: int  # Position in original text


@dataclass
class TTSSettings:
    """ElevenLabs TTS settings for an emotion."""

    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0  # 0-1, expressiveness
    use_speaker_boost: bool = True


@dataclass
class EmotionalState:
    """Current emotional state affecting voice."""

    mood: str = "neutral"
    gauge: int = 50
    tts_settings: TTSSettings = field(default_factory=TTSSettings)
    sound_before: str | None = None
    sound_after: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# VOICE ANNOTATION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

# Sound effects - trigger audio files
SOUND_PATTERNS = {
    # Sighs
    r"\(soupir\)": {"type": "sound", "category": "sighs", "file": "sigh_light"},
    r"\(soupir lourd\)": {"type": "sound", "category": "sighs", "file": "sigh_heavy"},
    r"\(soupir agacé\)": {"type": "sound", "category": "sighs", "file": "sigh_annoyed"},
    r"\(gros soupir\)": {"type": "sound", "category": "sighs", "file": "sigh_heavy"},
    # Reactions
    r"\(hmm\)": {"type": "sound", "category": "reactions", "file": "hmm_thinking"},
    r"\(hmm\.\.\.?\)": {"type": "sound", "category": "reactions", "file": "hmm_doubtful"},
    r"\(rire\)": {"type": "sound", "category": "reactions", "file": "laugh_polite"},
    r"\(rire poli\)": {"type": "sound", "category": "reactions", "file": "laugh_polite"},
    r"\(petit rire\)": {"type": "sound", "category": "reactions", "file": "laugh_polite"},
    r"\(rire sincère\)": {"type": "sound", "category": "reactions", "file": "laugh_genuine"},
    r"\(raclement de gorge\)": {"type": "sound", "category": "reactions", "file": "throat_clear"},
    r"\(se racle la gorge\)": {"type": "sound", "category": "reactions", "file": "throat_clear"},
    r"\(tousse\)": {"type": "sound", "category": "reactions", "file": "throat_clear"},
    # Interruptions
    r"\(interrompt\)": {"type": "sound", "category": "interruptions", "file": "wait_wait"},
    r"\(coupe la parole\)": {"type": "sound", "category": "interruptions", "file": "wait_wait"},
    # Ambiance
    r"\(téléphone sonne\)": {"type": "sound", "category": "ambiance", "file": "phone_ring_distant"},
    r"\(notification\)": {"type": "sound", "category": "ambiance", "file": "phone_notification"},
    r"\(tape au clavier\)": {"type": "sound", "category": "ambiance", "file": "keyboard_typing"},
    r"\(bruits de clavier\)": {"type": "sound", "category": "ambiance", "file": "keyboard_typing"},
}

# Emotion annotations - affect TTS parameters
EMOTION_PATTERNS = {
    # Negative emotions
    r"\(agacé[e]?\)": "annoyed",
    r"\(irrité[e]?\)": "annoyed",
    r"\(énervé[e]?\)": "angry",
    r"\(en colère\)": "angry",
    r"\(froid[e]?\)": "cold",
    r"\(glacial[e]?\)": "cold",
    r"\(sec\)": "cold",
    r"\(sèche\)": "cold",
    r"\(méfiant[e]?\)": "skeptical",
    r"\(sceptique\)": "skeptical",
    r"\(dubitatif\)": "skeptical",
    r"\(dubitative\)": "skeptical",
    r"\(impatient[e]?\)": "impatient",
    r"\(pressé[e]?\)": "impatient",
    r"\(ennuyé[e]?\)": "bored",
    r"\(las\)": "bored",
    r"\(lasse\)": "bored",
    # Neutral
    r"\(neutre\)": "neutral",
    r"\(professionnel[le]?\)": "neutral",
    # Positive emotions
    r"\(intéressé[e]?\)": "interested",
    r"\(curieux\)": "interested",
    r"\(curieuse\)": "interested",
    r"\(amusé[e]?\)": "amused",
    r"\(souriant[e]?\)": "friendly",
    r"\(chaleureux\)": "friendly",
    r"\(chaleureuse\)": "friendly",
    r"\(enthousiaste\)": "enthusiastic",
    r"\(ravi[e]?\)": "enthusiastic",
    r"\(conquis[e]?\)": "enthusiastic",
}

# Action annotations - visual feedback only (not audio)
ACTION_PATTERNS = {
    r"\(prend des notes\)": "takes_notes",
    r"\(note quelque chose\)": "takes_notes",
    r"\(hoche la tête\)": "nods",
    r"\(acquiesce\)": "nods",
    r"\(fronce les sourcils\)": "frowns",
    r"\(lève les yeux au ciel\)": "eye_roll",
    r"\(regarde sa montre\)": "checks_watch",
    r"\(consulte son téléphone\)": "checks_phone",
    r"\(se penche en avant\)": "leans_forward",
    r"\(croise les bras\)": "crosses_arms",
    r"\(sourire\)": "smiles",
    r"\(sourit\)": "smiles",
}


# ═══════════════════════════════════════════════════════════════════════════
# EMOTION → TTS SETTINGS MAPPING
# ═══════════════════════════════════════════════════════════════════════════

EMOTION_TTS_SETTINGS: dict[str, TTSSettings] = {
    # Negative emotions - lower stability = more variation
    "angry": TTSSettings(stability=0.3, similarity_boost=0.8, style=0.7),
    "annoyed": TTSSettings(stability=0.4, similarity_boost=0.75, style=0.5),
    "cold": TTSSettings(stability=0.7, similarity_boost=0.6, style=0.3),
    "skeptical": TTSSettings(stability=0.5, similarity_boost=0.7, style=0.4),
    "impatient": TTSSettings(stability=0.35, similarity_boost=0.75, style=0.6),
    "bored": TTSSettings(stability=0.6, similarity_boost=0.65, style=0.2),
    # Neutral
    "neutral": TTSSettings(stability=0.5, similarity_boost=0.75, style=0.0),
    # Positive emotions - higher similarity = more natural
    "interested": TTSSettings(stability=0.45, similarity_boost=0.8, style=0.4),
    "amused": TTSSettings(stability=0.4, similarity_boost=0.85, style=0.5),
    "friendly": TTSSettings(stability=0.5, similarity_boost=0.85, style=0.4),
    "enthusiastic": TTSSettings(stability=0.35, similarity_boost=0.9, style=0.7),
}

# Mood (from gauge) → default emotion
MOOD_TO_EMOTION: dict[str, str] = {
    "hostile": "angry",
    "skeptical": "skeptical",
    "neutral": "neutral",
    "interested": "interested",
    "ready_to_buy": "enthusiastic",
}

# Mood → sounds to potentially play
MOOD_SOUNDS: dict[str, dict[str, Any]] = {
    "hostile": {
        "before_response": ["sigh_annoyed", "sigh_heavy"],
        "probability": 0.4,
    },
    "skeptical": {
        "before_response": ["hmm_doubtful", "sigh_light"],
        "probability": 0.3,
    },
    "neutral": {
        "before_response": [],
        "probability": 0.0,
    },
    "interested": {
        "before_response": ["hmm_thinking"],
        "probability": 0.1,
    },
    "ready_to_buy": {
        "before_response": [],
        "probability": 0.0,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# VOICE EFFECTS SERVICE
# ═══════════════════════════════════════════════════════════════════════════


class VoiceEffectsService:
    """
    Service for handling voice effects and annotations.

    Features:
    - Parse voice annotations from text
    - Clean text for TTS (remove annotations)
    - Get TTS settings based on emotion/mood
    - Get sound files to play before/after TTS
    - Assemble audio (sounds + TTS)
    """

    AUDIO_BASE_PATH = Path("audio/voice_effects")

    def __init__(self):
        self.audio_path = self.AUDIO_BASE_PATH
        # Compile regex patterns for performance
        self._sound_patterns = [(re.compile(p, re.IGNORECASE), v) for p, v in SOUND_PATTERNS.items()]
        self._emotion_patterns = [(re.compile(p, re.IGNORECASE), v) for p, v in EMOTION_PATTERNS.items()]
        self._action_patterns = [(re.compile(p, re.IGNORECASE), v) for p, v in ACTION_PATTERNS.items()]

    # ═══════════════════════════════════════════════════════════════════
    # PARSING
    # ═══════════════════════════════════════════════════════════════════

    def parse_annotations(self, text: str) -> list[VoiceAnnotation]:
        """
        Parse all voice annotations from text.

        Args:
            text: Text with annotations like "(soupir) Bon, écoutez..."

        Returns:
            List of VoiceAnnotation objects
        """
        annotations = []

        # Find sound patterns
        for pattern, info in self._sound_patterns:
            for match in pattern.finditer(text):
                annotations.append(
                    VoiceAnnotation(
                        type="sound",
                        value=f"{info['category']}/{info['file']}",
                        original=match.group(),
                        position=match.start(),
                    )
                )

        # Find emotion patterns
        for pattern, emotion in self._emotion_patterns:
            for match in pattern.finditer(text):
                annotations.append(
                    VoiceAnnotation(
                        type="emotion",
                        value=emotion,
                        original=match.group(),
                        position=match.start(),
                    )
                )

        # Find action patterns
        for pattern, action in self._action_patterns:
            for match in pattern.finditer(text):
                annotations.append(
                    VoiceAnnotation(
                        type="action",
                        value=action,
                        original=match.group(),
                        position=match.start(),
                    )
                )

        # Sort by position
        annotations.sort(key=lambda a: a.position)

        return annotations

    def clean_text_for_tts(self, text: str) -> str:
        """
        Remove all annotations from text for TTS.

        Args:
            text: Text with annotations

        Returns:
            Clean text without annotations
        """
        # Remove all parenthetical annotations
        # Pattern: (anything) at word boundaries
        cleaned = re.sub(r"\([^)]+\)\s*", "", text)

        # Clean up extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def extract_primary_emotion(self, text: str) -> str | None:
        """
        Extract the primary emotion from text annotations.

        Returns the first emotion found, or None.
        """
        for pattern, emotion in self._emotion_patterns:
            if pattern.search(text):
                return emotion
        return None

    def extract_sounds(self, text: str) -> list[dict[str, str]]:
        """
        Extract all sounds to play from text annotations.

        Returns list of {category, file} dicts.
        """
        sounds = []
        for pattern, info in self._sound_patterns:
            if pattern.search(text):
                sounds.append({"category": info["category"], "file": info["file"]})
        return sounds

    def extract_actions(self, text: str) -> list[str]:
        """
        Extract all visual actions from text annotations.

        Returns list of action names (for frontend visual feedback).
        """
        actions = []
        for pattern, action in self._action_patterns:
            if pattern.search(text):
                actions.append(action)
        return actions

    # ═══════════════════════════════════════════════════════════════════
    # TTS SETTINGS
    # ═══════════════════════════════════════════════════════════════════

    def get_tts_settings(
        self,
        mood: str = "neutral",
        emotion_override: str | None = None,
        gauge: int = 50,
    ) -> TTSSettings:
        """
        Get TTS settings based on mood and optional emotion override.

        Args:
            mood: Current mood (hostile, skeptical, neutral, interested, ready_to_buy)
            emotion_override: Specific emotion from annotation
            gauge: Current emotional gauge (0-100)

        Returns:
            TTSSettings with stability, similarity_boost, style
        """
        # Use emotion override if provided
        if emotion_override and emotion_override in EMOTION_TTS_SETTINGS:
            return EMOTION_TTS_SETTINGS[emotion_override]

        # Map mood to emotion
        emotion = MOOD_TO_EMOTION.get(mood, "neutral")

        # Adjust based on gauge extremes
        settings = EMOTION_TTS_SETTINGS.get(emotion, EMOTION_TTS_SETTINGS["neutral"])

        # Clone settings to avoid mutating
        adjusted = TTSSettings(
            stability=settings.stability,
            similarity_boost=settings.similarity_boost,
            style=settings.style,
            use_speaker_boost=settings.use_speaker_boost,
        )

        # Extreme gauge adjustments
        if gauge < 20:
            adjusted.stability = max(0.2, adjusted.stability - 0.15)
            adjusted.style = min(1.0, adjusted.style + 0.2)
        elif gauge > 80:
            adjusted.similarity_boost = min(1.0, adjusted.similarity_boost + 0.1)

        return adjusted

    # ═══════════════════════════════════════════════════════════════════
    # SOUND FILES
    # ═══════════════════════════════════════════════════════════════════

    def get_sound_path(self, category: str, file: str) -> Path | None:
        """
        Get path to a sound file.

        Args:
            category: Sound category (sighs, reactions, etc.)
            file: File name without extension

        Returns:
            Path to MP3 file, or None if not found
        """
        path = self.audio_path / category / f"{file}.mp3"
        if path.exists():
            return path

        logger.warning("sound_file_not_found", category=category, file=file)
        return None

    def get_mood_sounds(self, mood: str) -> list[str]:
        """
        Get potential sounds to play for a mood.

        Returns list of sound paths (category/file format).
        """
        config = MOOD_SOUNDS.get(mood, {})
        sounds = config.get("before_response", [])
        probability = config.get("probability", 0.0)

        if sounds and random.random() < probability:
            # Pick one random sound
            sound = random.choice(sounds)
            # Determine category from sound name
            if "sigh" in sound:
                return [f"sighs/{sound}"]
            elif "hmm" in sound or "laugh" in sound or "throat" in sound:
                return [f"reactions/{sound}"]

        return []

    def should_add_verbal_tic(self, mood: str, gauge: int) -> str | None:
        """
        Determine if a verbal tic should be added.

        Returns the tic text to prepend, or None.
        """
        if mood in ("skeptical", "hostile") and gauge < 40:
            tics = ["Mouais... ", "Pfff... ", "Bof... ", "Hmm... "]
            if random.random() < 0.3:
                return random.choice(tics)

        elif mood == "neutral" and random.random() < 0.1:
            tics = ["Euh... ", "Donc... ", "Bon... "]
            return random.choice(tics)

        return None

    # ═══════════════════════════════════════════════════════════════════
    # AUDIO ASSEMBLY
    # ═══════════════════════════════════════════════════════════════════

    def prepare_tts_response(
        self,
        text: str,
        mood: str = "neutral",
        gauge: int = 50,
    ) -> dict[str, Any]:
        """
        Prepare everything needed for a TTS response.

        This is the main method to call before generating TTS.

        Args:
            text: Response text with annotations
            mood: Current mood
            gauge: Current gauge

        Returns:
            {
                "clean_text": str,  # Text for TTS
                "tts_settings": TTSSettings,  # ElevenLabs params
                "sounds_before": list[str],  # Sound file paths to play before
                "sounds_after": list[str],  # Sound file paths to play after
                "actions": list[str],  # Visual actions for frontend
                "emotion": str | None,  # Detected emotion
                "verbal_tic": str | None,  # Verbal tic to prepend
            }
        """
        # Parse annotations
        annotations = self.parse_annotations(text)

        # Extract emotion from annotations
        emotion = self.extract_primary_emotion(text)

        # Extract explicit sounds
        explicit_sounds = self.extract_sounds(text)
        sounds_before = [f"{s['category']}/{s['file']}" for s in explicit_sounds]

        # Add mood-based sounds
        mood_sounds = self.get_mood_sounds(mood)
        sounds_before = mood_sounds + sounds_before  # Mood sounds first

        # Extract actions
        actions = self.extract_actions(text)

        # Clean text
        clean_text = self.clean_text_for_tts(text)

        # Get TTS settings
        tts_settings = self.get_tts_settings(mood=mood, emotion_override=emotion, gauge=gauge)

        # Check for verbal tic
        verbal_tic = self.should_add_verbal_tic(mood, gauge)
        if verbal_tic:
            clean_text = verbal_tic + clean_text

        logger.info(
            "tts_response_prepared",
            mood=mood,
            gauge=gauge,
            emotion=emotion,
            sounds_count=len(sounds_before),
            actions_count=len(actions),
            text_length=len(clean_text),
        )

        return {
            "clean_text": clean_text,
            "tts_settings": tts_settings,
            "sounds_before": sounds_before,
            "sounds_after": [],
            "actions": actions,
            "emotion": emotion,
            "verbal_tic": verbal_tic,
        }

    async def read_sound_file(self, sound_path: str) -> bytes | None:
        """
        Read a sound file as bytes.

        Args:
            sound_path: Path like "sighs/sigh_light"

        Returns:
            Audio bytes or None if not found
        """
        parts = sound_path.split("/")
        if len(parts) != 2:
            return None

        full_path = self.get_sound_path(parts[0], parts[1])
        if full_path and full_path.exists():
            return full_path.read_bytes()
        return None

    def list_available_sounds(self) -> dict[str, list[str]]:
        """List all available sound files by category."""
        result = {}
        for category in ["sighs", "reactions", "interruptions", "ambiance"]:
            category_path = self.audio_path / category
            if category_path.exists():
                files = [f.stem for f in category_path.glob("*.mp3")]
                result[category] = files
            else:
                result[category] = []
        return result


# ═══════════════════════════════════════════════════════════════════════════
# VOICE CONFIG FOR TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════


def get_default_voice_config() -> dict[str, Any]:
    """
    Get default voice configuration for scenario templates.

    This is the structure used in Phase 7 for advanced voice control.
    """
    return {
        "prospect_voice_profile": {
            "gender": "female",
            "age_range": "35-45",
            "accent": "parisien",
            "base_tone": "professional",
            "speaking_pace": "medium",
        },
        "emotional_voice_mapping": {
            "hostile": {
                "tts_stability": 0.3,
                "tts_similarity": 0.8,
                "tts_style": 0.7,
                "sounds_probability": 0.4,
                "sounds_pool": ["sigh_annoyed", "sigh_heavy"],
            },
            "skeptical": {
                "tts_stability": 0.5,
                "tts_similarity": 0.7,
                "tts_style": 0.4,
                "sounds_probability": 0.3,
                "sounds_pool": ["hmm_doubtful", "sigh_light"],
            },
            "neutral": {
                "tts_stability": 0.5,
                "tts_similarity": 0.75,
                "tts_style": 0.0,
                "sounds_probability": 0.0,
                "sounds_pool": [],
            },
            "interested": {
                "tts_stability": 0.45,
                "tts_similarity": 0.8,
                "tts_style": 0.4,
                "sounds_probability": 0.1,
                "sounds_pool": ["hmm_thinking"],
            },
            "ready_to_buy": {
                "tts_stability": 0.35,
                "tts_similarity": 0.9,
                "tts_style": 0.7,
                "sounds_probability": 0.0,
                "sounds_pool": [],
            },
        },
        "verbal_tics": {
            "fillers": ["euh", "donc", "voilà", "bon"],
            "thinking_sounds": ["hmm", "ah"],
            "agreement_sounds": ["mm-hmm", "d'accord", "ok"],
            "doubt_sounds": ["mouais", "bof", "pfff"],
        },
        "interruption_settings": {
            "gauge_threshold": 30,
            "probability": 0.7,
            "phrases": [
                "Attendez, attendez...",
                "Oui mais...",
                "Non mais écoutez...",
                "Je vous arrête tout de suite",
            ],
        },
        "response_timing": {
            "natural_delay_ms": [800, 2000],
            "thinking_delay_ms": [2000, 4000],
            "max_user_speech_seconds": 45,
        },
    }


# Global instance
voice_effects_service = VoiceEffectsService()
