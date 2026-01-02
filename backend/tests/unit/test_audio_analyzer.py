"""Tests pour AudioAnalyzer."""

import pytest

# Import the service
from services.audio_analyzer import LIBROSA_AVAILABLE, AudioAnalyzer, EmotionAnalysis, ProsodyAnalysis


class TestAudioAnalyzer:
    """Tests de l'analyseur audio."""

    @pytest.fixture
    def analyzer(self):
        return AudioAnalyzer()

    @pytest.fixture
    def default_prosody(self):
        """Prosodie par defaut."""
        return ProsodyAnalysis(
            pitch_mean=200.0,
            pitch_variation="stable",
            tempo=120.0,
            pace="normal",
            pause_count=2,
            pause_total_duration=0.5,
            volume="normal",
            volume_variation=0.01,
        )

    # ===================================================================
    # TESTS DETECTION EMOTIONS TEXTUELLES
    # ===================================================================

    @pytest.mark.asyncio
    async def test_detect_emotions_confident(self, analyzer, default_prosody):
        """Detecter emotions d'un texte confiant."""
        transcript = "Oui absolument, notre solution repond parfaitement a ce besoin."

        emotions = await analyzer.detect_emotions(transcript, default_prosody)

        assert emotions.confidence > 0.7
        assert emotions.hesitation < 0.3
        assert emotions.indicators["hesitation_words"] == 0

    @pytest.mark.asyncio
    async def test_detect_emotions_hesitant(self, analyzer):
        """Detecter emotions d'un texte hesitant."""
        prosody = ProsodyAnalysis(
            pitch_mean=180.0,
            pitch_variation="variable",
            tempo=80.0,
            pace="slow",
            pause_count=5,
            pause_total_duration=2.0,
            volume="low",
            volume_variation=0.02,
        )

        transcript = "Euh... donc en fait... peut-etre que... voila, je pense que..."

        emotions = await analyzer.detect_emotions(transcript, prosody)

        assert emotions.confidence < 0.6
        assert emotions.hesitation > 0.3
        assert emotions.indicators["hesitation_words"] >= 4

    @pytest.mark.asyncio
    async def test_detect_emotions_with_repetitions(self, analyzer, default_prosody):
        """Detecter les repetitions."""
        transcript = "On peut peut faire ca, oui oui."

        emotions = await analyzer.detect_emotions(transcript, default_prosody)

        assert emotions.indicators["repetitions"] >= 1
        # Les repetitions reduisent la confiance
        assert emotions.confidence < 1.0

    @pytest.mark.asyncio
    async def test_feedback_generation(self, analyzer):
        """Verifier la generation de feedback."""
        prosody = ProsodyAnalysis(
            pitch_mean=180.0,
            pitch_variation="stable",
            tempo=80.0,
            pace="slow",
            pause_count=2,
            pause_total_duration=1.0,
            volume="low",
            volume_variation=0.01,
        )

        transcript = "Euh... je pense que..."

        emotions = await analyzer.detect_emotions(transcript, prosody)

        assert emotions.feedback is not None
        assert len(emotions.feedback) > 0

    @pytest.mark.asyncio
    async def test_positive_feedback_when_confident(self, analyzer, default_prosody):
        """Feedback positif si confiant."""
        transcript = "Notre solution vous permettra d'atteindre vos objectifs."

        emotions = await analyzer.detect_emotions(transcript, default_prosody)

        assert "continue" in emotions.feedback.lower() or "bonne" in emotions.feedback.lower()

    @pytest.mark.asyncio
    async def test_detect_emotions_without_prosody(self, analyzer):
        """Detection d'emotions sans prosodie."""
        transcript = "Bonjour, je vous appelle pour vous presenter notre solution."

        emotions = await analyzer.detect_emotions(transcript, None)

        assert isinstance(emotions, EmotionAnalysis)
        assert 0 <= emotions.confidence <= 1

    # ===================================================================
    # TESTS HESITATION WORDS
    # ===================================================================

    def test_hesitation_words_list(self, analyzer):
        """Verifier la liste des mots d'hesitation."""
        assert "euh" in analyzer.HESITATION_WORDS
        assert "hum" in analyzer.HESITATION_WORDS
        assert "enfin" in analyzer.HESITATION_WORDS
        assert "en fait" in analyzer.HESITATION_WORDS
        assert "peut-etre" in analyzer.HESITATION_WORDS

    def test_count_hesitations_basic(self, analyzer):
        """Compter les hesitations dans un texte simple."""
        transcript = "Euh, donc voila, je pense que..."

        count = analyzer.count_hesitations(transcript)
        assert count >= 3  # euh, donc, voila, je pense

    def test_count_hesitations_none(self, analyzer):
        """Pas d'hesitation dans un texte clair."""
        transcript = "Notre solution repond parfaitement a vos besoins."

        count = analyzer.count_hesitations(transcript)
        assert count == 0

    def test_count_hesitations_case_insensitive(self, analyzer):
        """Detection insensible a la casse."""
        transcript = "EUH donc VOILA je pense"

        count = analyzer.count_hesitations(transcript)
        assert count >= 3

    # ===================================================================
    # TESTS PROSODY ANALYSIS (si librosa disponible)
    # ===================================================================

    @pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
    @pytest.mark.asyncio
    async def test_prosody_analysis_with_audio(self, analyzer):
        """Test analyse de prosodie avec audio (si librosa disponible)."""
        import numpy as np

        # Generer un audio de test (ton simple a 440Hz)
        sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)
        audio_bytes = audio.astype(np.float32).tobytes()

        prosody = await analyzer.analyze_prosody(audio_bytes, sr)

        assert isinstance(prosody, ProsodyAnalysis)
        assert prosody.pitch_mean >= 0
        assert prosody.pace in ["slow", "normal", "fast"]
        assert prosody.volume in ["low", "normal", "loud"]

    @pytest.mark.asyncio
    async def test_prosody_analysis_without_librosa(self, analyzer):
        """Prosody analysis retourne defaut si librosa non disponible."""
        if LIBROSA_AVAILABLE:
            pytest.skip("librosa is available")

        prosody = await analyzer.analyze_prosody(b"fake audio data", 16000)
        assert isinstance(prosody, ProsodyAnalysis)
        assert prosody.pitch_mean == 0.0

    # ===================================================================
    # TESTS EDGE CASES
    # ===================================================================

    @pytest.mark.asyncio
    async def test_empty_transcript(self, analyzer, default_prosody):
        """Texte vide."""
        emotions = await analyzer.detect_emotions("", default_prosody)

        assert isinstance(emotions, EmotionAnalysis)
        assert emotions.indicators["word_count"] == 0

    @pytest.mark.asyncio
    async def test_very_long_transcript(self, analyzer, default_prosody):
        """Texte tres long."""
        transcript = " ".join(["Notre solution est excellente."] * 100)

        emotions = await analyzer.detect_emotions(transcript, default_prosody)

        assert isinstance(emotions, EmotionAnalysis)
        assert emotions.confidence >= 0

    @pytest.mark.asyncio
    async def test_stress_calculation(self, analyzer):
        """Calcul du stress."""
        # Prosodie rapide et erratique = stress eleve
        prosody = ProsodyAnalysis(
            tempo=180.0,  # Fast
            pitch_variation="erratic",
        )

        transcript = "Oui oui bien sur, pas de probleme."
        emotions = await analyzer.detect_emotions(transcript, prosody)

        assert emotions.stress > 0.5

    @pytest.mark.asyncio
    async def test_enthusiasm_calculation(self, analyzer):
        """Calcul de l'enthousiasme."""
        # Prosodie dynamique = enthousiasme eleve
        prosody = ProsodyAnalysis(
            tempo=140.0,  # Above normal
            volume="loud",
            pitch_variation="variable",
        )

        transcript = "C'est vraiment fantastique ce que vous proposez!"
        emotions = await analyzer.detect_emotions(transcript, prosody)

        assert emotions.enthusiasm > 0.6
