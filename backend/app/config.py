from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Literal
from pydantic import Field, field_validator

# Resolve .env from project root (parent of backend/)
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # AI Configuration - Multi-provider with fallback chain
    ai_api_keys: dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "groq": None,
            "anthropic": None,
            "openai": None,
            "azure": None,
            "google": None,
            "deepseek": None,
        },
        description="API keys for each AI provider"
    )
    ai_model: str = "groq/mixtral-8x7b-32768"
    ai_provider_order: list[str] = [
        "groq", "anthropic", "openai", "azure", "google", "deepseek"
    ]
    ai_enabled: bool = False
    ai_timeout: int = 60  # seconds
    ai_max_retries: int = 3

    # Server Configuration
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    debug: bool = False
    api_key_required: bool = False
    admin_api_key: Optional[str] = None

    # Playwright Configuration
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # milliseconds
    playwright_max_pages: int = 5
    playwright_viewport_width: int = 1920
    playwright_viewport_height: int = 1080

    # Security Configuration
    request_timeout: int = 30  # seconds
    max_content_length: int = 10 * 1024 * 1024  # 10MB
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    cors_credentials: bool = True
    allow_origins_regex: Optional[str] = None

    # Phishlet Generation
    evilginx_min_ver: str = "3.2.0"
    phishlet_author: str = "@rtlphishletgen"
    generate_force_post: bool = True
    generate_js_inject: bool = True

    # Logging & Audit
    log_level: str = "INFO"
    audit_logging_enabled: bool = True
    log_sensitive_data: bool = False

    # Database/Storage
    phishlets_data_dir: str = "./backend/data/phishlets"
    max_stored_phishlets: int = 1000

    model_config = {
        "env_file": str(_env_file),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("ai_provider_order")
    @classmethod
    def validate_provider_order(cls, v):
        valid_providers = {"groq", "anthropic", "openai", "azure", "google", "deepseek"}
        for provider in v:
            if provider not in valid_providers:
                raise ValueError(f"Invalid provider: {provider}")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v):
        if not v:
            raise ValueError("CORS origins cannot be empty")
        # Always allow localhost variants
        localhost_variants = {
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        }
        return list(set(v) | localhost_variants)

    def get_enabled_ai_provider(self) -> Optional[str]:
        """Get first available AI provider from fallback chain"""
        for provider in self.ai_provider_order:
            if provider in self.ai_api_keys and self.ai_api_keys[provider]:
                return provider
        return None

    def get_ai_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key for specific provider or first available"""
        if provider:
            return self.ai_api_keys.get(provider)
        provider = self.get_enabled_ai_provider()
        return self.ai_api_keys.get(provider) if provider else None


settings = Settings()

# Auto-enable AI if any key is configured
if any(settings.ai_api_keys.values()):
    settings.ai_enabled = True
    # Ensure groq is in the list if key exists
    if settings.ai_api_keys.get("groq") and "groq" not in settings.ai_provider_order:
        settings.ai_provider_order.insert(0, "groq")

