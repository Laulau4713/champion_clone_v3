"""
Audio Agent Tools - FFmpeg, Local Whisper, ElevenLabs integrations.

Uses LOCAL Whisper model (FREE) instead of OpenAI Whisper API.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
import uuid

import ffmpeg
import structlog

logger = structlog.get_logger()

# Try to import local Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("whisper_not_available", msg="Install openai-whisper for transcription")

# Try to import ElevenLabs
try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False


class AudioTools:
    """Collection of audio processing tools using FREE local Whisper."""

    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
        self.audio_dir = Path(os.getenv("AUDIO_DIR", "./audio"))

        # Local Whisper model (lazy loaded)
        self._whisper_model = None
        self._whisper_model_size = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large

        # ElevenLabs client (optional)
        if ELEVENLABS_AVAILABLE and os.getenv("ELEVENLABS_API_KEY"):
            self.elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        else:
            self.elevenlabs = None

        # Ensure directories
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def _get_whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            if not WHISPER_AVAILABLE:
                raise RuntimeError("Whisper not installed. Run: pip install openai-whisper")
            logger.info("loading_whisper_model", size=self._whisper_model_size)
            self._whisper_model = whisper.load_model(self._whisper_model_size)
        return self._whisper_model

    async def extract_audio(
        self,
        video_path: str,
        output_format: str = "mp3",
        sample_rate: int = 16000
    ) -> dict:
        """
        Extract audio from video file using FFmpeg.

        Args:
            video_path: Path to video file
            output_format: Output format (mp3, wav)
            sample_rate: Sample rate in Hz

        Returns:
            Dict with audio_path and metadata
        """
        video_path = Path(video_path)

        if not video_path.exists():
            return {"success": False, "error": f"Video not found: {video_path}"}

        # Generate output path
        audio_filename = f"{video_path.stem}_{uuid.uuid4().hex[:6]}.{output_format}"
        audio_path = self.audio_dir / audio_filename

        logger.info("extracting_audio", video=str(video_path), audio=str(audio_path))

        try:
            # Run FFmpeg extraction
            await asyncio.to_thread(
                self._run_ffmpeg,
                str(video_path),
                str(audio_path),
                sample_rate
            )

            if not audio_path.exists():
                return {"success": False, "error": "Audio extraction failed"}

            # Get audio duration
            duration = await self._get_duration(str(audio_path))

            return {
                "success": True,
                "audio_path": str(audio_path),
                "format": output_format,
                "sample_rate": sample_rate,
                "duration_seconds": duration,
                "file_size_bytes": audio_path.stat().st_size
            }

        except Exception as e:
            logger.error("audio_extraction_error", error=str(e))
            return {"success": False, "error": str(e)}

    def _run_ffmpeg(self, video_path: str, audio_path: str, sample_rate: int):
        """Synchronous FFmpeg execution."""
        (
            ffmpeg
            .input(video_path)
            .output(
                audio_path,
                acodec='libmp3lame',
                ab='192k',
                ar=str(sample_rate),
                ac=1,  # Mono
                loglevel='error'
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    async def _get_duration(self, audio_path: str) -> float:
        """Get audio duration."""
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, audio_path)
            return float(probe['format']['duration'])
        except Exception:
            return 0.0

    async def transcribe(
        self,
        audio_path: str,
        language: str = "fr",
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio using LOCAL Whisper model (FREE).

        Args:
            audio_path: Path to audio file
            language: Language code
            prompt: Optional context prompt

        Returns:
            Dict with transcript and metadata
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            return {"success": False, "error": f"Audio not found: {audio_path}"}

        if not WHISPER_AVAILABLE:
            return {"success": False, "error": "Whisper not installed. Run: pip install openai-whisper"}

        logger.info("transcribing_local", audio=str(audio_path), language=language)

        try:
            # Run Whisper in thread to avoid blocking
            model = self._get_whisper_model()
            result = await asyncio.to_thread(
                model.transcribe,
                str(audio_path),
                language=language,
                initial_prompt=prompt or "Ceci est un enregistrement commercial, vente, coaching.",
                verbose=False
            )

            # Extract text and segments
            transcript = result.get("text", "").strip()
            segments = [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                }
                for seg in result.get("segments", [])
            ]

            # Calculate duration from segments
            duration = segments[-1]["end"] if segments else 0

            return {
                "success": True,
                "transcript": transcript,
                "language": language,
                "segments": segments,
                "word_count": len(transcript.split()),
                "duration_seconds": duration,
                "model": f"whisper-local-{self._whisper_model_size}"
            }

        except Exception as e:
            logger.error("transcription_error", error=str(e))
            return {"success": False, "error": str(e)}

    async def clone_voice(
        self,
        name: str,
        audio_samples: list[str],
        description: Optional[str] = None
    ) -> dict:
        """
        Clone a voice using ElevenLabs.

        Args:
            name: Voice name
            audio_samples: List of audio file paths
            description: Voice description

        Returns:
            Dict with voice_id and metadata
        """
        if not self.elevenlabs:
            return {"success": False, "error": "ElevenLabs not configured"}

        logger.info("cloning_voice", name=name, samples=len(audio_samples))

        try:
            # Read audio files
            files = []
            for path in audio_samples:
                if Path(path).exists():
                    files.append(open(path, "rb"))

            if not files:
                return {"success": False, "error": "No valid audio samples"}

            # Create voice clone
            voice = await asyncio.to_thread(
                self.elevenlabs.clone,
                name=name,
                files=files,
                description=description or f"Voice clone for {name}"
            )

            # Close files
            for f in files:
                f.close()

            return {
                "success": True,
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category
            }

        except Exception as e:
            logger.error("voice_clone_error", error=str(e))
            return {"success": False, "error": str(e)}

    async def text_to_speech(
        self,
        text: str,
        voice_id: str,
        output_path: Optional[str] = None
    ) -> dict:
        """
        Generate speech from text using ElevenLabs.

        Args:
            text: Text to speak
            voice_id: ElevenLabs voice ID
            output_path: Optional output path

        Returns:
            Dict with audio path
        """
        if not self.elevenlabs:
            return {"success": False, "error": "ElevenLabs not configured"}

        try:
            # Generate audio
            audio = await asyncio.to_thread(
                self.elevenlabs.generate,
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )

            # Save to file
            if not output_path:
                output_path = str(self.audio_dir / f"tts_{uuid.uuid4().hex[:8]}.mp3")

            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            return {
                "success": True,
                "audio_path": output_path,
                "text_length": len(text)
            }

        except Exception as e:
            logger.error("tts_error", error=str(e))
            return {"success": False, "error": str(e)}

    async def analyze_audio(self, audio_path: str) -> dict:
        """
        Analyze audio characteristics.

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with analysis results
        """
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, audio_path)

            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            if not audio_stream:
                return {"success": False, "error": "No audio stream found"}

            return {
                "success": True,
                "duration_seconds": float(probe['format']['duration']),
                "bit_rate": int(probe['format'].get('bit_rate', 0)),
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "codec": audio_stream.get('codec_name', 'unknown')
            }

        except Exception as e:
            logger.error("audio_analysis_error", error=str(e))
            return {"success": False, "error": str(e)}
