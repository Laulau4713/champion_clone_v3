"""
Audio Tasks - Celery tasks for audio processing
================================================

Handles:
- Audio transcription (Whisper)
- TTS generation (ElevenLabs)
- Audio extraction from video (FFmpeg)
"""

import os
import subprocess
from pathlib import Path

import structlog
from celery import shared_task

logger = structlog.get_logger()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio"))


# =============================================================================
# AUDIO TRANSCRIPTION (Whisper)
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    rate_limit="20/m",
    time_limit=300,  # 5 minutes max
)
def transcribe_audio(self, audio_path: str, language: str = "fr"):
    """
    Transcribe audio file using Whisper.

    Args:
        audio_path: Path to audio file
        language: Language code (default: French)

    Returns:
        dict: {"text": str, "segments": list, "language": str}
    """
    try:
        import whisper

        logger.info("transcription_started", audio_path=audio_path)

        # Load model (cached after first load)
        model = whisper.load_model("base")  # Use 'small' or 'medium' for better quality

        # Transcribe
        result = model.transcribe(
            audio_path,
            language=language,
            fp16=False,  # CPU compatibility
        )

        logger.info(
            "transcription_completed",
            audio_path=audio_path,
            text_length=len(result["text"]),
        )

        return {
            "text": result["text"],
            "segments": result.get("segments", []),
            "language": result.get("language", language),
        }

    except Exception as e:
        logger.error("transcription_failed", audio_path=audio_path, error=str(e))
        raise


# =============================================================================
# TTS GENERATION (ElevenLabs)
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    rate_limit="10/m",
    time_limit=120,
)
def generate_tts(self, text: str, voice_id: str = None, output_filename: str = None):
    """
    Generate speech from text using ElevenLabs.

    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (optional, uses default)
        output_filename: Output file name (optional, auto-generated)

    Returns:
        dict: {"audio_path": str, "duration": float}
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("elevenlabs_not_configured")
        return {"audio_path": None, "error": "ElevenLabs not configured"}

    try:
        from elevenlabs import generate, save, set_api_key

        set_api_key(api_key)

        # Use default voice if not specified
        voice = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel (default)

        logger.info("tts_started", text_length=len(text), voice_id=voice)

        # Generate audio
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2",
        )

        # Save to file
        if not output_filename:
            import uuid

            output_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"

        output_path = AUDIO_DIR / output_filename
        save(audio, str(output_path))

        logger.info("tts_completed", output_path=str(output_path))

        return {
            "audio_path": str(output_path),
            "filename": output_filename,
        }

    except Exception as e:
        logger.error("tts_failed", error=str(e))
        raise


# =============================================================================
# AUDIO EXTRACTION FROM VIDEO (FFmpeg)
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=1,
    time_limit=600,  # 10 minutes for large videos
)
def extract_audio_from_video(self, video_path: str, output_format: str = "mp3"):
    """
    Extract audio track from video file using FFmpeg.

    Args:
        video_path: Path to video file
        output_format: Audio format (mp3, wav, etc.)

    Returns:
        dict: {"audio_path": str, "duration": float}
    """
    try:
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Generate output path
        audio_filename = f"{video_path.stem}.{output_format}"
        audio_path = AUDIO_DIR / audio_filename

        logger.info("audio_extraction_started", video_path=str(video_path))

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vn",  # No video
            "-acodec",
            "libmp3lame" if output_format == "mp3" else "pcm_s16le",
            "-ar",
            "16000",  # 16kHz for Whisper
            "-ac",
            "1",  # Mono
            "-y",  # Overwrite
            str(audio_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

        # Get duration
        duration = get_audio_duration(str(audio_path))

        logger.info(
            "audio_extraction_completed",
            audio_path=str(audio_path),
            duration=duration,
        )

        return {
            "audio_path": str(audio_path),
            "filename": audio_filename,
            "duration": duration,
        }

    except subprocess.TimeoutExpired:
        logger.error("audio_extraction_timeout", video_path=str(video_path))
        raise
    except Exception as e:
        logger.error("audio_extraction_failed", error=str(e))
        raise


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using FFprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0
