"""
Application Configuration.

Centralized settings management using Pydantic Settings.
All configuration is loaded from environment variables or .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    All settings can be overridden via environment variables.
    """

    # ===========================================
    # Database
    # ===========================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./champion_clone.db"

    # ===========================================
    # JWT Authentication
    # ===========================================
    JWT_SECRET: str = ""
    REFRESH_TOKEN_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===========================================
    # Security (OWASP compliant)
    # ===========================================
    PASSWORD_MIN_LENGTH: int = 12  # OWASP recommends 12-14 for high security

    # ===========================================
    # File Upload
    # ===========================================
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500 MB
    UPLOAD_DIR: str = "./uploads"
    AUDIO_DIR: str = "./audio"
    ALLOWED_EXTENSIONS: str = ".mp4,.mov,.avi"

    # ===========================================
    # CORS
    # ===========================================
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ===========================================
    # Rate Limiting
    # ===========================================
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_UPLOAD: str = "10/hour"
    RATE_LIMIT_ANALYZE: str = "20/hour"
    RATE_LIMIT_TRAINING: str = "60/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/hour"
    RATE_LIMIT_REFRESH: str = "30/minute"
    # Admin endpoints - stricter limits
    RATE_LIMIT_ADMIN_READ: str = "100/minute"
    RATE_LIMIT_ADMIN_WRITE: str = "30/minute"
    RATE_LIMIT_ADMIN_DELETE: str = "10/minute"
    RATE_LIMIT_ADMIN_EXPORT: str = "5/minute"

    # ===========================================
    # API Keys
    # ===========================================
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # ===========================================
    # ElevenLabs Voice Configuration
    # ===========================================
    ELEVENLABS_VOICE_FRIENDLY: str = ""  # Voix amicale (niveau facile)
    ELEVENLABS_VOICE_NEUTRAL: str = ""  # Voix neutre (niveau moyen)
    ELEVENLABS_VOICE_AGGRESSIVE: str = ""  # Voix pressée (niveau expert)
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"

    # ===========================================
    # Claude Models
    # ===========================================
    CLAUDE_OPUS_MODEL: str = "claude-opus-4-20250514"
    CLAUDE_SONNET_MODEL: str = "claude-sonnet-4-20250514"

    # ===========================================
    # Server
    # ===========================================
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ===========================================
    # Email / SMTP (optional)
    # ===========================================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_FROM: str = ""

    # ===========================================
    # LemonSqueezy (Payments - disabled by default)
    # ===========================================
    LEMONSQUEEZY_API_KEY: str = ""
    LEMONSQUEEZY_WEBHOOK_SECRET: str = ""
    LEMONSQUEEZY_STORE_ID: str = ""
    LEMONSQUEEZY_VARIANT_STARTER: str = ""
    LEMONSQUEEZY_VARIANT_PRO: str = ""
    LEMONSQUEEZY_VARIANT_ENTERPRISE: str = ""

    # Properties for payment service
    @property
    def lemonsqueezy_api_key(self) -> str:
        return self.LEMONSQUEEZY_API_KEY

    @property
    def lemonsqueezy_webhook_secret(self) -> str:
        return self.LEMONSQUEEZY_WEBHOOK_SECRET

    @property
    def lemonsqueezy_store_id(self) -> str:
        return self.LEMONSQUEEZY_STORE_ID

    @property
    def lemonsqueezy_variant_starter(self) -> str:
        return self.LEMONSQUEEZY_VARIANT_STARTER

    @property
    def lemonsqueezy_variant_pro(self) -> str:
        return self.LEMONSQUEEZY_VARIANT_PRO

    @property
    def lemonsqueezy_variant_enterprise(self) -> str:
        return self.LEMONSQUEEZY_VARIANT_ENTERPRISE

    # ===========================================
    # Helpers
    # ===========================================

    @property
    def allowed_extensions_set(self) -> set[str]:
        """Get allowed extensions as a set."""
        return {ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")}

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def cors_origins(self) -> str:
        """Get CORS origins string."""
        return self.CORS_ORIGINS

    @property
    def smtp_host(self) -> str:
        """Get SMTP host."""
        return self.SMTP_HOST

    @property
    def smtp_port(self) -> int:
        """Get SMTP port."""
        return self.SMTP_PORT

    @property
    def smtp_user(self) -> str:
        """Get SMTP user."""
        return self.SMTP_USER

    @property
    def smtp_password(self) -> str:
        """Get SMTP password."""
        return self.SMTP_PASSWORD

    @property
    def smtp_tls(self) -> bool:
        """Get SMTP TLS setting."""
        return self.SMTP_TLS

    @property
    def smtp_from(self) -> str:
        """Get SMTP from address."""
        return self.SMTP_FROM

    def validate_jwt_secrets(self) -> None:
        """
        Validate that JWT secrets are configured properly.
        Raises SystemExit if not configured in production.
        """
        if not self.JWT_SECRET:
            if self.DEBUG:
                # Allow insecure default in DEBUG mode only
                return
            raise SystemExit("FATAL: JWT_SECRET not set. Generate with: openssl rand -hex 32")

        if not self.REFRESH_TOKEN_SECRET:
            if self.DEBUG:
                return
            raise SystemExit("FATAL: REFRESH_TOKEN_SECRET not set. Generate with: openssl rand -hex 32")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
