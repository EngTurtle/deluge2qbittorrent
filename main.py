"""Main entry point for the Deluge to qBittorrent migration tool."""

import sys
from loguru import logger
import qbittorrentapi
from deluge_client.client import RemoteException

from src.logging import setup_logging
from src.config import load_config
from src.connections import connect_deluge, connect_qbittorrent
from src.migrate import deluge_migrate_qbittorrent


def main():
    """Main entry point for the migration tool."""
    # Load configuration first (with basic logging)
    config = load_config()

    # Setup logging with configured level
    log_level = config.logging.get("log_level", "INFO")
    setup_logging(log_level)

    logger.info("Deluge to qBittorrent Migration Tool")

    # Connect to both clients
    try:
        with connect_deluge(config) as deluge_client, connect_qbittorrent(config) as qbt_client:
            deluge_migrate_qbittorrent(deluge_client, qbt_client, config)
    except (RemoteException, qbittorrentapi.LoginFailed) as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)
    except (ConnectionRefusedError, qbittorrentapi.APIConnectionError) as e:
        logger.error(f"Connection failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
