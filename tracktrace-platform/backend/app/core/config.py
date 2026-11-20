"""Application configuration. Everything sensitive comes from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULTS = {"", "change-me", "changeme", "dev-secret-not-for-production"}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: Literal["development", "test", "production"] = "development"

    # Database (PostgreSQL only)
    DATABASE_URL: str = "postgresql+psycopg://tnt:tnt_dev_pw@localhost:5432/tnt_dev"

    # Secrets
    SECRET_KEY: str = "dev-secret-not-for-production"
    JWT_SECRET: str = "dev-secret-not-for-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 480
    PASSWORD_RESET_MINUTES: int = 30

    # URLs / CORS / cookies - PRODUCTION DEFAULTS FOR NETLIFY + RENDER
    FRONTEND_URL: str = "https://trackslogistics.netlify.app"
    API_URL: str = "https://tracktrace-platform.onrender.com"
    CORS_ORIGINS: str = "https://trackslogistics.netlify.app"
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "none"
    COOKIE_DOMAIN: str | None = None
    TRUSTED_PROXY_HEADERS: bool = True  # true only behind a proxy you control (Render/Cloudflare)

    # Business defaults (overridable in site settings by SUPER_ADMIN)
    TRACKING_PREFIX: str = "NWT"

    # Rate limits: "count/seconds"
    RATE_LIMIT_TRACKING: str = "30/60"
    RATE_LIMIT_LOGIN: str = "10/300"
    RATE_LIMIT_REGISTER: str = "10/3600"
    RATE_LIMIT_FORGOT: str = "5/3600"
    RATE_LIMIT_FORMS: str = "10/3600"  # quote + contact
    ACCOUNT_LOCK_THRESHOLD: int = 8
    ACCOUNT_LOCK_MINUTES: int = 15

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_STARTTLS: bool = True

    # SMS + WhatsApp (Twilio-compatible REST API)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_SMS_FROM: str = ""
    TWILIO_WHATSAPP_FROM: str = ""

    # Document storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    UPLOAD_DIR: str = "./uploads_dev"
    MAX_UPLOAD_MB: int = 10
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM)

    @property
    def sms_configured(self) -> bool:
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_SMS_FROM)

    @property
    def whatsapp_configured(self) -> bool:
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_WHATSAPP_FROM)

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            problems = []
            if self.SECRET_KEY in _INSECURE_DEFAULTS or len(self.SECRET_KEY) < 32:
                problems.append("SECRET_KEY must be a random value of 32+ characters")
            if self.JWT_SECRET in _INSECURE_DEFAULTS or len(self.JWT_SECRET) < 32:
                problems.append("JWT_SECRET must be a random value of 32+ characters")
            if not self.COOKIE_SECURE:
                problems.append("COOKIE_SECURE must be true in production (HTTPS)")
            if "localhost" in self.CORS_ORIGINS or "localhost" in self.FRONTEND_URL:
                problems.append("CORS_ORIGINS/FRONTEND_URL must not point to localhost in production")
            if problems:
                raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()