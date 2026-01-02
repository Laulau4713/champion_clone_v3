"""
Audio Agent Memory - Voice profiles and audio metadata storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import structlog

from memory.schemas import VoiceProfile

logger = structlog.get_logger()


class VoiceMemory:
    """
    Memory for voice profiles and audio metadata.

    Stores:
    - Voice profiles (characteristics, samples)
    - Audio file metadata
    - Transcription cache
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or os.getenv("VOICE_STORAGE", "./data/voices"))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.profiles_file = self.storage_path / "profiles.json"
        self.profiles: dict[str, VoiceProfile] = {}

        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from disk."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file) as f:
                    data = json.load(f)
                    for profile_data in data.get("profiles", []):
                        profile = VoiceProfile(
                            id=profile_data["id"],
                            champion_id=profile_data["champion_id"],
                            name=profile_data["name"],
                            audio_samples=profile_data.get("audio_samples", []),
                            elevenlabs_voice_id=profile_data.get("elevenlabs_voice_id"),
                            characteristics=profile_data.get("characteristics", {}),
                            created_at=datetime.fromisoformat(profile_data["created_at"]),
                        )
                        self.profiles[profile.id] = profile
                logger.info("voice_profiles_loaded", count=len(self.profiles))
            except Exception as e:
                logger.error("voice_profiles_load_error", error=str(e))

    def _save_profiles(self):
        """Save profiles to disk."""
        try:
            data = {"profiles": [p.to_dict() for p in self.profiles.values()]}
            with open(self.profiles_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("voice_profiles_save_error", error=str(e))

    async def store(self, key: str, value: dict, metadata: dict | None = None) -> bool:
        """
        Store a voice profile.

        Args:
            key: Profile ID
            value: Profile data
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            profile = VoiceProfile(
                id=key,
                champion_id=value.get("champion_id", 0),
                name=value.get("name", "Unknown"),
                audio_samples=value.get("audio_samples", []),
                elevenlabs_voice_id=value.get("elevenlabs_voice_id"),
                characteristics=value.get("characteristics", {}),
            )

            self.profiles[key] = profile
            self._save_profiles()

            logger.debug("voice_profile_stored", key=key)
            return True

        except Exception as e:
            logger.error("voice_profile_store_error", key=key, error=str(e))
            return False

    async def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        """
        Retrieve voice profiles.

        Args:
            query: Champion ID or name to search
            limit: Max results

        Returns:
            List of matching profiles
        """
        results = []

        for profile in self.profiles.values():
            # Match by champion_id or name
            if str(profile.champion_id) == query or query.lower() in profile.name.lower():
                results.append(profile.to_dict())

            if len(results) >= limit:
                break

        return results

    async def get_by_champion(self, champion_id: int) -> VoiceProfile | None:
        """Get voice profile for a champion."""
        for profile in self.profiles.values():
            if profile.champion_id == champion_id:
                return profile
        return None

    async def add_audio_sample(self, profile_id: str, audio_path: str) -> bool:
        """Add audio sample to profile."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        profile.audio_samples.append(audio_path)
        self._save_profiles()
        return True

    async def update_elevenlabs_id(self, profile_id: str, voice_id: str) -> bool:
        """Update ElevenLabs voice ID."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        profile.elevenlabs_voice_id = voice_id
        self._save_profiles()
        return True

    async def delete(self, key: str) -> bool:
        """Delete a voice profile."""
        if key in self.profiles:
            del self.profiles[key]
            self._save_profiles()
            return True
        return False
