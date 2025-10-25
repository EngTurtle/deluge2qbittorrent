from src.logging import logger
from qbittorrentapi import Client as QbittorrentClient
from deluge_client import DelugeRPCClient
# primary file for migration functions

def deluge_migrate_qbittorrent(deluge_client: DelugeRPCClient, qbt_client: QbittorrentClient):
    """Migrate torrents from Deluge to qBittorrent.

    Args:
        deluge_client: Connected Deluge client instance.
        qbt_client: Connected qBittorrent client instance.
    """
    # log number of torrents in each client
    deluge_torrents = deluge_client.call('core.get_torrents_status', {}, ['name'])
    qbt_torrents = qbt_client.torrents_info()
    logger.info(f"Deluge torrents count: {len(deluge_torrents)}") # type: ignore
    logger.info(f"qBittorrent torrents count: {len(qbt_torrents)}")

    # get list of torrents from deluge
    # loop through deluge torrents
        # check if torrent exists in qBittorrent
        # check if label exists as category in qBittorrent
        # pause torrent in deluge
        # add torrent to qBittorrent
            # as paused
            # set category if applicable
            # set path, file, and folder rename
            # initiate recheck in qBittorrent
            # if progress in qBittorrent is within 1% of deluge
                # delete torrent from deluge
                # resume torrent in qBittorrent
    pass