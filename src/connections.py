"""Connection management for Deluge and qBittorrent clients."""

import sys
from deluge_client import DelugeRPCClient
import qbittorrentapi
from loguru import logger

from .config import Config


def connect_deluge(config: Config) -> DelugeRPCClient:
    """Connect to Deluge daemon.

    Args:
        config: Configuration object

    Returns:
        Connected DelugeRPCClient instance

    Raises:
        SystemExit: If connection fails
    """
    try:
        logger.info(f"Connecting to Deluge at {config.deluge['host']}:{config.deluge['port']}")

        client = DelugeRPCClient(
            config.deluge["host"],
            config.deluge["port"],
            config.deluge["username"],
            config.deluge["password"],
        )
        client.connect()

        logger.info("Successfully connected to Deluge")
        return client

    except ConnectionRefusedError:
        logger.error(f"Connection refused by Deluge at {config.deluge['host']}:{config.deluge['port']}")
        logger.error("Ensure Deluge daemon is running and accessible")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to Deluge: {e}")
        sys.exit(1)


def connect_qbittorrent(config: Config) -> qbittorrentapi.Client:
    """Connect to qBittorrent Web UI.

    Args:
        config: Configuration object

    Returns:
        Connected qBittorrent Client instance

    Raises:
        SystemExit: If connection fails
    """
    try:
        logger.info(f"Connecting to qBittorrent at {config.qbittorrent['host']}")

        client = qbittorrentapi.Client(
            host=config.qbittorrent["host"],
            username=config.qbittorrent["username"],
            password=config.qbittorrent["password"],
        )
        client.auth_log_in()

        logger.info(f"Successfully connected to qBittorrent (version {client.app.version})")
        return client

    except qbittorrentapi.LoginFailed:
        logger.error("Failed to login to qBittorrent: Invalid username or password")
        sys.exit(1)
    except qbittorrentapi.APIConnectionError as e:
        logger.error(f"Cannot connect to qBittorrent at {config.qbittorrent['host']}: {e}")
        logger.error("Ensure qBittorrent Web UI is running and accessible")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to qBittorrent: {e}")
        sys.exit(1)
