"""Main entry point for the Deluge to qBittorrent migration tool."""

from loguru import logger

from src.logging import setup_logging
from src.config import load_config
from src.connections import connect_deluge, connect_qbittorrent


def main():
    """Main entry point for the migration tool."""
    setup_logging()

    logger.info("Deluge to qBittorrent Migration Tool")

    # Load configuration
    config = load_config()

    # Connect to both clients (will exit on failure)
    deluge_client = connect_deluge(config)
    qbt_client = connect_qbittorrent(config)

    logger.info("Ready to begin migration")

    # TODO: Implement migration logic here
    logger.info("Migration logic not yet implemented")


if __name__ == "__main__":
    main()
