"""
Champions Router.

Endpoints:
- POST /upload - Upload champion video
- POST /analyze/{champion_id} - Analyze video for patterns
- GET /champions - List all champions
- GET /champions/{champion_id} - Get champion details
- DELETE /champions/{champion_id} - Delete champion
"""

import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import AnalysisLog, Champion, User
from schemas import AnalyzeRequest, AnalyzeResponse, ChampionListResponse, ChampionResponse, UploadResponse

settings = get_settings()
logger = structlog.get_logger()

router = APIRouter(tags=["Champions"])


# ============================================
# Video Validation
# ============================================


def validate_video_file(file_bytes: bytes) -> bool:
    """
    Validate that file is actually a video by checking magic bytes.
    """
    # Check for MP4/MOV (ftyp at offset 4)
    if len(file_bytes) >= 12:
        ftyp_marker = file_bytes[4:8]
        if ftyp_marker == b"ftyp":
            return True

    # Check for AVI (RIFF at offset 0, AVI at offset 8)
    if len(file_bytes) >= 12:
        if file_bytes[0:4] == b"RIFF" and file_bytes[8:11] == b"AVI":
            return True

    return False


# ============================================
# Dependencies (imported from auth router)
# ============================================

from api.routers.auth import get_current_user, require_enterprise_access

# ============================================
# Endpoints
# ============================================


@router.post("/upload", response_model=UploadResponse)
async def upload_champion_video(
    request: Request,
    name: str = Form(..., description="Champion's name"),
    description: str | None = Form(None, description="Optional description"),
    video: UploadFile = File(..., description="Video file (MP4/MOV). Max 500 MB."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """
    Upload a champion's video for analysis.

    Accepts MP4 or MOV files (max 500 MB). The video will be processed to:
    1. Extract audio
    2. Transcribe using Whisper
    3. Store for pattern analysis
    """
    # Validate file extension
    file_ext = Path(video.filename).suffix.lower() if video.filename else ""
    if file_ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=400, detail=f"Invalid file extension. Allowed: {settings.ALLOWED_EXTENSIONS}. Got: {file_ext}"
        )

    # Validate magic bytes
    first_bytes = await video.read(12)
    await video.seek(0)

    if not validate_video_file(first_bytes):
        raise HTTPException(status_code=400, detail="Invalid file content. File does not appear to be a valid video.")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    video_path = upload_dir / unique_filename

    logger.info("uploading_video", filename=video.filename, champion=name)

    try:
        # Save with size limit check
        total_size = 0
        chunk_size = 1024 * 1024  # 1 MB

        with open(video_path, "wb") as buffer:
            while chunk := video.file.read(chunk_size):
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE:
                    buffer.close()
                    video_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
                    )
                buffer.write(chunk)

        # Create champion record
        champion = Champion(name=name, description=description, video_path=str(video_path), status="uploaded")
        db.add(champion)
        await db.flush()

        # Log the upload
        log = AnalysisLog(
            champion_id=champion.id,
            step="upload",
            status="completed",
            details={"filename": video.filename, "size": video_path.stat().st_size},
        )
        db.add(log)
        await db.commit()

        logger.info("video_uploaded", champion_id=champion.id, path=str(video_path))

        return UploadResponse(
            champion_id=champion.id,
            name=champion.name,
            status=champion.status,
            message="Video uploaded successfully. Use POST /analyze/{champion_id} to process.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_error", error=str(e))
        if video_path.exists():
            video_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze/{champion_id}", response_model=AnalyzeResponse)
