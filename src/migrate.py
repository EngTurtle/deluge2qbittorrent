import time
from typing import Any
from src.logging import logger
from qbittorrentapi import Client as QbittorrentClient
from deluge_client import DelugeRPCClient
from src.config import Config


def deluge_migrate_qbittorrent(deluge_client: DelugeRPCClient, qbt_client: QbittorrentClient, config: Config):
    """Migrate torrents from Deluge to qBittorrent.

    Args:
        deluge_client: Connected Deluge client instance.
        qbt_client: Connected qBittorrent client instance.
        config: Configuration object with migration settings.
    """
    # Get migration settings
    test_mode = config.migration.get("test_mode", False)
    test_torrent_name = config.migration.get("test_torrent_name", "")
    auto_delete = config.migration.get("auto_delete", False)
    auto_resume = config.migration.get("auto_resume", False)

    # Get all torrents from Deluge with necessary fields
    logger.debug("Fetching torrents from Deluge...")
    deluge_torrents = deluge_client.call(
        'core.get_torrents_status',
        {},
        ['hash', 'name', 'save_path', 'state', 'label', 'mapped_files', 'files', 'file_renamed', 'progress', 'paused']
    )

    # Get existing qBittorrent torrents for comparison
    logger.debug("Fetching torrents from qBittorrent...")
    qbt_torrents = qbt_client.torrents_info()
    qbt_hashes = {t.hash.lower() for t in qbt_torrents}

    logger.info(f"Found {len(deluge_torrents)} torrents in Deluge, {len(qbt_torrents)} in qBittorrent")  # type: ignore

    # Filter torrents based on test mode
    torrents_to_migrate = []
    for torrent_hash, torrent_info in deluge_torrents.items():  # type: ignore
        if test_mode:
            # Deluge returns byte strings, need to decode
            torrent_name = torrent_info[b'name'].decode('utf-8')
            if torrent_name == test_torrent_name:
                torrents_to_migrate.append((torrent_hash, torrent_info))
                logger.debug(f"Test mode: found test torrent '{test_torrent_name}'")
                break
        else:
            torrents_to_migrate.append((torrent_hash, torrent_info))

    if test_mode and not torrents_to_migrate:
        logger.warning(f"Test mode enabled but test torrent '{test_torrent_name}' not found in Deluge")
        return

    logger.info(f"Migrating {len(torrents_to_migrate)} torrent(s)...")

    # Migrate each torrent
    for torrent_hash, torrent_info in torrents_to_migrate:
        migrate_single_torrent(
            deluge_client,
            qbt_client,
            torrent_hash,
            torrent_info,
            qbt_hashes,
            auto_delete,
            auto_resume
        )


