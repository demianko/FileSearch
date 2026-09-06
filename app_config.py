from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """Data model representing user-configurable application state."""

    directory: str = "D:/ABogue/Books/"
    pattern: str = "ai * pattern"
    extension: str = "pdf, epub, txt"
    sort_order: str = "published, publisher, modified"
    publisher: str = ""
    limit: int = 100
    filter_result: str = ""


class ConfigManager:
    """Responsible for loading and persisting user application configuration in ~/.filesearch/config."""

    DEFAULT_CONFIG_PATH = Path.home() / ".filesearch" / "config"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH

    def load(self) -> AppConfig:
        """Loads configuration from disk or returns default configuration if missing or corrupted."""
        if not self.config_path.exists():
            return AppConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return AppConfig()

            return AppConfig(
                directory=str(data.get("directory", AppConfig.directory)),
                pattern=str(data.get("pattern", AppConfig.pattern)),
                extension=str(data.get("extension", AppConfig.extension)),
                sort_order=str(data.get("sort_order", AppConfig.sort_order)),
                publisher=str(data.get("publisher", AppConfig.publisher)),
                limit=int(data.get("limit", AppConfig.limit)),
                filter_result=str(data.get("filter_result", AppConfig.filter_result)),
            )
        except Exception:
            return AppConfig()

    def save(self, config: AppConfig) -> bool:
        """Saves configuration to disk. Returns True on success, False on failure."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(config), f, indent=2)
            return True
        except Exception:
            return False