async def analyze_champion(
    request: Request,
    champion_id: int,
    body: AnalyzeRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """
    Analyze a champion's video to extract sales patterns.

    This process:
    1. Extracts audio from video (ffmpeg)
    2. Transcribes audio (Whisper)
    3. Analyzes transcript for patterns (Claude Opus)
    """
    # Import agents here to avoid circular imports
    from agents import AudioAgent, PatternAgent

    result = await db.execute(select(Champion).where(Champion.id == champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if champion.patterns_json and not (body and body.force_reanalyze):
        return AnalyzeResponse(
            champion_id=champion.id,
            status="already_analyzed",
            message="Patterns already extracted. Use force_reanalyze=true to re-analyze.",
            patterns=champion.patterns_json,
        )

    if not champion.video_path:
        raise HTTPException(status_code=400, detail="No video file associated with champion")

    logger.info("starting_analysis", champion_id=champion_id)

    try:
        champion.status = "processing"
        await db.commit()

        log = AnalysisLog(champion_id=champion_id, step="analysis_start", status="started")
        db.add(log)
        await db.commit()

        # Initialize agents
        audio_agent = AudioAgent()
        pattern_agent = PatternAgent()

        # Step 1: Extract audio and transcribe
        audio_result = await audio_agent.execute_tool("extract_audio", {"video_path": champion.video_path})
        champion.audio_path = audio_result.data.get("audio_path")

        transcript_result = await audio_agent.execute_tool("transcribe", {"audio_path": champion.audio_path})
        champion.transcript = transcript_result.data.get("transcript")

        log = AnalysisLog(
            champion_id=champion_id,
            step="transcription",
            status="completed",
            details={"transcript_length": len(champion.transcript) if champion.transcript else 0},
        )
        db.add(log)
        await db.commit()

        # Step 2: Extract patterns
        pattern_result = await pattern_agent.execute_tool(
            "extract_patterns", {"transcript": champion.transcript, "champion_name": champion.name}
        )
        patterns = pattern_result.data.get("patterns", {})
        champion.patterns_json = patterns
        champion.status = "ready"

        log = AnalysisLog(
            champion_id=champion_id,
            step="pattern_extraction",
            status="completed",
            details={
                "openings": len(patterns.get("openings", [])),
                "objection_handlers": len(patterns.get("objection_handlers", [])),
                "closes": len(patterns.get("closes", [])),
            },
        )
        db.add(log)
        await db.commit()

        logger.info("analysis_complete", champion_id=champion_id)

        return AnalyzeResponse(
            champion_id=champion.id,
            status="completed",
            message="Analysis complete. Patterns extracted successfully.",
            patterns=patterns,
        )

    except Exception as e:
        logger.error("analysis_error", champion_id=champion_id, error=str(e))

        champion.status = "error"
        log = AnalysisLog(champion_id=champion_id, step="analysis", status="error", error_message=str(e))
        db.add(log)
        await db.commit()

        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/champions", response_model=list[ChampionListResponse])
async def list_champions(
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """List all champions. Requires Enterprise plan."""
    query = select(Champion).order_by(Champion.created_at.desc())

    if status:
        query = query.where(Champion.status == status)

    result = await db.execute(query)
    champions = result.scalars().all()

    return [ChampionListResponse.model_validate(c) for c in champions]


@router.get("/champions/{champion_id}", response_model=ChampionResponse)
async def get_champion(
    champion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """Get a specific champion's details. Requires Enterprise plan."""
    result = await db.execute(select(Champion).where(Champion.id == champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    return ChampionResponse(
        id=champion.id,
        name=champion.name,
        description=champion.description,
        has_video=bool(champion.video_path),
        has_audio=bool(champion.audio_path),
        transcript=champion.transcript,
        patterns_json=champion.patterns_json,
        status=champion.status,
        created_at=champion.created_at,
        updated_at=champion.updated_at,
    )


@router.delete("/champions/{champion_id}")
async def delete_champion(
    champion_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_enterprise_access)
):
    """Delete a champion and associated files."""
    result = await db.execute(select(Champion).where(Champion.id == champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    # Delete files
    for path in [champion.video_path, champion.audio_path]:
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("file_deletion_error", path=path, error=str(e))

    await db.delete(champion)
    await db.commit()

    return {"message": f"Champion {champion_id} deleted"}