def migrate_single_torrent(
    deluge_client: DelugeRPCClient,
    qbt_client: QbittorrentClient,
    torrent_hash: str,
    torrent_info: dict[str, Any],
    qbt_hashes: set[str],
    auto_delete: bool,
    auto_resume: bool
):
    """Migrate a single torrent from Deluge to qBittorrent.

    Args:
        deluge_client: Connected Deluge client instance.
        qbt_client: Connected qBittorrent client instance.
        torrent_hash: Hash of the torrent to migrate.
        torrent_info: Torrent information from Deluge.
        qbt_hashes: Set of existing torrent hashes in qBittorrent.
        auto_delete: Whether to delete from Deluge after successful migration.
        auto_resume: Whether to resume in qBittorrent after migration.
    """
    # Deluge returns byte strings, decode to regular strings
    torrent_name = torrent_info[b'name'].decode('utf-8')
    logger.info(f"Migrating: {torrent_name}")

    # Decode hash if it's bytes
    hash_str = torrent_hash.decode('utf-8') if isinstance(torrent_hash, bytes) else torrent_hash

    # Check if torrent already exists in qBittorrent
    if hash_str.lower() in qbt_hashes:
        logger.info(f"  Already exists in qBittorrent, skipping")
        return

    # Pause torrent in Deluge if not already paused
    if not torrent_info[b'paused']:
        logger.debug("  Pausing torrent in Deluge...")
        deluge_client.call('core.pause_torrent', [torrent_hash])

    # Get proper magnet URI from Deluge (includes trackers and complete metadata)
    logger.debug("  Getting magnet URI from Deluge...")
    magnet_uri_bytes = deluge_client.call('core.get_magnet_uri', torrent_hash)
    magnet_uri = magnet_uri_bytes.decode('utf-8') if isinstance(magnet_uri_bytes, bytes) else str(magnet_uri_bytes)

    # Log magnet URI details (show tracker count)
    tracker_count = magnet_uri.count('&tr=')
    logger.debug(f"  Magnet URI includes {tracker_count} tracker(s)")

    # Add torrent to qBittorrent using magnet URI
    
    save_path = torrent_info[b'save_path'].decode('utf-8')
    label = torrent_info.get(b'label', b'').decode('utf-8')

    try:
        add_params = {
            'urls': magnet_uri,
            'save_path': save_path,
            'is_paused': True,
            'use_auto_torrent_management': False,  # Disable auto management to use our save_path
        }

        # Only add category if label is not empty
        if label:
            add_params['category'] = label
        logger.info("  Adding to qBittorrent via magnet URI...")
        result = qbt_client.torrents_add(**add_params)
        if result != 'Ok.':
            logger.error(f"Failed to add torrent to qBittorrent: {result}")
            return
    except Exception as e:
        logger.error(f"Failed to add torrent to qBittorrent: {e}")
        return

    # Wait for qBittorrent to process the magnet and download metadata
    logger.debug("  Waiting for qBittorrent to download metadata...")
    max_wait = 60
    wait_interval = 5
    elapsed = 0

    qbt_torrent = None
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval

        qbt_torrent = qbt_client.torrents_info(torrent_hashes=hash_str)
        if qbt_torrent:
            logger.debug(f"  Metadata downloaded after {elapsed}s")
            break

        logger.debug(f"  Waiting for metadata... ({elapsed}s/{max_wait}s)")

    if not qbt_torrent:
        logger.error(f"  Failed to download metadata from magnet")
        return

    qbt_torrent = qbt_torrent[0]
    logger.debug(f"  Successfully added to qBittorrent")

    # Get current file names from Deluge (after any renames)
    deluge_files = torrent_info.get(b'files', [])  # type: ignore

    # Get the actual current file paths from Deluge's file list
    # These are the paths AFTER any user renames
    current_file_names = []
    for file_info in deluge_files:
        file_path = file_info.get(b'path', b'')
        file_path_str = file_path.decode('utf-8') if isinstance(file_path, bytes) else str(file_path)
        current_file_names.append(file_path_str)

    # Resume torrent briefly to populate file list, then pause
    logger.debug("  Resuming torrent to populate file list...")
    qbt_torrent.resume()
    time.sleep(3)  # Wait for file list to populate

    # Refresh torrent object and pause it
    qbt_torrent = qbt_client.torrents_info(torrent_hashes=hash_str)[0]
    qbt_torrent.pause()
    time.sleep(1)

    # Get file list from qBittorrent (now populated)
    qbt_files = qbt_client.torrents_files(torrent_hash=hash_str)
    logger.debug(f"  qBittorrent has {len(qbt_files)} file(s)")

    # Compare and rename files that don't match
    files_renamed = 0
    for i, (deluge_name, qbt_file) in enumerate(zip(current_file_names, qbt_files)):
        qbt_name = qbt_file.name
        if deluge_name != qbt_name:
            logger.debug(f"  Renaming file {i}: '{qbt_name}' -> '{deluge_name}'")
            try:
                qbt_torrent.rename_file(file_id=i, new_file_name=deluge_name)
                files_renamed += 1
            except Exception as e:
                logger.warning(f"  Failed to rename file {i}: {e}")

    if files_renamed > 0:
        logger.debug(f"  Renamed {files_renamed} file(s) to match Deluge")

    # For single-file torrents, also rename the torrent itself to match
    if len(deluge_files) == 1:
        deluge_torrent_name = torrent_name  # This is from Deluge
        qbt_torrent_name = qbt_torrent.name
        if deluge_torrent_name != qbt_torrent_name:
            logger.debug(f"  Renaming torrent: '{qbt_torrent_name}' -> '{deluge_torrent_name}'")
            try:
                qbt_torrent.rename(new_name=deluge_torrent_name)
            except Exception as e:
                logger.warning(f"  Failed to rename torrent: {e}")

    # Recheck torrent in qBittorrent
    logger.debug("  Starting recheck...")
    qbt_torrent.recheck()

    # Wait for recheck to complete
    logger.debug("  Waiting for recheck to complete...")
    wait_for_recheck(qbt_client, hash_str)

    # Compare progress
    deluge_progress = torrent_info[b'progress']
    qbt_torrent_updated = qbt_client.torrents_info(torrent_hashes=hash_str)[0]
    qbt_progress = qbt_torrent_updated.progress

    logger.debug(f"  Progress - Deluge: {deluge_progress:.2f}%, qBittorrent: {qbt_progress:.2f}%")

    # Check if migration was successful
    progress_diff = abs(deluge_progress - qbt_progress)
    if progress_diff < 1.0:  # Within 1% tolerance
        logger.info(f"  Successfully migrated ({qbt_progress:.1f}% complete)")

        # Delete from Deluge if auto_delete is enabled
        if auto_delete:
            logger.info("  Deleting from Deluge...")
            deluge_client.call('core.remove_torrent', torrent_hash, False)  # False = don't remove data

        # Resume in qBittorrent if auto_resume is enabled
        if auto_resume:
            logger.info("  Resuming in qBittorrent...")
            qbt_torrent.resume()
    else:
        logger.warning(f"  Progress mismatch ({progress_diff:.2f}%), manual verification recommended")


def wait_for_recheck(qbt_client: QbittorrentClient, torrent_hash: str, timeout: int = 600):
    """Wait for torrent recheck to complete in qBittorrent.

    Args:
        qbt_client: Connected qBittorrent client instance.
        torrent_hash: Hash of the torrent being rechecked.
        timeout: Maximum time to wait in seconds (default: 300).
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        torrent = qbt_client.torrents_info(torrent_hashes=torrent_hash)
        if not torrent:
            logger.error("  Torrent not found in qBittorrent")
            return

        torrent = torrent[0]
        # Check if torrent is still in checking state
        if torrent.state not in ['checkingUP', 'checkingDL', 'checkingResumeData']:
            logger.debug("  Recheck completed")
            return

        time.sleep(5)  # Check every 5 seconds

    logger.warning(f"  Recheck timeout after {timeout} seconds")