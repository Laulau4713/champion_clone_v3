"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ============================================
# Auth Schemas
# ============================================


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str | None = Field(None, description="User's full name")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user response (no password!)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None = None
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


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(None, description="User's full name")
    email: EmailStr | None = Field(None, description="New email address")


class PasswordChange(BaseModel):
    """Schema for changing password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


# ============================================
# Champion Schemas
# ============================================


class ChampionBase(BaseModel):
    """Base champion fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Champion's name")
    description: str | None = Field(None, description="Optional description")


class ChampionCreate(ChampionBase):
    """Schema for creating a champion (via file upload)."""

    pass


class ChampionPatterns(BaseModel):
    """Extracted sales patterns structure."""

    openings: list[str] = Field(default_factory=list, description="Opening techniques")
    objection_handlers: list[dict[str, Any]] = Field(
        default_factory=list, description="Objection handling patterns with context"
    )
    closes: list[str] = Field(default_factory=list, description="Closing techniques")
    key_phrases: list[str] = Field(default_factory=list, description="Signature phrases")
    tone_style: str = Field("", description="Overall communication style")
    success_patterns: list[str] = Field(default_factory=list, description="Successful patterns identified")


class ChampionResponse(ChampionBase):
    """Schema for champion response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    # video_path and audio_path removed - never expose internal server paths
    has_video: bool | None = None  # Indicates if video exists
    has_audio: bool | None = None  # Indicates if audio was extracted
    transcript: str | None = None
    patterns_json: dict[str, Any] | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class ChampionListResponse(BaseModel):
    """Schema for listing champions."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
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
    objectives: list[str] = Field(default_factory=list, description="Training objectives")
    difficulty: str = Field("medium", description="Difficulty level: easy, medium, hard")


class ScenarioResponse(BaseModel):
    """Response containing generated scenarios."""

    champion_id: int
    champion_name: str
    scenarios: list[TrainingScenario]


# ============================================
# Training Session Schemas
# ============================================


class SessionMessage(BaseModel):
    """Individual message in a training session."""

    role: str = Field(..., pattern="^(champion|user|system)$", description="Message sender")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feedback: str | None = Field(None, description="AI feedback on user response")
    score: float | None = Field(None, ge=0, le=10, description="Score 0-10")


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
    tips: list[str] = Field(default_factory=list, description="Tips for the user")


class SessionRespondRequest(BaseModel):
    """User's response in a training session."""

    session_id: int = Field(..., description="Active session ID")
    user_response: str = Field(..., min_length=1, description="User's response to champion")


class SessionRespondResponse(BaseModel):
    """Champion's response and feedback."""

    champion_response: str = Field(..., description="Champion's next message")
    feedback: str = Field(..., description="Feedback on user's response")
    score: float = Field(..., ge=0, le=10, description="Score for user's response")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
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
    strengths: list[str]
    areas_for_improvement: list[str]
    duration_seconds: int


class SessionResponse(BaseModel):
    """Full session response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    champion_id: int
    scenario: dict[str, Any] | None
    messages: list[dict[str, Any]]
    overall_score: float | None
    feedback_summary: str | None
    status: str
    started_at: datetime
    ended_at: datetime | None


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
    patterns: ChampionPatterns | None = None


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
    detail: str | None = None
    code: str


class ValidationErrorResponse(BaseModel):
    """Validation error details."""

    loc: list[str]
    msg: str
    type: str


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool
    message: str


# ============================================
# Enriched Scenario Data Schemas (Phase 1)
# ============================================


class HowItWorksSchema(BaseModel):
    """How the product/service works."""

    summary: str = Field(..., description="Brief summary of how it works")
    key_features: list[str] = Field(default_factory=list, description="Main features")
    technical_requirements: str | None = Field(None, description="Technical requirements")
    implementation_time: str | None = Field(None, description="Time to implement")


class SupportSchema(BaseModel):
    """Support and onboarding details."""

    onboarding: str | None = Field(None, description="Onboarding process")
    support: str | None = Field(None, description="Support channels and hours")
    documentation: str | None = Field(None, description="Documentation available")
    csm: str | None = Field(None, description="Customer Success Manager details")
    sla: str | None = Field(None, description="SLA details")


class PricingSchema(BaseModel):
    """Pricing information."""

    model: str = Field(..., description="Pricing model: flat, per_user, usage")
    entry_price: str | None = Field(None, description="Entry-level price")
    popular_plan: str | None = Field(None, description="Most popular plan")
    enterprise: str | None = Field(None, description="Enterprise pricing")
    engagement: str | None = Field(None, description="Commitment options")
    free_trial: str | None = Field(None, description="Free trial details")
    minimum: str | None = Field(None, description="Minimum purchase")


class ProductInfoCreate(BaseModel):
    """Schema for creating a ProductInfo."""

    slug: str = Field(..., min_length=1, max_length=100, description="Unique slug")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    tagline: str = Field(..., min_length=1, max_length=500, description="Product tagline")
    category: str | None = Field(None, description="Product category")
    how_it_works: HowItWorksSchema | None = None
    integrations: list[str] | None = None
    support_included: SupportSchema | None = None
    pricing: PricingSchema | None = None


class ProductInfoResponse(BaseModel):
    """Schema for ProductInfo response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    tagline: str
    category: str | None = None
    how_it_works: dict[str, Any] | None = None
    integrations: list[str] | None = None
    support_included: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TestimonialSchema(BaseModel):
    """Customer testimonial."""

    name: str = Field(..., description="Customer name")
    role: str = Field(..., description="Customer role/title")
    company: str = Field(..., description="Company name and size")
    quote: str = Field(..., description="Testimonial quote")
    result: str | None = Field(None, description="Measurable result")


