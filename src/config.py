"""Configuration loading and validation."""

import sys
from pathlib import Path
from typing import Any
import tomli
from loguru import logger


class Config:
    """Configuration container for the migration tool."""

    def __init__(self, config_dict: dict[str, Any]):
        """Initialize configuration from dictionary.

        Args:
            config_dict: Raw configuration dictionary
        """
        self._config = config_dict
        self._validate()

    def _validate(self):
        """Validate required configuration sections."""
        required_sections = ["deluge", "qbittorrent", "migration"]
        for section in required_sections:
            if section not in self._config:
                logger.error(f"Missing required section '{section}' in config file")
                sys.exit(1)

    @property
    def deluge(self) -> dict[str, Any]:
        """Get Deluge configuration."""
        return self._config["deluge"]

    @property
    def qbittorrent(self) -> dict[str, Any]:
        """Get qBittorrent configuration."""
        return self._config["qbittorrent"]

    @property
    def migration(self) -> dict[str, Any]:
        """Get migration configuration."""
        return self._config["migration"]

    @property
    def logging(self) -> dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", {"log_level": "INFO"})



def load_config(config_path: Path = Path("config.toml")) -> Config:
    """Load configuration from TOML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Config object

    Raises:
        SystemExit: If config file doesn't exist or is invalid
    """
    if not config_path.exists():
        logger.error(f"Configuration file '{config_path}' not found")
        logger.info(f"Please copy 'config.example.toml' to '{config_path}' and fill in your credentials")
        sys.exit(1)

    try:
        with open(config_path, "rb") as f:
            config_dict = tomli.load(f)
        return Config(config_dict)
    except tomli.TOMLDecodeError as e:
        logger.error(f"Invalid TOML in configuration file: {e}")
        sys.exit(1)
