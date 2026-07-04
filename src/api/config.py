"""Application settings adapter over the unified runtime config."""

from src.runtime_config import Settings, get_settings

settings: Settings = get_settings()
