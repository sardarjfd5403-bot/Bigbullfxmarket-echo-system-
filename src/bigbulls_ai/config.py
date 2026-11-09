"""Safe application configuration defaults."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    trading_mode: str = os.getenv("TRADING_MODE", "paper")
    live_trading_enabled: bool = os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> None:
        if self.trading_mode not in {"paper", "live"}:
            raise ValueError("TRADING_MODE must be 'paper' or 'live'.")
        if self.trading_mode == "live" and not self.live_trading_enabled:
            raise ValueError("Live mode is disabled. Explicitly enable it only after release gates.")


def load_settings() -> Settings:
    """Load settings; live trading remains disabled by default."""
    settings = Settings()
    settings.validate()
    return settings