class CaseStudySchema(BaseModel):
    """Case study details."""

    client: str = Field(..., description="Client name")
    sector: str | None = Field(None, description="Client sector")
    problem: str = Field(..., description="Problem they faced")
    solution: str = Field(..., description="Solution implemented")
    results: dict[str, Any] = Field(default_factory=dict, description="Measurable results")


class StatsSchema(BaseModel):
    """Product statistics."""

    clients_count: str | None = Field(None, description="Number of clients")
    satisfaction: str | None = Field(None, description="Satisfaction rating")
    nps: str | None = Field(None, description="Net Promoter Score")
    uptime: str | None = Field(None, description="Uptime percentage")
    attacks_blocked: str | None = Field(None, description="Security-specific stat")


class ProofElementsCreate(BaseModel):
    """Schema for creating ProofElements."""

    product_id: int = Field(..., description="Associated product ID")
    testimonials: list[TestimonialSchema] | None = None
    case_studies: list[CaseStudySchema] | None = None
    stats: StatsSchema | None = None
    notable_clients: list[str] | None = None


class ProofElementsResponse(BaseModel):
    """Schema for ProofElements response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    testimonials: list[dict[str, Any]] | None = None
    case_studies: list[dict[str, Any]] | None = None
    stats: dict[str, Any] | None = None
    notable_clients: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class CompetitorSchema(BaseModel):
    """Competitor information."""

    name: str = Field(..., description="Competitor name")
    positioning: str = Field(..., description="Market positioning")
    strengths: list[str] = Field(default_factory=list, description="Their strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Their weaknesses")
    price_comparison: str | None = Field(None, description="Price comparison")


class SwitchCostSchema(BaseModel):
    """Cost of switching from competitor."""

    migration_time: str | None = Field(None, description="Time to migrate")
    data_import: str | None = Field(None, description="Data import capabilities")
    training_needed: str | None = Field(None, description="Training requirements")
    risk: str | None = Field(None, description="Migration risk assessment")
    difficulty: str | None = Field(None, description="Migration difficulty")


class CompetitionInfoCreate(BaseModel):
    """Schema for creating CompetitionInfo."""

    product_id: int = Field(..., description="Associated product ID")
    main_competitors: list[CompetitorSchema] | None = None
    our_differentiator: str | None = Field(None, description="Key differentiator")
    switch_cost: SwitchCostSchema | None = None


class CompetitionInfoResponse(BaseModel):
    """Schema for CompetitionInfo response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    main_competitors: list[dict[str, Any]] | None = None
    our_differentiator: str | None = None
    switch_cost: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class EnrichedScenarioData(BaseModel):
    """
    Complete enriched scenario data combining product, proof, and competition.

    This is used in scenario templates and generated scenarios.
    """

    product: ProductInfoCreate
    proof: ProofElementsCreate | None = None
    competition: CompetitionInfoCreate | None = None


class ProductInfoWithRelations(ProductInfoResponse):
    """ProductInfo with all related proof and competition data."""

    proof_elements: list[ProofElementsResponse] = Field(default_factory=list)
    competition_info: list[CompetitionInfoResponse] = Field(default_factory=list)
