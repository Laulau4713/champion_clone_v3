"""
Service de voix : TTS (ElevenLabs) + STT (Whisper API)

Gère la synthèse vocale et la reconnaissance vocale pour les sessions
d'entraînement avec voix.
"""

import base64
import hashlib
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import structlog

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class VoiceService:
    """
    Gère la synthèse vocale (TTS) et la reconnaissance vocale (STT).

    TTS: ElevenLabs API
    STT: OpenAI Whisper API
    """

    ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
    OPENAI_BASE_URL = "https://api.openai.com/v1"

    # Mapping personnalité → voix
    VOICE_MAPPING = {
        "friendly": "ELEVENLABS_VOICE_FRIENDLY",
        "curious": "ELEVENLABS_VOICE_FRIENDLY",
        "open": "ELEVENLABS_VOICE_FRIENDLY",
        "neutral": "ELEVENLABS_VOICE_NEUTRAL",
        "skeptical": "ELEVENLABS_VOICE_NEUTRAL",
        "analytical": "ELEVENLABS_VOICE_NEUTRAL",
        "hesitant": "ELEVENLABS_VOICE_NEUTRAL",
        "busy": "ELEVENLABS_VOICE_AGGRESSIVE",
        "aggressive": "ELEVENLABS_VOICE_AGGRESSIVE",
        "impatient": "ELEVENLABS_VOICE_AGGRESSIVE",
        "defensive": "ELEVENLABS_VOICE_AGGRESSIVE",
    }

    def __init__(self):
        self.elevenlabs_key = settings.ELEVENLABS_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.cache_dir = Path("cache/audio")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════
    # TTS - TEXT TO SPEECH (ElevenLabs)
    # ═══════════════════════════════════════════════════════════════

    def _get_voice_id(self, personality: str = "neutral") -> str:
        """Retourne le voice_id selon la personnalité."""
        voice_setting = self.VOICE_MAPPING.get(personality, "ELEVENLABS_VOICE_NEUTRAL")
        voice_id = getattr(settings, voice_setting, "")

        # Fallback to neutral if specific voice not configured
        if not voice_id:
            voice_id = settings.ELEVENLABS_VOICE_NEUTRAL

        # If still no voice, use a default ElevenLabs voice
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - default multilingual voice

        return voice_id

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Génère une clé de cache pour l'audio."""
        content = f"{text}|{voice_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        """Retourne le chemin du fichier cache."""
        return self.cache_dir / f"{cache_key}.mp3"

    async def text_to_speech(
        self,
        text: str,
        personality: str = "neutral",
        use_cache: bool = True,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> tuple[bytes, str]:
        """
        Convertit du texte en audio via ElevenLabs.

        Args:
            text: Texte à convertir
            personality: Personnalité du prospect (détermine la voix)
            use_cache: Utiliser le cache si disponible
            stability: Stabilité de la voix (0-1)
            similarity_boost: Similarité à la voix originale (0-1)

        Returns:
            tuple[bytes, str]: (audio_bytes, cache_key)
        """
        if not self.elevenlabs_key:
            logger.warning("elevenlabs_api_key_missing")
            raise ValueError("ElevenLabs API key not configured")

        voice_id = self._get_voice_id(personality)
        cache_key = self._get_cache_key(text, voice_id)
        cache_path = self._get_cache_path(cache_key)

        # Vérifier le cache
        if use_cache and cache_path.exists():
            logger.info("tts_cache_hit", cache_key=cache_key)
            return cache_path.read_bytes(), cache_key

        # Appeler ElevenLabs
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}",
                headers={"xi-api-key": self.elevenlabs_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": settings.ELEVENLABS_MODEL,
                    "voice_settings": {"stability": stability, "similarity_boost": similarity_boost},
                },
            )

            if response.status_code != 200:
                logger.error("elevenlabs_tts_error", status=response.status_code, response=response.text[:200])
                raise Exception(f"ElevenLabs error: {response.status_code} - {response.text}")

            audio_bytes = response.content

        # Sauvegarder dans le cache
        if use_cache:
            cache_path.write_bytes(audio_bytes)
            logger.info("tts_cached", cache_key=cache_key, size=len(audio_bytes))

        return audio_bytes, cache_key

    async def text_to_speech_stream(self, text: str, personality: str = "neutral") -> AsyncGenerator[bytes, None]:
        """
        Stream audio via ElevenLabs (pour réponse plus rapide).
        Yields chunks d'audio.
        """
        if not self.elevenlabs_key:
            raise ValueError("ElevenLabs API key not configured")

        voice_id = self._get_voice_id(personality)

        async with (
            httpx.AsyncClient(timeout=60.0) as client,
            client.stream(
                "POST",
                f"{self.ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream",
                headers={"xi-api-key": self.elevenlabs_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": settings.ELEVENLABS_MODEL,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            ) as response,
        ):
            if response.status_code != 200:
                raise Exception(f"ElevenLabs stream error: {response.status_code}")

            async for chunk in response.aiter_bytes():
                yield chunk

    # ═══════════════════════════════════════════════════════════════
    # STT - SPEECH TO TEXT (Whisper API)
    # ═══════════════════════════════════════════════════════════════

    async def speech_to_text(self, audio_bytes: bytes, language: str = "fr") -> dict:
        """
        Convertit de l'audio en texte via Whisper API.

        Args:
            audio_bytes: Audio au format webm, mp3, wav, etc.
            language: Code langue (fr, en, etc.)

        Returns:
            dict: {
                "text": str,
                "duration": float,
                "language": str
            }
        """
        if not self.openai_key:
            logger.warning("openai_api_key_missing")
            raise ValueError("OpenAI API key not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Préparer le fichier pour l'upload
            files = {
                "file": ("audio.webm", audio_bytes, "audio/webm"),
            }
            data = {"model": "whisper-1", "language": language, "response_format": "verbose_json"}

            response = await client.post(
                f"{self.OPENAI_BASE_URL}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                files=files,
                data=data,
            )

            if response.status_code != 200:
                logger.error("whisper_stt_error", status=response.status_code, response=response.text[:200])
                raise Exception(f"Whisper error: {response.status_code} - {response.text}")

            result = response.json()

            logger.info("stt_completed", text_length=len(result.get("text", "")), duration=result.get("duration", 0))

            return {
                "text": result.get("text", ""),
                "duration": result.get("duration", 0),
                "language": result.get("language", language),
            }

    # ═══════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════

    def audio_to_base64(self, audio_bytes: bytes) -> str:
        """Encode l'audio en base64."""
        return base64.b64encode(audio_bytes).decode("utf-8")

    def base64_to_audio(self, base64_string: str) -> bytes:
        """Décode le base64 en audio."""
        return base64.b64decode(base64_string)

    async def get_elevenlabs_voices(self) -> list[dict]:
        """Liste les voix disponibles sur ElevenLabs."""
        if not self.elevenlabs_key:
            raise ValueError("ElevenLabs API key not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.ELEVENLABS_BASE_URL}/voices", headers={"xi-api-key": self.elevenlabs_key}
            )

            # Fallback to configured voices if API fails (permission issue)
            if response.status_code != 200:
                logger.warning(
                    "elevenlabs_voices_fallback", status=response.status_code, reason="Using configured voices"
                )
                return self._get_configured_voices()

            data = response.json()
            return [
                {
                    "voice_id": v["voice_id"],
                    "name": v["name"],
                    "category": v.get("category", ""),
                    "labels": v.get("labels", {}),
                }
                for v in data.get("voices", [])
            ]

    def _get_configured_voices(self) -> list[dict]:
        """Retourne les voix configurées dans .env."""
        voices = []
        if settings.ELEVENLABS_VOICE_FRIENDLY:
            voices.append(
                {
                    "voice_id": settings.ELEVENLABS_VOICE_FRIENDLY,
                    "name": "Friendly (Rachel)",
                    "category": "configured",
                    "labels": {"level": "beginner"},
                }
            )
        if settings.ELEVENLABS_VOICE_NEUTRAL:
            voices.append(
                {
                    "voice_id": settings.ELEVENLABS_VOICE_NEUTRAL,
                    "name": "Neutral",
                    "category": "configured",
                    "labels": {"level": "intermediate"},
                }
            )
        if settings.ELEVENLABS_VOICE_AGGRESSIVE:
            voices.append(
                {
                    "voice_id": settings.ELEVENLABS_VOICE_AGGRESSIVE,
                    "name": "Aggressive (Senior)",
                    "category": "configured",
                    "labels": {"level": "expert"},
                }
            )
        return voices

    async def check_elevenlabs_quota(self) -> dict:
        """Vérifie le quota ElevenLabs restant."""
        if not self.elevenlabs_key:
            raise ValueError("ElevenLabs API key not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.ELEVENLABS_BASE_URL}/user/subscription", headers={"xi-api-key": self.elevenlabs_key}
            )

            # Fallback if API fails (permission issue)
            if response.status_code != 200:
                logger.warning(
                    "elevenlabs_quota_fallback", status=response.status_code, reason="Quota check unavailable"
                )
                return {
                    "character_count": -1,
                    "character_limit": -1,
                    "remaining": -1,
                    "tier": "unknown",
                    "status": "unavailable",
                    "message": "Quota API requires elevated permissions",
                }

            data = response.json()
            return {
                "character_count": data.get("character_count", 0),
                "character_limit": data.get("character_limit", 0),
                "remaining": data.get("character_limit", 0) - data.get("character_count", 0),
                "tier": data.get("tier", "unknown"),
                "status": "available",
            }

    def is_configured(self) -> dict:
        """Vérifie si les services sont configurés."""
        return {
            "elevenlabs": bool(self.elevenlabs_key),
            "whisper": bool(self.openai_key),
            "voice_friendly": bool(settings.ELEVENLABS_VOICE_FRIENDLY),
            "voice_neutral": bool(settings.ELEVENLABS_VOICE_NEUTRAL),
            "voice_aggressive": bool(settings.ELEVENLABS_VOICE_AGGRESSIVE),
        }


# Instance globale
voice_service = VoiceService()
