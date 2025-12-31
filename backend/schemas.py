"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# ============================================
# Auth Schemas
# ============================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User's full name")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user response (no password!)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: str = "user"
    created_at: datetime
    # Subscription & trial info
    subscription_plan: str = "free"
    trial_sessions_used: int = 0
    trial_sessions_max: int = 3  # Constant for frontend display


class Token(BaseModel):
    """JWT token response with access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


# ============================================
# Champion Schemas
# ============================================

class ChampionBase(BaseModel):
    """Base champion fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Champion's name")
    description: Optional[str] = Field(None, description="Optional description")


class ChampionCreate(ChampionBase):
    """Schema for creating a champion (via file upload)."""
    pass


class ChampionPatterns(BaseModel):
    """Extracted sales patterns structure."""
    openings: List[str] = Field(default_factory=list, description="Opening techniques")
    objection_handlers: List[dict[str, Any]] = Field(
        default_factory=list,
        description="Objection handling patterns with context"
    )
    closes: List[str] = Field(default_factory=list, description="Closing techniques")
    key_phrases: List[str] = Field(default_factory=list, description="Signature phrases")
    tone_style: str = Field("", description="Overall communication style")
    success_patterns: List[str] = Field(default_factory=list, description="Successful patterns identified")


class ChampionResponse(ChampionBase):
    """Schema for champion response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    # video_path and audio_path removed - never expose internal server paths
    has_video: Optional[bool] = None  # Indicates if video exists
    has_audio: Optional[bool] = None  # Indicates if audio was extracted
    transcript: Optional[str] = None
    patterns_json: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ChampionListResponse(BaseModel):
    """Schema for listing champions."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime


# ============================================
# Training Scenario Schemas
# ============================================

class TrainingScenario(BaseModel):
    """Generated training scenario."""
    context: str = Field(..., description="Business context for the scenario")
    prospect_type: str = Field(..., description="Type of prospect (e.g., 'skeptical CFO')")
    challenge: str = Field(..., description="Main challenge to overcome")
    objectives: List[str] = Field(default_factory=list, description="Training objectives")
    difficulty: str = Field("medium", description="Difficulty level: easy, medium, hard")


class ScenarioResponse(BaseModel):
    """Response containing generated scenarios."""
    champion_id: int
    champion_name: str
    scenarios: List[TrainingScenario]


# ============================================
# Training Session Schemas
# ============================================

class SessionMessage(BaseModel):
    """Individual message in a training session."""
    role: str = Field(..., pattern="^(champion|user|system)$", description="Message sender")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feedback: Optional[str] = Field(None, description="AI feedback on user response")
    score: Optional[float] = Field(None, ge=0, le=10, description="Score 0-10")


class SessionStartRequest(BaseModel):
    """Request to start a new training session."""
    champion_id: int = Field(..., description="Champion to train against")
    scenario_index: int = Field(0, ge=0, description="Which scenario to use (0-based)")
    # user_id removed - now taken from JWT token


class SessionStartResponse(BaseModel):
    """Response after starting a session."""
    session_id: int
    champion_name: str
    scenario: TrainingScenario
    first_message: str = Field(..., description="Champion's opening message")
    tips: List[str] = Field(default_factory=list, description="Tips for the user")


class SessionRespondRequest(BaseModel):
    """User's response in a training session."""
    session_id: int = Field(..., description="Active session ID")
    user_response: str = Field(..., min_length=1, description="User's response to champion")


class SessionRespondResponse(BaseModel):
    """Champion's response and feedback."""
    champion_response: str = Field(..., description="Champion's next message")
    feedback: str = Field(..., description="Feedback on user's response")
    score: float = Field(..., ge=0, le=10, description="Score for user's response")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    session_complete: bool = Field(False, description="Whether session is complete")


class SessionEndRequest(BaseModel):
    """Request to end a training session."""
    session_id: int = Field(..., description="Session to end")


class SessionSummary(BaseModel):
    """Summary of a completed session."""
    session_id: int
    champion_name: str
    total_exchanges: int
    overall_score: float
    feedback_summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    duration_seconds: int


class SessionResponse(BaseModel):
    """Full session response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    champion_id: int
    scenario: Optional[dict[str, Any]]
    messages: List[dict[str, Any]]
    overall_score: Optional[float]
    feedback_summary: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]


# ============================================
# Analysis Schemas
# ============================================

class AnalyzeRequest(BaseModel):
    """Request to analyze a champion's video."""
    force_reanalyze: bool = Field(False, description="Force re-analysis even if already done")


class AnalyzeResponse(BaseModel):
    """Response from analysis endpoint."""
    champion_id: int
    status: str
    message: str
    patterns: Optional[ChampionPatterns] = None


# ============================================
# Upload Schemas
# ============================================

class UploadResponse(BaseModel):
    """Response after uploading a video."""
    champion_id: int
    name: str
    status: str
    message: str
    # video_path removed - never expose internal server paths


# ============================================
# Error Schemas
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: str


class ValidationErrorResponse(BaseModel):
    """Validation error details."""
    loc: List[str]
    msg: str
    type: str


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool
    message: str
