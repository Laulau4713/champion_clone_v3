"""
AudioAnalyzer - Analyse audio et detection d'emotions.

Responsable de:
- Analyse de la prosodie (pitch, tempo, pauses)
- Detection des emotions via le texte et la prosodie
- Generation de feedback sur la confiance
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
import structlog

logger = structlog.get_logger()

# Check for librosa availability
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa_not_available", msg="Install librosa for audio analysis")


@dataclass
class ProsodyAnalysis:
    """Resultats de l'analyse de prosodie."""
    pitch_mean: float = 0.0
    pitch_variation: str = "stable"  # stable, variable, erratic
    tempo: float = 120.0  # words per minute approximation
    pace: str = "normal"  # slow, normal, fast
    pause_count: int = 0
    pause_total_duration: float = 0.0
    volume: str = "normal"  # low, normal, loud
    volume_variation: float = 0.0


@dataclass
class EmotionAnalysis:
    """Resultats de l'analyse d'emotions."""
    confidence: float = 0.7
    hesitation: float = 0.3
    stress: float = 0.3
    enthusiasm: float = 0.5
    indicators: dict = field(default_factory=dict)
    feedback: str = ""


class AudioAnalyzer:
    """
    Analyseur audio pour la detection d'emotions et de prosodie.

    Utilise librosa pour l'analyse audio et des heuristiques
    textuelles pour la detection des hesitations.
    """

    # Mots d'hesitation francais
    HESITATION_WORDS = [
        "euh", "hum", "hmm", "ah", "oh",
        "enfin", "en fait", "voila", "donc",
        "peut-etre", "je pense", "je crois",
        "comment dire", "disons", "bon"
    ]

    # Patterns de repetition
    REPETITION_PATTERN = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)

    def __init__(self):
        logger.info("audio_analyzer_initialized", librosa_available=LIBROSA_AVAILABLE)

    async def analyze_prosody(self, audio_data: bytes, sample_rate: int = 16000) -> ProsodyAnalysis:
        """
        Analyse la prosodie d'un segment audio.

        Args:
            audio_data: Donnees audio en bytes
            sample_rate: Frequence d'echantillonnage

        Returns:
            ProsodyAnalysis avec les metriques de prosodie
        """
        if not LIBROSA_AVAILABLE:
            logger.warning("prosody_analysis_skipped", reason="librosa not available")
            return ProsodyAnalysis()

        try:
            import numpy as np

            # Convert bytes to numpy array
            audio = np.frombuffer(audio_data, dtype=np.float32)

            # Extract pitch (F0)
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sample_rate)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            pitch_mean = np.mean(pitch_values) if pitch_values else 0.0
            pitch_std = np.std(pitch_values) if pitch_values else 0.0

            # Classify pitch variation
            if pitch_std < 20:
                pitch_variation = "stable"
            elif pitch_std < 50:
                pitch_variation = "variable"
            else:
                pitch_variation = "erratic"

            # Tempo estimation (based on onset detection)
            onset_env = librosa.onset.onset_strength(y=audio, sr=sample_rate)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sample_rate)[0]

            # Classify pace
            if tempo < 100:
                pace = "slow"
            elif tempo > 150:
                pace = "fast"
            else:
                pace = "normal"

            # Volume analysis
            rms = librosa.feature.rms(y=audio)[0]
            rms_mean = np.mean(rms)
            rms_std = np.std(rms)

            if rms_mean < 0.02:
                volume = "low"
            elif rms_mean > 0.1:
                volume = "loud"
            else:
                volume = "normal"

            return ProsodyAnalysis(
                pitch_mean=float(pitch_mean),
                pitch_variation=pitch_variation,
                tempo=float(tempo),
                pace=pace,
                pause_count=0,  # Requires silence detection
                pause_total_duration=0.0,
                volume=volume,
                volume_variation=float(rms_std)
            )

        except Exception as e:
            logger.error("prosody_analysis_error", error=str(e))
            return ProsodyAnalysis()

    async def detect_emotions(
        self,
        transcript: str,
        prosody: Optional[ProsodyAnalysis] = None
    ) -> EmotionAnalysis:
        """
        Detecte les emotions a partir du texte et de la prosodie.

        Args:
            transcript: Texte transcrit
            prosody: Analyse de prosodie optionnelle

        Returns:
            EmotionAnalysis avec les emotions detectees
        """
        prosody = prosody or ProsodyAnalysis()
        transcript_lower = transcript.lower()

        # Count hesitation words
        hesitation_count = sum(
            1 for word in self.HESITATION_WORDS
            if word in transcript_lower
        )

        # Count repetitions
        repetitions = len(self.REPETITION_PATTERN.findall(transcript))

        # Calculate word count for normalization
        word_count = len(transcript.split())

        # Calculate hesitation score (normalized)
        hesitation_score = min(1.0, (hesitation_count + repetitions * 2) / max(word_count, 1) * 5)

        # Calculate confidence based on multiple factors
        confidence = 1.0

        # Reduce confidence for hesitations
        confidence -= hesitation_score * 0.4

        # Reduce confidence for slow pace
        if prosody.pace == "slow":
            confidence -= 0.15

        # Reduce confidence for low volume
        if prosody.volume == "low":
            confidence -= 0.15

        # Reduce confidence for erratic pitch
        if prosody.pitch_variation == "erratic":
            confidence -= 0.1

        # Reduce for many pauses
        if prosody.pause_count > 5:
            confidence -= 0.1

        # Clamp confidence between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        # Calculate stress (inverse of some confidence factors)
        stress = 0.3
        if prosody.tempo > 150:
            stress += 0.2
        if prosody.pitch_variation == "erratic":
            stress += 0.2
        stress = min(1.0, stress)

        # Calculate enthusiasm
        enthusiasm = 0.5
        if prosody.tempo > 120:
            enthusiasm += 0.15
        if prosody.volume == "loud":
            enthusiasm += 0.15
        if prosody.pitch_variation == "variable":
            enthusiasm += 0.1
        enthusiasm = min(1.0, enthusiasm)

        # Generate feedback
        feedback = self._generate_feedback(confidence, hesitation_score, prosody)

        indicators = {
            "hesitation_words": hesitation_count,
            "repetitions": repetitions,
            "word_count": word_count
        }

        return EmotionAnalysis(
            confidence=confidence,
            hesitation=hesitation_score,
            stress=stress,
            enthusiasm=enthusiasm,
            indicators=indicators,
            feedback=feedback
        )

    def _generate_feedback(
        self,
        confidence: float,
        hesitation: float,
        prosody: ProsodyAnalysis
    ) -> str:
        """
        Genere un feedback base sur l'analyse.

        Args:
            confidence: Score de confiance
            hesitation: Score d'hesitation
            prosody: Analyse de prosodie

        Returns:
            Feedback textuel
        """
        feedbacks = []

        if confidence >= 0.8:
            feedbacks.append("Bonne confiance dans votre voix, continuez ainsi!")
        elif confidence >= 0.6:
            feedbacks.append("Votre ton est correct, essayez d'etre plus affirmatif.")
        else:
            feedbacks.append("Travaillez votre assurance, evitez les hesitations.")

        if hesitation > 0.5:
            feedbacks.append("Reduisez les mots de remplissage (euh, donc, voila).")

        if prosody.pace == "slow":
            feedbacks.append("Accelerez legerement votre debit.")
        elif prosody.pace == "fast":
            feedbacks.append("Ralentissez un peu pour plus de clarte.")

        if prosody.volume == "low":
            feedbacks.append("Parlez plus fort pour projeter de l'assurance.")

        return " ".join(feedbacks)

    def count_hesitations(self, transcript: str) -> int:
        """
        Compte le nombre de mots d'hesitation dans le texte.

        Args:
            transcript: Texte a analyser

        Returns:
            Nombre d'hesitations
        """
        transcript_lower = transcript.lower()
        return sum(1 for word in self.HESITATION_WORDS if word in transcript_lower)
