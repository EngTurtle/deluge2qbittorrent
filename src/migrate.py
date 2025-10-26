import time
from typing import Any
from os.path import join as path_join
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
    state_folder = config.deluge.get('state_path', 'deluge_state_backup\\state\\')
    test_mode = config.migration.get("test_mode", False)
    test_torrent_name = config.migration.get("test_torrent_name", "")
    auto_delete = config.migration.get("auto_delete", False)
    auto_resume = config.migration.get("auto_resume", False)

    # get auth session timeout from qbittorrent
    session_qbt_timeout = qbt_client.app_preferences()['web_ui_session_timeout']
    last_qbt_login = time.time()

    # Get all torrents from Deluge with necessary fields
    logger.debug("Fetching torrents from Deluge...")
    deluge_torrents = deluge_client.call(
        'core.get_torrents_status',
        {},
        ['hash', 'name', 'state', 'label', 'paused']
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
                torrents_to_migrate.append(torrent_hash)
                logger.debug(f"Test mode: found test torrent '{test_torrent_name}'")
                break
        else:
            torrents_to_migrate.append(torrent_hash)

    if test_mode and not torrents_to_migrate:
        logger.warning(f"Test mode enabled but test torrent '{test_torrent_name}' not found in Deluge")
        return

    logger.info(f"Migrating {len(torrents_to_migrate)} torrent(s)...")

    # Migrate each torrent
    for torrent_hash in torrents_to_migrate:
        if not qbt_client.is_logged_in:
            qbt_client.auth_log_in(username=config.qbittorrent.get('username'),
                                   password=config.qbittorrent.get('password'))
            last_qbt_login = time.time()
        if (time.time() - last_qbt_login) > (0.75 * session_qbt_timeout):
            qbt_client.auth_log_in(username=config.qbittorrent.get('username'),
                                   password=config.qbittorrent.get('password'))
            last_qbt_login = time.time()

        migrate_single_torrent(
            deluge_client,
            qbt_client,
            state_folder,
            torrent_hash,
            qbt_hashes,
            auto_delete,
            auto_resume
        )


def migrate_single_torrent(
    deluge_client: DelugeRPCClient,
    qbt_client: QbittorrentClient,
    state_folder: str,
    torrent_hash: str,
    qbt_hashes: set[str],
    auto_delete: bool,
    auto_resume: bool
):
    """Migrate a single torrent from Deluge to qBittorrent.

    Args:
        deluge_client: Connected Deluge client instance.
        qbt_client: Connected qBittorrent client instance.
        torrent_hash: Hash of the torrent to migrate.
        qbt_hashes: Set of existing torrent hashes in qBittorrent.
        auto_delete: Whether to delete from Deluge after successful migration.
        auto_resume: Whether to resume in qBittorrent after migration.
    """
    torrent_info =  deluge_client.call('core.get_torrent_status', torrent_hash, [])
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
    
    save_path = torrent_info[b'save_path'].decode('utf-8')
    label = torrent_info.get(b'label', b'').decode('utf-8')

    # load torrent file from state folder

    torrent_path = path_join(state_folder, hash_str+'.torrent')
    try:
        with open(torrent_path, 'rb') as f:
            logger.debug(f"  Loading torrent from {torrent_path}")
            torrent = f.read()
    except FileNotFoundError as e:
        logger.error(f"Failed to find torrent file at: {torrent_path}")
        return

    try:
        add_params = {
            'torrent_files': torrent,
            'save_path': save_path,
            'download_path': save_path,
            'is_paused': True,
            'is_root_folder': False,
            'rename': torrent_name,
            'use_auto_torrent_management': False
        }
        # Only add category if label is not empty
        if label:
            add_params['category'] = label
        logger.debug("  Adding to qBittorrent...")
        result = qbt_client.torrents_add(**add_params)
        if result != 'Ok.':
            logger.error(f"Failed to add torrent to qBittorrent: {result}")
            return
    except Exception as e:
        logger.error(f"Failed to add torrent to qBittorrent: {e}")
        return

    time.sleep(0.2)
    qbt_torrent = qbt_client.torrents_info(torrent_hashes=hash_str)

    if not qbt_torrent:
        logger.error(f"  Failed to load torrent in qBittorrent")
        return

    qbt_torrent = qbt_torrent[0]
    logger.debug(f"  Successfully added to qBittorrent")

    # Get current file names from Deluge (after any renames)
    deluge_files = torrent_info[b'files']  # type: ignore
    deluge_files_priorities = torrent_info[b'file_priorities']
    # Get the actual current file paths from Deluge's file list
    # These are the paths AFTER any user renames
    deluge_file_paths = {}
    for file_info in deluge_files:
        file_path = file_info.get(b'path')
        file_path_str = file_path.decode('utf-8') if isinstance(file_path, bytes) else str(file_path)
        deluge_file_paths[file_info.get(b'index')] = file_path_str

    time.sleep(0.05 * len(deluge_files_priorities))
    # Get file list from qBittorrent (now populated)
    qbt_files = qbt_client.torrents_files(torrent_hash=hash_str)
    logger.debug(f"  qBittorrent has {len(qbt_files)} file(s)")

    if len(deluge_file_paths) != len(qbt_files):
        logger.error("   number of torrent files don't match, reverting")
        qbt_client.torrents_delete(delete_files=False, torrent_hashes=hash_str)
        return

    # Compare and rename files that don't match
    files_renamed = 0
    logger.info("  Renaming files to match Deluge")
    for qbt_file in qbt_files:
        qbt_name = qbt_file.name
        index = qbt_file['index']
        deluge_path = deluge_file_paths[index]
        if deluge_path != qbt_name:
            logger.debug(f"  Renaming file {index}: '{qbt_name}' -> '{deluge_path}'")
            qbt_torrent.rename_file(file_id=index, new_file_name=deluge_path)
            files_renamed += 1

    if files_renamed > 0:
        logger.debug(f"  Renamed {files_renamed} file(s) to match Deluge")

    # Recheck torrent in qBittorrent
    time.sleep(1)
    logger.debug("  Starting recheck...")
    qbt_torrent.recheck()

    # Wait for recheck to complete
    logger.debug("  Waiting for recheck to complete...")
    wait_for_recheck(qbt_client, hash_str)

    logger.debug(f"  Update file priority")
    for index, priority in enumerate(deluge_files_priorities):
        priority = 0 if priority == 0 else 1
        qbt_torrent.file_priority(file_ids=index, priority=priority)

    # Compare progress
    deluge_progress = torrent_info[b'progress']
    qbt_torrent_updated = qbt_client.torrents_info(torrent_hashes=hash_str)[0]
    qbt_progress = qbt_torrent_updated.progress * 100.0

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
        time.sleep(2)  # Check every 5 seconds
        torrent = qbt_client.torrents_info(torrent_hashes=torrent_hash)
        if not torrent:
            logger.error("  Torrent not found in qBittorrent")
            return

        torrent = torrent[0]
        # Check if torrent is still in checking state
        if torrent.state not in ['checkingUP', 'checkingDL', 'checkingResumeData']:
            logger.debug(f"  torrent state is {torrent.state}")
            logger.debug("  Recheck completed")
            time.sleep(1)
            return



    logger.warning(f"  Recheck timeout after {timeout} seconds")