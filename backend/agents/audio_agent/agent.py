"""
Audio Agent - Autonomous agent for audio/video processing.
"""

import os
from typing import Optional

from agents.base_agent import BaseAgent, ToolResult
from .tools import AudioTools
from .memory import VoiceMemory


class AudioAgent(BaseAgent):
    """
    Audio processing agent.

    Capabilities:
    - Extract audio from video (FFmpeg)
    - Transcribe audio (Whisper)
    - Clone voice (ElevenLabs)
    - Text-to-speech generation
    """

    SYSTEM_PROMPT = """Tu es l'Audio Agent de Champion Clone.

Ton rôle est de traiter les fichiers audio/vidéo pour extraire le contenu vocal des champions de la vente.

CAPACITÉS:
1. extract_audio: Extraire l'audio d'une vidéo (FFmpeg)
   - Input: video_path, output_format (mp3/wav), sample_rate
   - Output: audio_path, duration, metadata

2. transcribe: Transcrire l'audio en texte (Whisper)
   - Input: audio_path, language (fr/en)
   - Output: transcript, segments avec timestamps

3. clone_voice: Cloner une voix (ElevenLabs)
   - Input: name, audio_samples (liste de chemins)
   - Output: voice_id

4. text_to_speech: Générer de l'audio à partir de texte
   - Input: text, voice_id
   - Output: audio_path

5. analyze_audio: Analyser les caractéristiques audio
   - Input: audio_path
   - Output: duration, sample_rate, channels, etc.

WORKFLOW TYPIQUE:
1. Recevoir un fichier vidéo
2. Extraire l'audio
3. Transcrire avec Whisper
4. (Optionnel) Cloner la voix pour TTS ultérieur

RÈGLES:
- Toujours vérifier que les fichiers existent avant traitement
- Utiliser le français comme langue par défaut pour la transcription
- Stocker les profils vocaux en mémoire pour réutilisation
- Retourner des métadonnées complètes avec chaque opération

Choisis les outils appropriés pour accomplir la tâche demandée."""

    def __init__(self):
        super().__init__(
            name="Audio Agent",
            model=os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514")
        )

        self.tools_impl = AudioTools()
        self.memory = VoiceMemory()

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "extract_audio",
                "description": "Extract audio track from a video file using FFmpeg",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "video_path": {
                            "type": "string",
                            "description": "Path to the video file"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["mp3", "wav"],
                            "default": "mp3",
                            "description": "Output audio format"
                        },
                        "sample_rate": {
                            "type": "integer",
                            "default": 16000,
                            "description": "Sample rate in Hz (16000 recommended for Whisper)"
                        }
                    },
                    "required": ["video_path"]
                }
            },
            {
                "name": "transcribe",
                "description": "Transcribe audio file to text using OpenAI Whisper",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "Path to the audio file"
                        },
                        "language": {
                            "type": "string",
                            "default": "fr",
                            "description": "Language code (fr, en, etc.)"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Optional context prompt to improve transcription"
                        }
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "clone_voice",
                "description": "Clone a voice using ElevenLabs from audio samples",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the cloned voice"
                        },
                        "audio_samples": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of audio file paths for cloning"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the voice"
                        }
                    },
                    "required": ["name", "audio_samples"]
                }
            },
            {
                "name": "text_to_speech",
                "description": "Generate audio from text using a cloned voice",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech"
                        },
                        "voice_id": {
                            "type": "string",
                            "description": "ElevenLabs voice ID"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional output file path"
                        }
                    },
                    "required": ["text", "voice_id"]
                }
            },
            {
                "name": "analyze_audio",
                "description": "Analyze audio file characteristics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "Path to the audio file"
                        }
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "store_voice_profile",
                "description": "Store a voice profile in memory for later use",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "champion_id": {
                            "type": "integer",
                            "description": "Champion ID"
                        },
                        "name": {
                            "type": "string",
                            "description": "Voice profile name"
                        },
                        "audio_samples": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Audio sample paths"
                        },
                        "elevenlabs_voice_id": {
                            "type": "string",
                            "description": "ElevenLabs voice ID if available"
                        }
                    },
                    "required": ["champion_id", "name"]
                }
            }
        ]

    async def execute_tool(self, name: str, input_data: dict) -> ToolResult:
        """Execute a tool and return the result."""
        try:
            if name == "extract_audio":
                result = await self.tools_impl.extract_audio(
                    video_path=input_data["video_path"],
                    output_format=input_data.get("output_format", "mp3"),
                    sample_rate=input_data.get("sample_rate", 16000)
                )

            elif name == "transcribe":
                result = await self.tools_impl.transcribe(
                    audio_path=input_data["audio_path"],
                    language=input_data.get("language", "fr"),
                    prompt=input_data.get("prompt")
                )

            elif name == "clone_voice":
                result = await self.tools_impl.clone_voice(
                    name=input_data["name"],
                    audio_samples=input_data["audio_samples"],
                    description=input_data.get("description")
                )

            elif name == "text_to_speech":
                result = await self.tools_impl.text_to_speech(
                    text=input_data["text"],
                    voice_id=input_data["voice_id"],
                    output_path=input_data.get("output_path")
                )

            elif name == "analyze_audio":
                result = await self.tools_impl.analyze_audio(
                    audio_path=input_data["audio_path"]
                )

            elif name == "store_voice_profile":
                import uuid
                profile_id = str(uuid.uuid4())[:8]
                success = await self.memory.store(
                    key=profile_id,
                    value={
                        "champion_id": input_data["champion_id"],
                        "name": input_data["name"],
                        "audio_samples": input_data.get("audio_samples", []),
                        "elevenlabs_voice_id": input_data.get("elevenlabs_voice_id")
                    }
                )
                result = {"success": success, "profile_id": profile_id}

            else:
                return ToolResult(
                    tool_name=name,
                    success=False,
                    output=None,
                    error=f"Unknown tool: {name}"
                )

            return ToolResult(
                tool_name=name,
                success=result.get("success", True),
                output=result,
                error=result.get("error")
            )

        except Exception as e:
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(e)
            )
